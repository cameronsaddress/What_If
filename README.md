# What If

AI-powered life-path simulator that explores alternate outcomes of major decisions. Users describe a life choice, and the system generates branching narrative timelines using multi-provider LLM reasoning, real-world probability data, and an interactive "River of Destiny" visualization.

## Architecture

```
                    Streamlit UI (app.py)
              Decision Input | Mode Selection
              Visualization  | API Monitoring
                         |
                    SimulationEngine (backend.py)
                         |
          +--------------+--------------+
          |              |              |
       Grok (xAI)    Claude       GPT-4
       (primary)    (fallback)   (fallback)
          |              |              |
          +--------------+--------------+
                         |
          +--------------+--------------+
          |              |              |
    Rate Limiter    Response Cache   Security
    (token bucket)  (LRU, 15m TTL)  (validation,
     10 req/bucket)  (100 items)     filtering)
          |
     SQLAlchemy ORM
          |
      SQLite DB
   (simulation history)
```

## Tech Stack

| Layer | Technologies |
|---|---|
| **UI Framework** | Streamlit with custom CSS (glassmorphism, gradient animations) |
| **LLM Providers** | Grok (xAI), Anthropic Claude, OpenAI GPT-4 — automatic fallback chain |
| **Data Models** | Pydantic (type-safe request/response validation) |
| **Database** | SQLite via SQLAlchemy ORM |
| **Visualization** | svgwrite — procedural SVG "River of Destiny" with Bezier curves |
| **Security** | Input sanitization, content filtering, API key masking, XSS prevention |
| **Performance** | Token bucket rate limiting, LRU response caching (15-min TTL) |
| **Payments** | Stripe integration (premium tier) |

## Key Features

### Multi-Provider LLM Integration
- Three-provider fallback chain: Grok -> Claude -> GPT-4
- Procedural generation fallback when all APIs are unavailable
- Response caching reduces API costs by avoiding duplicate calls
- Manual confirmation mode for cost-controlled testing

### Simulation Engine
- **Three modes:** Realistic (research-backed probabilities), 50/50 (balanced), Random (improbable)
- Six decision categories with real-world probability data: career relocation, education, entrepreneurship, relationships, lifestyle, financial
- Fate scoring algorithm (0-100) based on sentiment analysis of generated events
- Shareable simulation results via database-backed URLs

### Interactive Visualization
- SVG "River of Destiny" with branching Bezier curve paths
- Hover effects, gradient animations, mobile-responsive viewBox scaling
- Color-coded branches based on fate scores

### Production-Grade Infrastructure
- Token bucket rate limiter (10 requests, 0.5/sec refill, burst limit 5)
- LRU cache with TTL (100 items, 15-minute expiration)
- Input validation and sanitization (length limits, HTML escaping)
- Content filtering for inappropriate requests
- API usage monitoring with cost tracking
- Thread-safe operations with locks

## Project Structure

```
app.py                 Streamlit UI (custom CSS, session state, layout)
backend.py             SimulationEngine, LLM clients, Pydantic models, DB ops
visualization.py       River of Destiny SVG generator with mobile adapter
rate_limiter.py        Token bucket rate limiter + LRU cache + API monitor
security.py            Input validation, content filtering, API key management
config.py              Centralized configuration (rate limits, cache, costs)
probabilities.py       Real-world probability data for 6 decision categories
test_app.py            Unit and integration tests
test_improvements.py   Security and performance test suite
quickstart.sh          Automated setup script
```

## Getting Started

### Prerequisites
- Python 3.12+
- API key for at least one provider: Grok (xAI), Anthropic, or OpenAI

### Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run the application
streamlit run app.py
# Available at http://localhost:8501
```

API keys can also be entered directly in the UI without environment variables.

## Testing

```bash
# Run full test suite
pytest test_app.py test_improvements.py -v

# Run with coverage
pytest --cov=. --cov-report=term-missing
```

## Deployment

### Docker

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["streamlit", "run", "app.py", "--server.port", "8501"]
```

### Streamlit Cloud
1. Connect GitHub repo to [Streamlit Cloud](https://streamlit.io/cloud)
2. Add API keys in the Streamlit secrets dashboard
3. Deploy
