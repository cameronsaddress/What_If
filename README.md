# What If

AI-powered life-path simulator that explores alternate outcomes of major decisions. Users describe a life choice, and the system generates branching narrative timelines using multi-model LLM reasoning through OpenRouter, real-world probability data, and an interactive "River of Destiny" SVG visualization.

## Architecture

```
                  Streamlit UI (app.py)
            Decision Input | Mode Selection
            Visualization  | API Monitoring
                       |
                  SimulationEngine (backend.py)
                       |
            +----------+----------+
            |          |          |
         Claude     GPT-4o     Gemini
        Sonnet 4.5  (fallback)  Flash 2.0
        (primary)              (fallback)
            |          |          |
            +----------+----------+
                       |               All models accessed through
                   OpenRouter          a single OpenAI-compatible
                   (unified API)       client with automatic
                       |               failover
            +----------+----------+
            |          |          |
      Rate Limiter  Response    Security
      (token bucket) Cache      (validation,
       10 req/bucket) (LRU,      sanitization)
                     15m TTL)
            |
       SQLAlchemy ORM
            |
        SQLite DB
     (simulation history)
```

## Tech Stack

| Layer | Technologies |
|---|---|
| **UI** | Streamlit with custom CSS (dark glassmorphism, Inter font, responsive) |
| **LLM** | OpenRouter gateway — Claude Sonnet 4.5, GPT-4o, Gemini 2.0 Flash (automatic fallback chain) |
| **Data Models** | Pydantic v2 (type-safe validation) |
| **Database** | SQLite via SQLAlchemy ORM (modern `DeclarativeBase`) |
| **Visualization** | svgwrite — procedural SVG with Bezier curves, hover effects, dark theme |
| **Security** | Input sanitization, content filtering, HTML escaping, XSS prevention |
| **Performance** | Token bucket rate limiting, LRU response caching (15-min TTL), API cost tracking |

## Key Features

### Unified Multi-Model LLM Integration
- Single OpenRouter client replaces three separate API integrations
- Three-model fallback chain: Claude Sonnet 4.5 -> GPT-4o -> Gemini 2.0 Flash
- Procedural generation fallback when all APIs are unavailable
- Response caching eliminates duplicate API calls
- Automatic JSON extraction with markdown fence stripping

### Simulation Engine
- **Three modes:** Realistic (research-backed probabilities), Balanced (50/50), Wildcard (improbable events)
- Six decision categories with real-world probability data: career, education, entrepreneurship, relationships, lifestyle, financial
- Fate scoring algorithm (0-100) based on sentiment analysis of generated events
- Shareable simulation results via database-backed URLs

### Interactive Visualization
- SVG "River of Destiny" with branching Bezier curve paths
- Dark-themed design with glow effects and hover interactions
- Event nodes with tooltips placed along cubic Bezier curves
- Mobile-responsive viewBox scaling

### Production Infrastructure
- Token bucket rate limiter (10 requests, 0.5/sec refill)
- LRU cache with TTL (100 items, 15-minute expiration)
- Input validation and HTML sanitization
- Content safety filtering
- API usage monitoring with cost tracking per model
- Thread-safe operations

## Project Structure

```
app.py                 Streamlit UI (dark glassmorphism, session state, responsive)
backend.py             SimulationEngine, OpenRouter client, Pydantic models, DB ops
visualization.py       River of Destiny SVG generator with mobile adapter
rate_limiter.py        Token bucket rate limiter + LRU cache + API monitor
security.py            Input validation, content filtering, output sanitization
config.py              Centralized configuration (models, rate limits, cache, costs)
probabilities.py       Real-world probability data for 6 decision categories
test_app.py            Unit and integration tests
test_improvements.py   Security and performance test suite
quickstart.sh          Automated setup script
```

## Getting Started

### Prerequisites
- Python 3.12+
- OpenRouter API key (free tier available at [openrouter.ai](https://openrouter.ai))

### Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your OpenRouter API key

# Run the application
streamlit run app.py
# Available at http://localhost:8501
```

The app also accepts the API key directly in the UI settings panel.

## Testing

```bash
# Run full test suite
pytest test_app.py test_improvements.py -v

# Run with coverage
pytest --cov=. --cov-report=term-missing
```
