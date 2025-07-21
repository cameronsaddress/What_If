"""
Core backend logic for Quantum Life Fork Simulator
Handles simulation generation, LLM integration, and data models
"""

import json
import random
import hashlib
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from pydantic import BaseModel, Field
import asyncio
from sqlalchemy import create_engine, Column, String, JSON, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import anthropic
import openai
import httpx
import os
from probabilities import get_probability, LIFE_DECISION_PROBABILITIES
from rate_limiter import rate_limiter, response_cache, api_monitor
from security import input_validator, content_filter, api_key_manager

# Database setup
Base = declarative_base()
engine = create_engine('sqlite:///quantum_life_simulations.db')
Session = sessionmaker(bind=engine)

# Data Models
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

# Database Model
class SimulationDB(Base):
    __tablename__ = 'simulations'
    
    id = Column(String, primary_key=True)
    user_decision = Column(String)
    mode = Column(String)
    branches = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    share_count = Column(Integer, default=0)

# Create tables
Base.metadata.create_all(engine)

class SimulationEngine:
    def __init__(self, api_key: Optional[str] = None, api_type: str = "anthropic", 
                 confirm_callback: Optional[Callable] = None):
        self.anthropic_client = None
        self.openai_client = None
        self.grok_client = None
        self.api_type = api_type
        self.confirm_callback = confirm_callback
        self._init_llm_clients(api_key)
    
    def _init_llm_clients(self, api_key: Optional[str] = None):
        """Initialize LLM clients with fallback"""
        try:
            if api_key and self.api_type == "grok":
                # Initialize Grok client
                self.grok_client = httpx.AsyncClient(
                    base_url="https://api.x.ai/v1",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    timeout=30.0
                )
            elif api_key and self.api_type == "anthropic":
                self.anthropic_client = anthropic.Anthropic(api_key=api_key)
            elif api_key and self.api_type == "openai":
                self.openai_client = openai.OpenAI(api_key=api_key)
            elif os.getenv("ANTHROPIC_API_KEY"):
                self.anthropic_client = anthropic.Anthropic(
                    api_key=os.getenv("ANTHROPIC_API_KEY")
                )
            elif os.getenv("OPENAI_API_KEY"):
                self.openai_client = openai.OpenAI(
                    api_key=os.getenv("OPENAI_API_KEY")
                )
        except Exception as e:
            print(f"Error initializing LLM client: {e}")
    
    def generate_simulation_id(self, decision: str, mode: str) -> str:
        """Generate unique simulation ID"""
        hash_input = f"{decision}{mode}{datetime.utcnow().isoformat()}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:12]
    
    def calculate_fate_score(self, events: List[str], mode: str) -> int:
        """Calculate a 'fate score' based on positive outcomes"""
        positive_keywords = ['success', 'happy', 'achieve', 'win', 'love', 'prosper', 'fulfill']
        negative_keywords = ['fail', 'regret', 'lose', 'struggle', 'miss', 'difficult']
        
        score = 50  # Base score
        for event in events:
            event_lower = event.lower()
            for pos in positive_keywords:
                if pos in event_lower:
                    score += 5
            for neg in negative_keywords:
                if neg in event_lower:
                    score -= 5
        
        # Mode adjustments
        if mode == "random":
            score += random.randint(-20, 20)
        
        return max(0, min(100, score))
    
    async def generate_branches(self, decision: str, mode: str, num_branches: int = 4) -> List[LifeBranch]:
        """Generate life branches using LLM"""
        # Validate and sanitize inputs
        decision = input_validator.sanitize_decision(decision)
        mode = input_validator.validate_mode(mode)
        
        # Check content safety
        is_safe, reason = content_filter.check_content_safety(decision)
        if not is_safe:
            # Return safe fallback for inappropriate content
            return self._generate_safe_fallback_branches(num_branches)
        
        branches = []
        
        # Determine relevant probability category
        decision_lower = decision.lower()
        prob_category = "career_relocation"  # default
        
        if any(word in decision_lower for word in ['move', 'relocate', 'city', 'country']):
            prob_category = "career_relocation"
        elif any(word in decision_lower for word in ['study', 'degree', 'university', 'college']):
            prob_category = "education_choices"
        elif any(word in decision_lower for word in ['start', 'business', 'company', 'startup']):
            prob_category = "entrepreneurship"
        elif any(word in decision_lower for word in ['marry', 'relationship', 'divorce', 'date']):
            prob_category = "relationship_decisions"
        
        for i in range(num_branches):
            branch = await self._generate_single_branch(
                decision, mode, i, prob_category, num_branches
            )
            branches.append(branch)
        
        return branches
    
    async def _generate_single_branch(self, decision: str, mode: str, 
                                     branch_index: int, prob_category: str,
                                     total_branches: int) -> LifeBranch:
        """Generate a single life branch"""
        
        # Create prompt based on mode
        prompt = self._create_branch_prompt(decision, mode, branch_index, prob_category, total_branches)
        
        # Try to get LLM response with caching
        cache_suffix = f"{decision[:20]}_{mode}_{branch_index}"
        branch_data = await self._call_llm(prompt, cache_suffix)
        
        if not branch_data:
            # Fallback to procedural generation
            branch_data = self._generate_fallback_branch(decision, mode, branch_index, prob_category)
        
        # Calculate fate score
        fate_score = self.calculate_fate_score(branch_data['key_events'], mode)
        
        return LifeBranch(
            branch_id=branch_index,
            title=branch_data['title'],
            story=branch_data['story'],
            timeline=branch_data['timeline'],
            key_events=branch_data['key_events'],
            probability_score=branch_data.get('probability_score', 0.5),
            fate_score=fate_score
        )
    
    def _create_branch_prompt(self, decision: str, mode: str, branch_index: int,
                             prob_category: str, total_branches: int) -> str:
        """Create LLM prompt for branch generation"""
        
        mode_instructions = {
            "realistic": "Use realistic probabilities and likely outcomes based on real-world data.",
            "50/50": "Give equal weight to positive and negative outcomes.",
            "random": "Include surprising, unlikely, or wildly improbable events."
        }
        
        # Get relevant probabilities for context
        probs = LIFE_DECISION_PROBABILITIES.get(prob_category, {})
        
        prompt = f"""
        Generate alternative life path #{branch_index + 1} of {total_branches} for this decision:
        "{decision}"
        
        Mode: {mode} - {mode_instructions[mode]}
        
        Consider these real-world probabilities for context:
        {json.dumps(probs, indent=2)}
        
        Create a unique branch that differs significantly from other branches.
        Branch theme suggestions:
        - Branch 1: The expected path
        - Branch 2: The challenging but rewarding path  
        - Branch 3: The unexpected twist path
        - Branch 4: The wildcard path
        
        Return JSON with this structure:
        {{
            "title": "Brief branch title (5-7 words)",
            "story": "Narrative description of this life path (150-200 words)",
            "timeline": [
                {{"year": "Year 1", "event": "What happens"}},
                {{"year": "Year 3", "event": "Major milestone"}},
                {{"year": "Year 5", "event": "Outcome"}}
            ],
            "key_events": ["Event 1", "Event 2", "Event 3"],
            "probability_score": 0.0-1.0 based on likelihood
        }}
        """
        
        return prompt
    
    async def _call_llm(self, prompt: str, cache_key_suffix: str = "") -> Optional[Dict]:
        """Call LLM with rate limiting, caching, and confirmation"""
        # Check cache first
        cache_key = f"{self.api_type}_{cache_key_suffix}"
        cached_response = response_cache.get(prompt, cache_key)
        if cached_response:
            api_monitor.record_call(f"{self.api_type}_cache", tokens=0, cost=0)
            return cached_response
        
        # Check rate limit
        can_proceed, wait_time = rate_limiter.can_make_request()
        if not can_proceed:
            raise Exception(f"Rate limit exceeded. Please wait {wait_time:.1f} seconds.")
        
        # Manual confirmation if callback provided
        if self.confirm_callback:
            confirmed = await self.confirm_callback(
                f"Make {self.api_type.upper()} API call?",
                f"This will send a request to {self.api_type} API.\nTokens available: {rate_limiter.get_status()['available_tokens']}"
            )
            if not confirmed:
                return None
        
        try:
            response_data = None
            tokens_used = 0
            
            if self.grok_client:
                # Call Grok API
                response = await self.grok_client.post(
                    "/chat/completions",
                    json={
                        "model": "grok-beta",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7,
                        "max_tokens": 1000
                    }
                )
                response.raise_for_status()
                result = response.json()
                response_data = json.loads(result["choices"][0]["message"]["content"])
                tokens_used = result.get("usage", {}).get("total_tokens", 0)
                
            elif self.anthropic_client:
                response = self.anthropic_client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=1000,
                    messages=[{"role": "user", "content": prompt}]
                )
                response_data = json.loads(response.content[0].text)
                tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else 0
                
            elif self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                response_data = json.loads(response.choices[0].message.content)
                tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else 0
            
            # Cache successful response
            if response_data:
                response_cache.set(prompt, cache_key, response_data)
                api_monitor.record_call(self.api_type, tokens=tokens_used, cost=tokens_used * 0.00001)
                
            return response_data
            
        except Exception as e:
            api_monitor.record_call(self.api_type, error=True)
            print(f"LLM call failed: {e}")
            return None
    
    def _generate_safe_fallback_branches(self, num_branches: int) -> List[LifeBranch]:
        """Generate safe fallback branches for inappropriate content"""
        safe_branches = []
        for i in range(num_branches):
            branch = LifeBranch(
                branch_id=i,
                title=f"Path {i+1}: A New Beginning",
                story="Every decision opens new doors. This path leads to personal growth and positive outcomes through dedication and perseverance.",
                timeline=[
                    {"year": "Year 1", "event": "Started fresh with new perspective"},
                    {"year": "Year 3", "event": "Built meaningful connections"},
                    {"year": "Year 5", "event": "Achieved personal milestone"}
                ],
                key_events=["Fresh start", "Personal growth", "Positive outcome"],
                probability_score=0.5,
                fate_score=70
            )
            safe_branches.append(branch)
        return safe_branches
    
    def _generate_fallback_branch(self, decision: str, mode: str, 
                                 branch_index: int, prob_category: str) -> Dict:
        """Generate branch without LLM"""
        templates = [
            {
                "title": "The Conventional Path",
                "story": f"You decided to {decision}. Things progressed as most would expect - some challenges, some victories, but overall a steady journey. Life unfolds with familiar rhythms, bringing both comfort and occasional wonder about the roads not taken.",
                "timeline": [
                    {"year": "Year 1", "event": "Initial adjustment period with mixed results"},
                    {"year": "Year 3", "event": "Established new routines and relationships"},
                    {"year": "Year 5", "event": "Achieved moderate success and stability"}
                ],
                "key_events": ["Found your footing", "Built new connections", "Reached equilibrium"],
                "probability_score": 0.7
            },
            {
                "title": "The Transformative Journey",
                "story": f"Your choice to {decision} catalyzed unexpected personal growth. Initial struggles gave way to profound discoveries about yourself. What seemed like a simple decision became a complete life transformation.",
                "timeline": [
                    {"year": "Year 1", "event": "Difficult start but important lessons learned"},
                    {"year": "Year 3", "event": "Breakthrough moment changes everything"},
                    {"year": "Year 5", "event": "Living a completely different life than imagined"}
                ],
                "key_events": ["Overcame major obstacle", "Discovered hidden talent", "Found true calling"],
                "probability_score": 0.4
            },
            {
                "title": "The Serendipitous Adventure",
                "story": f"After deciding to {decision}, life took surprising turns. A chance encounter led to unexpected opportunities. Sometimes the best outcomes come from the most unlikely circumstances.",
                "timeline": [
                    {"year": "Year 1", "event": "Random encounter changes trajectory"},
                    {"year": "Year 3", "event": "Pursuing opportunity you never expected"},
                    {"year": "Year 5", "event": "Success in an entirely different field"}
                ],
                "key_events": ["Met future mentor", "Pivoted to new path", "Achieved unexpected success"],
                "probability_score": 0.3
            },
            {
                "title": "The Wild Card Timeline",
                "story": f"Your decision to {decision} triggered a cascade of improbable events. Against all odds, you found yourself in situations that defy conventional wisdom. Life became stranger than fiction.",
                "timeline": [
                    {"year": "Year 1", "event": "Bizarre coincidence alters course"},
                    {"year": "Year 3", "event": "Became involved in something extraordinary"},
                    {"year": "Year 5", "event": "Living a life no one could have predicted"}
                ],
                "key_events": ["Won unlikely lottery", "Became accidental celebrity", "Changed the world"],
                "probability_score": 0.1
            }
        ]
        
        template = templates[branch_index % len(templates)]
        
        # Adjust based on mode
        if mode == "random":
            template["probability_score"] = random.random()
        elif mode == "50/50":
            template["probability_score"] = 0.5
            
        # Sanitize output
        template["story"] = content_filter.sanitize_output(template["story"])
        for event in template["timeline"]:
            event["event"] = content_filter.sanitize_output(event["event"])
        template["key_events"] = [content_filter.sanitize_output(e) for e in template["key_events"]]
        
        return template
    
    async def save_simulation(self, result: SimulationResult) -> str:
        """Save simulation to database"""
        session = Session()
        try:
            sim_db = SimulationDB(
                id=result.simulation_id,
                user_decision=result.user_decision,
                mode=result.mode,
                branches=[branch.dict() for branch in result.branches],
                created_at=result.created_at
            )
            session.add(sim_db)
            session.commit()
            return result.simulation_id
        finally:
            session.close()
    
    async def load_simulation(self, simulation_id: str) -> Optional[SimulationResult]:
        """Load simulation from database"""
        session = Session()
        try:
            sim_db = session.query(SimulationDB).filter_by(id=simulation_id).first()
            if sim_db:
                branches = [LifeBranch(**branch) for branch in sim_db.branches]
                return SimulationResult(
                    simulation_id=sim_db.id,
                    user_decision=sim_db.user_decision,
                    mode=sim_db.mode,
                    branches=branches,
                    created_at=sim_db.created_at
                )
            return None
        finally:
            session.close()

# LLM Integration Agent contributions
class LLMPromptOptimizer:
    """Specialized class for optimizing LLM prompts"""
    
    @staticmethod
    def enhance_narrative_prompt(base_prompt: str, user_context: Dict) -> str:
        """Enhance prompts with user context for better narratives"""
        enhancements = []
        
        # Add temporal context
        current_age = user_context.get('age', 30)
        enhancements.append(f"Assume the person is currently {current_age} years old.")
        
        # Add personality traits if provided
        if 'traits' in user_context:
            enhancements.append(f"Consider these personality traits: {', '.join(user_context['traits'])}")
        
        # Add location context
        if 'location' in user_context:
            enhancements.append(f"Current location: {user_context['location']}")
        
        enhanced = base_prompt + "\n\nAdditional context:\n" + "\n".join(enhancements)
        return enhanced