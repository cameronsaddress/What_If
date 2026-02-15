"""
Core simulation engine for the What If life-path simulator.
Handles LLM-powered branch generation, fallback logic, and persistence.
"""

import json
import random
import hashlib
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from openai import OpenAI
from sqlalchemy import create_engine, Column, String, JSON, DateTime, Integer
from sqlalchemy.orm import DeclarativeBase, sessionmaker
import os

from probabilities import get_probability, LIFE_DECISION_PROBABILITIES
from rate_limiter import rate_limiter, response_cache, api_monitor
from security import input_validator, content_filter
from config import LLM_CONFIG, COST_ESTIMATES

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    pass

engine = create_engine("sqlite:///whatif_simulations.db")
Session = sessionmaker(bind=engine)


class SimulationDB(Base):
    __tablename__ = "simulations"

    id = Column(String, primary_key=True)
    user_decision = Column(String)
    mode = Column(String)
    branches = Column(JSON)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    share_count = Column(Integer, default=0)


Base.metadata.create_all(engine)

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

class LifeBranch(BaseModel):
    branch_id: int
    title: str
    story: str
    timeline: List[Dict[str, str]]
    key_events: List[str]
    probability_score: float
    fate_score: int = Field(ge=0, le=100)


class SimulationResult(BaseModel):
    simulation_id: str
    user_decision: str
    mode: str
    branches: List[LifeBranch]
    created_at: datetime
    share_url: Optional[str] = None

# ---------------------------------------------------------------------------
# Simulation engine
# ---------------------------------------------------------------------------

CATEGORY_KEYWORDS = {
    "career_relocation": ["move", "relocate", "city", "country", "abroad"],
    "education_choices": ["study", "degree", "university", "college", "school"],
    "entrepreneurship": ["start", "business", "company", "startup", "founder"],
    "relationship_decisions": ["marry", "relationship", "divorce", "date", "partner"],
    "lifestyle_changes": ["diet", "exercise", "habit", "fitness", "health"],
    "financial_decisions": ["invest", "save", "buy", "mortgage", "retire"],
}


class SimulationEngine:
    """Generates alternate life-path branches using LLM reasoning with
    automatic model fallback through OpenRouter."""

    def __init__(self, api_key: Optional[str] = None):
        self.client: Optional[OpenAI] = None
        self._init_client(api_key)

    def _init_client(self, api_key: Optional[str] = None):
        key = api_key or os.getenv("OPENROUTER_API_KEY")
        if key:
            self.client = OpenAI(
                base_url=LLM_CONFIG["base_url"],
                api_key=key,
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate_branches(
        self, decision: str, mode: str, num_branches: int = 4
    ) -> List[LifeBranch]:
        decision = input_validator.sanitize_decision(decision)
        mode = input_validator.validate_mode(mode)

        is_safe, reason = content_filter.check_content_safety(decision)
        if not is_safe:
            return self._generate_safe_fallback(num_branches)

        prob_category = self._classify_decision(decision)

        branches: List[LifeBranch] = []
        for i in range(num_branches):
            branch = await self._generate_single_branch(
                decision, mode, i, prob_category, num_branches
            )
            branches.append(branch)
        return branches

    async def save_simulation(self, result: SimulationResult) -> str:
        session = Session()
        try:
            row = SimulationDB(
                id=result.simulation_id,
                user_decision=result.user_decision,
                mode=result.mode,
                branches=[b.model_dump() for b in result.branches],
                created_at=result.created_at,
            )
            session.add(row)
            session.commit()
            return result.simulation_id
        finally:
            session.close()

    async def load_simulation(self, simulation_id: str) -> Optional[SimulationResult]:
        session = Session()
        try:
            row = session.query(SimulationDB).filter_by(id=simulation_id).first()
            if not row:
                return None
            return SimulationResult(
                simulation_id=row.id,
                user_decision=row.user_decision,
                mode=row.mode,
                branches=[LifeBranch(**b) for b in row.branches],
                created_at=row.created_at,
            )
        finally:
            session.close()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def generate_simulation_id(decision: str, mode: str) -> str:
        raw = f"{decision}{mode}{datetime.now(timezone.utc).isoformat()}"
        return hashlib.md5(raw.encode()).hexdigest()[:12]

    @staticmethod
    def calculate_fate_score(events: List[str], mode: str) -> int:
        positive = ["success", "happy", "achieve", "win", "love", "prosper", "fulfill", "thrive"]
        negative = ["fail", "regret", "lose", "struggle", "miss", "difficult", "decline"]

        score = 50
        for event in events:
            lower = event.lower()
            score += 5 * sum(1 for w in positive if w in lower)
            score -= 5 * sum(1 for w in negative if w in lower)

        if mode == "random":
            score += random.randint(-20, 20)

        return max(0, min(100, score))

    @staticmethod
    def _classify_decision(decision: str) -> str:
        lower = decision.lower()
        for category, keywords in CATEGORY_KEYWORDS.items():
            if any(kw in lower for kw in keywords):
                return category
        return "career_relocation"

    # ------------------------------------------------------------------
    # Branch generation
    # ------------------------------------------------------------------

    async def _generate_single_branch(
        self, decision: str, mode: str, index: int,
        prob_category: str, total: int
    ) -> LifeBranch:
        prompt = self._build_prompt(decision, mode, index, prob_category, total)

        cache_suffix = f"{decision[:20]}_{mode}_{index}"
        data = await self._call_llm(prompt, cache_suffix)

        if not data:
            data = self._fallback_branch(decision, mode, index, prob_category)

        fate = self.calculate_fate_score(data["key_events"], mode)

        return LifeBranch(
            branch_id=index,
            title=data["title"],
            story=data["story"],
            timeline=data["timeline"],
            key_events=data["key_events"],
            probability_score=data.get("probability_score", 0.5),
            fate_score=fate,
        )

    def _build_prompt(
        self, decision: str, mode: str, index: int,
        prob_category: str, total: int
    ) -> str:
        mode_desc = {
            "realistic": "Use realistic probabilities and likely outcomes based on real-world data.",
            "50/50": "Give equal weight to positive and negative outcomes.",
            "random": "Include surprising, unlikely, or wildly improbable events.",
        }
        probs = LIFE_DECISION_PROBABILITIES.get(prob_category, {})

        return f"""Generate alternate life path #{index + 1} of {total} for this decision:
"{decision}"

Mode: {mode} — {mode_desc[mode]}

Real-world probability context:
{json.dumps(probs, indent=2)}

Create a unique branch that differs significantly from others.
Suggested themes: 1) expected path, 2) challenging but rewarding, 3) unexpected twist, 4) wildcard.

Return ONLY valid JSON (no markdown, no code fences):
{{
    "title": "Brief title (5-7 words)",
    "story": "Narrative of this life path (150-200 words)",
    "timeline": [
        {{"year": "Year 1", "event": "What happens"}},
        {{"year": "Year 3", "event": "Major milestone"}},
        {{"year": "Year 5", "event": "Outcome"}}
    ],
    "key_events": ["Event 1", "Event 2", "Event 3"],
    "probability_score": 0.0
}}"""

    # ------------------------------------------------------------------
    # LLM call with caching, rate limiting, and model fallback
    # ------------------------------------------------------------------

    async def _call_llm(self, prompt: str, cache_suffix: str = "") -> Optional[Dict]:
        cache_key = f"openrouter_{cache_suffix}"
        cached = response_cache.get(prompt, cache_key)
        if cached:
            api_monitor.record_call("cache", tokens=0, cost=0)
            return cached

        can_proceed, wait_time = rate_limiter.can_make_request()
        if not can_proceed:
            logger.warning("Rate limit hit — wait %.1fs", wait_time)
            return None

        if not self.client:
            return None

        models = [
            LLM_CONFIG["models"]["primary"],
            LLM_CONFIG["models"]["fallback_1"],
            LLM_CONFIG["models"]["fallback_2"],
        ]

        for model in models:
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=LLM_CONFIG["max_tokens"],
                    temperature=LLM_CONFIG["temperature"],
                )
                raw = response.choices[0].message.content.strip()

                # Strip markdown code fences if present
                if raw.startswith("```"):
                    raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
                    if raw.endswith("```"):
                        raw = raw[:-3]
                    raw = raw.strip()

                data = json.loads(raw)
                tokens = getattr(response.usage, "total_tokens", 0) if response.usage else 0
                cost = tokens * COST_ESTIMATES.get(model, 0.00002) / 1000

                response_cache.set(prompt, cache_key, data)
                api_monitor.record_call(model, tokens=tokens, cost=cost)
                return data

            except Exception as e:
                logger.warning("Model %s failed: %s — trying next", model, e)
                api_monitor.record_call(model, error=True)
                continue

        return None

    # ------------------------------------------------------------------
    # Procedural fallback (no LLM required)
    # ------------------------------------------------------------------

    def _generate_safe_fallback(self, count: int) -> List[LifeBranch]:
        return [
            LifeBranch(
                branch_id=i,
                title=f"Path {i + 1}: A New Beginning",
                story="Every decision opens new doors. This path leads to personal growth and positive outcomes through dedication and perseverance.",
                timeline=[
                    {"year": "Year 1", "event": "Started fresh with new perspective"},
                    {"year": "Year 3", "event": "Built meaningful connections"},
                    {"year": "Year 5", "event": "Achieved personal milestone"},
                ],
                key_events=["Fresh start", "Personal growth", "Positive outcome"],
                probability_score=0.5,
                fate_score=70,
            )
            for i in range(count)
        ]

    @staticmethod
    def _fallback_branch(
        decision: str, mode: str, index: int, prob_category: str
    ) -> Dict[str, Any]:
        templates = [
            {
                "title": "The Conventional Path",
                "story": f"You decided to {decision}. Things progressed as most would expect — some challenges, some victories, but overall a steady journey. Life unfolds with familiar rhythms, bringing both comfort and occasional wonder about the roads not taken.",
                "timeline": [
                    {"year": "Year 1", "event": "Initial adjustment period with mixed results"},
                    {"year": "Year 3", "event": "Established new routines and relationships"},
                    {"year": "Year 5", "event": "Achieved moderate success and stability"},
                ],
                "key_events": ["Found your footing", "Built new connections", "Reached equilibrium"],
                "probability_score": 0.7,
            },
            {
                "title": "The Transformative Journey",
                "story": f"Your choice to {decision} catalyzed unexpected personal growth. Initial struggles gave way to profound discoveries about yourself. What seemed like a simple decision became a complete life transformation.",
                "timeline": [
                    {"year": "Year 1", "event": "Difficult start but important lessons learned"},
                    {"year": "Year 3", "event": "Breakthrough moment changes everything"},
                    {"year": "Year 5", "event": "Living a completely different life than imagined"},
                ],
                "key_events": ["Overcame major obstacle", "Discovered hidden talent", "Found true calling"],
                "probability_score": 0.4,
            },
            {
                "title": "The Serendipitous Adventure",
                "story": f"After deciding to {decision}, life took surprising turns. A chance encounter led to unexpected opportunities. Sometimes the best outcomes come from the most unlikely circumstances.",
                "timeline": [
                    {"year": "Year 1", "event": "Random encounter changes trajectory"},
                    {"year": "Year 3", "event": "Pursuing opportunity you never expected"},
                    {"year": "Year 5", "event": "Success in an entirely different field"},
                ],
                "key_events": ["Met future mentor", "Pivoted to new path", "Achieved unexpected success"],
                "probability_score": 0.3,
            },
            {
                "title": "The Wildcard Timeline",
                "story": f"Your decision to {decision} triggered a cascade of improbable events. Against all odds, you found yourself in situations that defy conventional wisdom. Life became stranger than fiction.",
                "timeline": [
                    {"year": "Year 1", "event": "Bizarre coincidence alters course"},
                    {"year": "Year 3", "event": "Became involved in something extraordinary"},
                    {"year": "Year 5", "event": "Living a life no one could have predicted"},
                ],
                "key_events": ["Unexpected windfall", "Unlikely connection", "Rewrote the script"],
                "probability_score": 0.1,
            },
        ]

        template = templates[index % len(templates)]

        if mode == "random":
            template["probability_score"] = random.random()
        elif mode == "50/50":
            template["probability_score"] = 0.5

        template["story"] = content_filter.sanitize_output(template["story"])
        for ev in template["timeline"]:
            ev["event"] = content_filter.sanitize_output(ev["event"])
        template["key_events"] = [content_filter.sanitize_output(e) for e in template["key_events"]]

        return template
