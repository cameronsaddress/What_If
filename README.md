# 🌊 Quantum Life Fork Simulator

An innovative web application that simulates alternate life paths based on key decisions, featuring an interactive "River of Destiny" visualization.

## 🚀 Features

- **Multi-Path Simulation**: Explore 3-4 alternate life timelines based on your decisions
- **Three Simulation Modes**:
  - 🎯 Realistic: Based on real-world probability data
  - ⚖️ 50/50: Balanced outcomes
  - 🎲 Random: Wild and unexpected possibilities
- **Interactive Visualization**: Beautiful SVG "River of Destiny" showing branching life paths
- **Mobile Responsive**: Works seamlessly on all devices
- **Social Sharing**: Share your quantum journeys on social media
- **Premium Features**: Detailed reports, 4 branches, and ad-free experience

## 🛠️ Tech Stack

- **Framework**: Streamlit (Python 3.12+)
- **Backend**: FastAPI (for async operations)
- **LLM Integration**: Grok (xAI) / Anthropic Claude / OpenAI GPT-4
- **Database**: SQLite with SQLAlchemy
- **Visualization**: SVGWrite for dynamic graphics
- **Payments**: Stripe integration
- **Security**: Input validation, content filtering, rate limiting
- **Performance**: Response caching, API monitoring

## 📋 Prerequisites

- Python 3.12 or higher
- API key for Grok (xAI), Anthropic Claude, or OpenAI
- Stripe account (for premium features - optional)

## 🔧 Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/quantum-life-simulator.git
cd quantum-life-simulator
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

## 🚀 Running the Application

### Development Mode
```bash
streamlit run app.py
```

The app will be available at `http://localhost:8501`

### Testing Mode (with Manual API Confirmation)
1. Run the app normally
2. Enter your API key in the UI (not in .env)
3. Each API call will show a confirmation popup
4. Monitor rate limits and cache hits in the UI

### Production Mode
```bash
streamlit run app.py --server.port 80 --server.address 0.0.0.0
```

## 🧪 Testing

Run the test suite:
```bash
pytest test_app.py -v
```

## 📱 Deployment Options

### Streamlit Cloud (Recommended)
1. Push to GitHub
2. Connect to [Streamlit Cloud](https://streamlit.io/cloud)
3. Add secrets in dashboard
4. Deploy!

### Heroku
```bash
# Create Procfile
echo "web: streamlit run app.py --server.port $PORT" > Procfile

# Deploy
heroku create quantum-life-app
heroku config:set ANTHROPIC_API_KEY=your_key
git push heroku main
```

### Docker
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["streamlit", "run", "app.py"]
```

## 🔐 Security Considerations

- API keys can be entered via UI (masked display)
- Input validation and sanitization
- Content filtering for inappropriate requests
- Rate limiting (10 requests, 0.5/sec refill)
- API key format validation
- User data encrypted in database
- HTTPS enforced in production

## 📊 Performance Optimization

- LLM responses cached for 15 minutes (LRU, 100 items)
- Token bucket rate limiting prevents API abuse
- Manual confirmation for testing reduces accidental calls
- API usage monitoring and cost tracking
- Database queries optimized with indexes
- SVG generation optimized for mobile
- Async operations for better concurrency
- Fallback to procedural generation on failures

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📄 License

MIT License - see LICENSE file

## 🆘 Support

- Documentation: docs.quantumlife.app
- Issues: [GitHub Issues](https://github.com/yourusername/quantum-life-simulator/issues)
- Email: support@quantumlife.app

## 🎮 Usage Tips

1. **Best Decisions to Simulate**:
   - Career moves
   - Educational choices
   - Relationship decisions
   - Life-changing adventures

2. **Understanding Fate Scores**:
   - 0-40: Challenging path
   - 41-70: Balanced outcomes
   - 71-100: Favorable timeline

3. **Sharing Your Journey**:
   - Click share buttons for social media
   - Use #QuantumLifeChallenge for TikTok
   - Screenshot the River visualization

## 🚧 Roadmap

- [ ] PDF export functionality
- [ ] Multi-language support
- [ ] Real-time collaborative simulations
- [ ] AI-generated branch images
- [ ] Mobile app versions

---

## 🆕 Recent Improvements

1. **Grok API Integration**: Full support for xAI's Grok model
2. **Frontend API Key Input**: No need for environment variables during testing
3. **Manual Confirmation**: Yes/No popup before each API call
4. **Enhanced Security**: Input validation, content filtering, key masking
5. **Advanced Rate Limiting**: Token bucket algorithm with visual status
6. **Smart Caching**: Reduce costs with intelligent response caching
7. **API Monitoring**: Track usage, costs, and performance metrics

Built with ❤️ by the Quantum Life Team