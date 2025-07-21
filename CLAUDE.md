# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

"Quantum Life Fork Simulator" - A web application that simulates alternate life paths based on user decisions, featuring an interactive "River of Destiny" visualization. Built with Streamlit and Python, it uses LLMs to generate branching narratives.

## Key Commands

### Development
```bash
# Quick setup
./quickstart.sh

# Run the app
streamlit run app.py

# Run tests
pytest test_app.py test_improvements.py -v

# Lint code
trunk check

# Clear cache
python -c "from rate_limiter import response_cache; response_cache.clear()"
```

## Architecture

### Core Modules
- **app.py**: Main Streamlit interface, handles UI/UX and user interactions
- **backend.py**: SimulationEngine class manages branch generation, LLM integration, and database operations
- **visualization.py**: RiverOfDestiny class creates interactive SVG visualizations
- **probabilities.py**: Real-world probability data for realistic simulations
- **rate_limiter.py**: Token bucket rate limiting, LRU cache, and API monitoring
- **security.py**: Input validation, content filtering, and API key management
- **config.py**: Central configuration for optimization and performance settings

### Key Design Patterns
1. **Async Operations**: Backend uses asyncio for concurrent branch generation
2. **Fallback System**: Procedural generation when LLM APIs unavailable
3. **Mode-Based Logic**: Three simulation modes (realistic/50-50/random) affect probability calculations
4. **Caching Strategy**: Use `@st.cache_data` for expensive operations

### Database Schema
- SQLite with SQLAlchemy
- Main table: `simulations` (stores JSON branches, enables sharing via IDs)

## Important Considerations

### LLM Integration
- Supports Grok (xAI), Anthropic Claude, and OpenAI APIs
- Frontend API key input for testing (no env vars required)
- Manual confirmation popup before each API call
- Fallback to procedural generation if APIs fail
- Prompts engineered for JSON output with specific structure

### New Features (Recent Improvements)
1. **Rate Limiting**: Token bucket algorithm (10 requests, 0.5/sec refill)
2. **Response Caching**: 15-minute TTL, 100 response LRU cache
3. **Security**: Input sanitization, API key validation, content filtering
4. **Grok API Support**: Full integration with xAI's Grok model
5. **Manual Confirmation**: Yes/No popup before API calls for testing

### Visualization
- SVG-based "River of Destiny" with CSS hover effects
- Mobile-responsive through viewBox scaling
- Branch paths use bezier curves for organic appearance

### Premium Features
- Free: 3 branches, text ads
- Premium ($2.99): 4 branches, no ads, PDF export (planned)
- Stripe integration ready but requires configuration

## Testing Approach
- Unit tests for core logic (simulation engine, probability calculations)
- Integration tests for full simulation flow
- Edge case handling (empty decisions, API failures)
- Performance tests for concurrent operations
- Security tests (input validation, content filtering)
- Rate limiting and caching tests

## Performance & Cost Optimization
- API calls cached for 15 minutes to reduce costs
- Rate limiting prevents API abuse (configurable in config.py)
- Batch processing for similar requests
- Fallback to procedural generation on rate limit
- API usage monitoring and cost tracking