"""
Test suite for the What If life-path simulator.
Covers core engine, visualization, probabilities, and integration flows.
"""

import pytest
import asyncio
from datetime import datetime, timezone

from backend import SimulationEngine, LifeBranch, SimulationResult
from visualization import RiverOfDestiny, MobileRiverAdapter
from probabilities import get_probability, LIFE_DECISION_PROBABILITIES


class TestSimulationEngine:

    @pytest.fixture
    def engine(self):
        return SimulationEngine()

    def test_simulation_id_uniqueness(self, engine):
        id1 = engine.generate_simulation_id("test", "realistic")
        id2 = engine.generate_simulation_id("test", "realistic")
        assert id1 != id2
        assert len(id1) == 12

    def test_fate_score_positive(self, engine):
        events = ["achieve success", "find love", "win award"]
        score = engine.calculate_fate_score(events, "realistic")
        assert score > 50
        assert 0 <= score <= 100

    def test_fate_score_negative(self, engine):
        events = ["face failure", "lose job", "struggle financially"]
        score = engine.calculate_fate_score(events, "realistic")
        assert score < 50
        assert 0 <= score <= 100

    @pytest.mark.asyncio
    async def test_fallback_branch_generation(self, engine):
        """Without an API key, the engine falls back to procedural generation."""
        branches = await engine.generate_branches("move to Paris", "realistic", 4)
        assert len(branches) == 4
        assert all(isinstance(b, LifeBranch) for b in branches)
        assert all(b.story and b.timeline and b.key_events for b in branches)
        assert all(0 <= b.fate_score <= 100 for b in branches)

    @pytest.mark.asyncio
    async def test_mode_variations(self, engine):
        realistic = await engine.generate_branches("start a business", "realistic", 2)
        balanced = await engine.generate_branches("start a business", "50/50", 2)
        wild = await engine.generate_branches("start a business", "random", 2)

        assert realistic[0].probability_score != realistic[1].probability_score
        assert all(b.probability_score == 0.5 for b in balanced)
        assert len(wild) == 2

    def test_classify_decision(self, engine):
        assert engine._classify_decision("move to Tokyo") == "career_relocation"
        assert engine._classify_decision("start a business") == "entrepreneurship"
        assert engine._classify_decision("get a degree") == "education_choices"
        assert engine._classify_decision("invest in crypto") == "financial_decisions"


class TestProbabilities:

    def test_data_structure(self):
        for category, outcomes in LIFE_DECISION_PROBABILITIES.items():
            assert isinstance(outcomes, dict)
            for outcome, prob in outcomes.items():
                assert isinstance(prob, float)
                assert 0 <= prob <= 1

    def test_get_probability_realistic(self):
        p = get_probability("career_relocation", "job_satisfaction_increase", "realistic")
        assert p == 0.67

    def test_get_probability_balanced(self):
        p = get_probability("any", "any", "50/50")
        assert p == 0.5

    def test_get_probability_random(self):
        probs = [get_probability("any", "any", "random") for _ in range(10)]
        assert all(0.1 <= p <= 0.9 for p in probs)
        assert len(set(probs)) > 1


class TestVisualization:

    def test_svg_generation(self):
        river = RiverOfDestiny(800, 600)
        branches = [
            {"branch_id": 0, "title": "Test Path 1", "fate_score": 75, "key_events": ["A", "B"]},
            {"branch_id": 1, "title": "Test Path 2", "fate_score": 50, "key_events": ["C", "D"]},
        ]
        svg = river.generate_river_svg(branches, "Test Decision")

        assert "<svg" in svg
        assert "Test Decision" in svg
        assert "Test Path 1" in svg
        assert "branch-path" in svg
        assert "event-node" in svg

    def test_mobile_adaptation(self):
        original = '<svg width="800" height="600">Content</svg>'
        adapted = MobileRiverAdapter.adapt_for_mobile(original, 400)
        assert "viewBox" in adapted
        assert "preserveAspectRatio" in adapted


class TestIntegration:

    @pytest.mark.asyncio
    async def test_full_simulation_flow(self):
        engine = SimulationEngine()

        decision = "move to Japan"
        branches = await engine.generate_branches(decision, "realistic", 3)

        sim_id = engine.generate_simulation_id(decision, "realistic")
        result = SimulationResult(
            simulation_id=sim_id,
            user_decision=decision,
            mode="realistic",
            branches=branches,
            created_at=datetime.now(timezone.utc),
        )

        await engine.save_simulation(result)
        loaded = await engine.load_simulation(sim_id)

        assert loaded is not None
        assert loaded.user_decision == decision
        assert len(loaded.branches) == 3


class TestEdgeCases:

    @pytest.mark.asyncio
    async def test_empty_decision(self):
        engine = SimulationEngine()
        branches = await engine.generate_branches("", "realistic", 2)
        assert len(branches) == 2
        assert all(b.story for b in branches)

    def test_invalid_mode_defaults(self):
        prob = get_probability("test", "test", "invalid_mode")
        assert isinstance(prob, float)
        assert 0.1 <= prob <= 0.9

    @pytest.mark.asyncio
    async def test_missing_simulation(self):
        engine = SimulationEngine()
        result = await engine.load_simulation("nonexistent")
        assert result is None


class TestPerformance:

    @pytest.mark.asyncio
    async def test_concurrent_simulations(self):
        engine = SimulationEngine()
        tasks = [engine.generate_branches(f"decision {i}", "realistic", 2) for i in range(5)]
        results = await asyncio.gather(*tasks)
        assert len(results) == 5
        assert all(len(r) == 2 for r in results)

    def test_large_visualization(self):
        river = RiverOfDestiny(800, 600)
        branches = [
            {"branch_id": i, "title": f"Path {i}", "fate_score": 50 + i * 10, "key_events": [f"E{j}" for j in range(3)]}
            for i in range(4)
        ]
        svg = river.generate_river_svg(branches, "Complex Decision")
        assert len(svg) > 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
