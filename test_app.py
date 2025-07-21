"""
Test suite for Quantum Life Fork Simulator
Tests core functionality, integration, and edge cases
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import modules to test
from backend import SimulationEngine, LifeBranch, SimulationResult, LLMPromptOptimizer
from visualization import RiverOfDestiny, MobileRiverAdapter
from probabilities import get_probability, LIFE_DECISION_PROBABILITIES

class TestSimulationEngine:
    """Test the core simulation engine"""
    
    @pytest.fixture
    def engine(self):
        return SimulationEngine()
    
    def test_simulation_id_generation(self, engine):
        """Test unique ID generation"""
        id1 = engine.generate_simulation_id("test decision", "realistic")
        id2 = engine.generate_simulation_id("test decision", "realistic")
        assert id1 != id2
        assert len(id1) == 12
    
    def test_fate_score_calculation(self, engine):
        """Test fate score calculation"""
        positive_events = ["achieve success", "find love", "win award"]
        negative_events = ["face failure", "lose job", "struggle financially"]
        
        positive_score = engine.calculate_fate_score(positive_events, "realistic")
        negative_score = engine.calculate_fate_score(negative_events, "realistic")
        
        assert positive_score > 50
        assert negative_score < 50
        assert 0 <= positive_score <= 100
        assert 0 <= negative_score <= 100
    
    @pytest.mark.asyncio
    async def test_fallback_branch_generation(self, engine):
        """Test branch generation without LLM"""
        # Mock LLM to force fallback
        engine.anthropic_client = None
        engine.openai_client = None
        
        branches = await engine.generate_branches("move to Paris", "realistic", 4)
        
        assert len(branches) == 4
        assert all(isinstance(b, LifeBranch) for b in branches)
        assert all(b.story and b.timeline and b.key_events for b in branches)
        assert all(0 <= b.fate_score <= 100 for b in branches)
    
    @pytest.mark.asyncio
    async def test_mode_variations(self, engine):
        """Test different simulation modes"""
        engine.anthropic_client = None  # Use fallback
        
        realistic = await engine.generate_branches("start a business", "realistic", 2)
        balanced = await engine.generate_branches("start a business", "50/50", 2)
        random = await engine.generate_branches("start a business", "random", 2)
        
        # Realistic should have varied probabilities
        assert realistic[0].probability_score != realistic[1].probability_score
        
        # 50/50 should have equal probabilities (in fallback)
        assert all(b.probability_score == 0.5 for b in balanced)
        
        # Random should have... random probabilities
        assert len(random) == 2

class TestProbabilities:
    """Test probability data and functions"""
    
    def test_probability_data_structure(self):
        """Ensure probability data is properly structured"""
        for category, outcomes in LIFE_DECISION_PROBABILITIES.items():
            assert isinstance(outcomes, dict)
            for outcome, prob in outcomes.items():
                assert isinstance(prob, float)
                assert 0 <= prob <= 1
    
    def test_get_probability_modes(self):
        """Test probability retrieval for different modes"""
        # Realistic mode
        realistic_prob = get_probability("career_relocation", "job_satisfaction_increase", "realistic")
        assert realistic_prob == 0.67
        
        # 50/50 mode
        balanced_prob = get_probability("any_category", "any_outcome", "50/50")
        assert balanced_prob == 0.5
        
        # Random mode
        random_probs = [get_probability("any", "any", "random") for _ in range(10)]
        assert all(0.1 <= p <= 0.9 for p in random_probs)
        assert len(set(random_probs)) > 1  # Should have variation

class TestVisualization:
    """Test River of Destiny visualization"""
    
    def test_river_generation(self):
        """Test SVG generation"""
        river = RiverOfDestiny(800, 600)
        
        branches = [
            {
                'branch_id': 0,
                'title': 'Test Path 1',
                'fate_score': 75,
                'key_events': ['Event 1', 'Event 2']
            },
            {
                'branch_id': 1,
                'title': 'Test Path 2',
                'fate_score': 50,
                'key_events': ['Event A', 'Event B']
            }
        ]
        
        svg = river.generate_river_svg(branches, "Test Decision")
        
        assert '<svg' in svg
        assert 'Test Decision' in svg
        assert 'Test Path 1' in svg
        assert 'Test Path 2' in svg
        assert 'branch-path' in svg  # CSS class
        assert 'event-node' in svg   # CSS class
    
    def test_mobile_adaptation(self):
        """Test mobile responsiveness"""
        original_svg = '<svg width="800" height="600">Content</svg>'
        mobile_svg = MobileRiverAdapter.adapt_for_mobile(original_svg, 400)
        
        assert 'viewBox' in mobile_svg
        assert 'preserveAspectRatio' in mobile_svg
        assert 'font-size: 16px' in mobile_svg  # Enlarged text

class TestIntegration:
    """Integration tests for the full app flow"""
    
    @pytest.mark.asyncio
    async def test_full_simulation_flow(self):
        """Test complete simulation generation and storage"""
        engine = SimulationEngine()
        engine.anthropic_client = None  # Use fallback
        
        # Generate simulation
        decision = "move to Japan"
        mode = "realistic"
        branches = await engine.generate_branches(decision, mode, 3)
        
        # Create result
        sim_id = engine.generate_simulation_id(decision, mode)
        result = SimulationResult(
            simulation_id=sim_id,
            user_decision=decision,
            mode=mode,
            branches=branches,
            created_at=datetime.utcnow()
        )
        
        # Save and load
        await engine.save_simulation(result)
        loaded = await engine.load_simulation(sim_id)
        
        assert loaded is not None
        assert loaded.user_decision == decision
        assert loaded.mode == mode
        assert len(loaded.branches) == 3
    
    def test_llm_prompt_optimizer(self):
        """Test LLM prompt enhancement"""
        base_prompt = "Generate a life path"
        context = {
            'age': 25,
            'traits': ['adventurous', 'creative'],
            'location': 'New York'
        }
        
        enhanced = LLMPromptOptimizer.enhance_narrative_prompt(base_prompt, context)
        
        assert 'age' in enhanced
        assert '25' in enhanced
        assert 'adventurous' in enhanced
        assert 'New York' in enhanced

class TestEdgeCases:
    """Test edge cases and error handling"""
    
    @pytest.mark.asyncio
    async def test_empty_decision(self):
        """Test handling of empty decision input"""
        engine = SimulationEngine()
        engine.anthropic_client = None
        
        branches = await engine.generate_branches("", "realistic", 2)
        assert len(branches) == 2
        assert all(b.story for b in branches)
    
    def test_invalid_mode(self):
        """Test handling of invalid mode"""
        prob = get_probability("test", "test", "invalid_mode")
        assert isinstance(prob, float)
        assert 0.1 <= prob <= 0.9  # Should default to random
    
    @pytest.mark.asyncio
    async def test_database_error_handling(self):
        """Test database error resilience"""
        engine = SimulationEngine()
        
        # Try to load non-existent simulation
        result = await engine.load_simulation("nonexistent123")
        assert result is None

# Performance tests
class TestPerformance:
    """Performance and scalability tests"""
    
    @pytest.mark.asyncio
    async def test_concurrent_simulations(self):
        """Test handling multiple concurrent simulations"""
        engine = SimulationEngine()
        engine.anthropic_client = None
        
        # Generate 5 simulations concurrently
        tasks = [
            engine.generate_branches(f"decision {i}", "realistic", 2)
            for i in range(5)
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        assert all(len(r) == 2 for r in results)
    
    def test_large_visualization(self):
        """Test visualization with maximum branches"""
        river = RiverOfDestiny(800, 600)
        
        branches = [
            {
                'branch_id': i,
                'title': f'Path {i}',
                'fate_score': 50 + i * 10,
                'key_events': [f'Event {j}' for j in range(3)]
            }
            for i in range(4)
        ]
        
        svg = river.generate_river_svg(branches, "Complex Decision")
        assert svg
        assert len(svg) > 1000  # Should be substantial

if __name__ == "__main__":
    pytest.main([__file__, "-v"])