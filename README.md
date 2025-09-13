# Local Chat Companion

A privacy-focused local chat assistant with adaptive memory and learni8. **Run the Application**
   ```bash
   python main.py
   ```

### Quick Start (Minimal Setup)

For a quick test with minimal dependencies:

```bash
# Create Python 3.12 virtual environment
py -3.12 -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install only core dependencies
pip install python-dotenv pydantic pydantic-settings httpx rich

# Test the application
python main.py --version
python main.py --help
```

This minimal setup provides the core chat functionality. Install additional dependencies as needed for advanced features.apabilities, designed to work with LM Studio and local language models.

## 🎯 Vision

Create an intelligent, privacy-focused chat companion that learns and adapts to user preferences while maintaining complete data sovereignty. The system provides personalized interactions through sophisticated memory management and behavior shaping capabilities.

## ✨ Features

### 🔐 Privacy First
- **100% Local Processing**: All data stays on your machine
- **No Cloud Dependencies**: Works completely offline
- **Encrypted Storage**: Optional encryption for sensitive data
- **Data Control**: Full control over what is remembered and learned

### 🧠 Adaptive Memory System
- **Session Memory**: Tracks current conversation context
- **Long-term Memory**: Stores important facts and preferences
- **Smart Retrieval**: Context-aware memory recall
- **Memory Management**: Review, edit, and control stored memories

### 🎭 Personality & Behavior
- **Style Presets**: Friend, Coach, Assistant, or Custom personalities
- **Behavior Shaping**: Teach desired responses through examples
- **Feedback Learning**: Thumbs up/down with contextual tags
- **Tone Adaptation**: Adjusts communication style over time

### 🛠 Technical Capabilities
- **LM Studio Integration**: Seamless local LLM connection
- **Vector Search**: Efficient semantic memory retrieval
- **Multiple UIs**: CLI, Web, and Desktop interfaces
- **Extensible Architecture**: Plugin-ready design

## 🚀 Quick Start

### Prerequisites

- Python 3.12 or higher (recommended: Python 3.12)
- [LM Studio](https://lmstudio.ai/) installed and running
- A local language model loaded in LM Studio

### Installation

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd local-chat-companion
   ```

2. **Create Virtual Environment with Python 3.12**
   ```bash
   # Windows (using py launcher)
   py -3.12 -m venv venv
   venv\Scripts\activate
   
   # Linux/Mac
   python3.12 -m venv venv
   source venv/bin/activate
   ```

3. **Install Core Dependencies**
   ```bash
   pip install --upgrade pip
   pip install python-dotenv pydantic pydantic-settings httpx rich
   ```

4. **Install Optional Dependencies (as needed)**
   ```bash
   # For full functionality (recommended)
   pip install -r requirements.txt
   
   # Or install specific feature sets:
   pip install structlog loguru  # Enhanced logging
   pip install typer click       # Advanced CLI features
   pip install fastapi uvicorn   # Web interface
   pip install pytest pytest-cov # Testing
   ```

5. **Configure Environment**
   ```bash
   # Copy the template and edit with your settings
   copy .env.template .env
   # Edit .env with your preferred settings
   ```

5. **Initialize Database**
   ```bash
   python -c "from src.core.config import load_config; load_config().ensure_directories()"
   ```

6. **Start LM Studio**
   - Launch LM Studio
   - Load your preferred local model
   - Start the local server (default: http://localhost:1234)

7. **Run the Application**
   ```bash
   python main.py
   ```

## 📖 Development Phases

The project follows a structured 10-phase development plan:

### Phase 0: Setup & Vision ✅
- [x] Project structure
- [x] Environment configuration
- [x] Basic documentation

### Phase 1: Core Chat ✅
- [x] LM Studio integration
- [x] Basic chat loop
- [x] Message handling
- [x] Configuration system

### Phase 2: Profile & Session Memory
- [ ] User profile management
- [ ] Session memory tracking
- [ ] Memory inspector
- [ ] Learning controls

### Phase 3: Long-Term Memory
- [ ] Vector database integration
- [ ] Importance scoring
- [ ] Memory retrieval
- [ ] Review queue

### Phase 4: Behavior & Teaching
- [ ] Style card system
- [ ] Teaching library
- [ ] Role switching
- [ ] Behavior presets

### Phase 5: Feedback & Adaptation
- [ ] Feedback collection
- [ ] Session digests
- [ ] Self-evaluation
- [ ] Adaptive learning

### Phase 6: Projects & Topics
- [ ] Project boards
- [ ] Document integration
- [ ] Context switching
- [ ] Goal tracking

### Phase 7: Routines & Tools
- [ ] Daily check-ins
- [ ] Weekly reviews
- [ ] Local tools integration
- [ ] TTS/ASR support

### Phase 8: Transparency & Safety
- [ ] Usage transparency
- [ ] Privacy controls
- [ ] Data purging
- [ ] Safety features

### Phase 9: Performance & Testing
- [ ] Performance optimization
- [ ] Automated testing
- [ ] Metrics dashboard
- [ ] Regression testing

### Phase 10: Onboarding & Polish
- [ ] Setup wizard
- [ ] User documentation
- [ ] Export/import
- [ ] Backup system

## 🗂 Project Structure

```
local-chat-companion/
├── src/
│   ├── core/                 # Core system components
│   │   ├── config.py         # Configuration management
│   │   └── logging_config.py # Logging setup
│   ├── chat/                 # Chat interface and handling
│   ├── memory/               # Memory management system
│   └── ui/                   # User interface components
├── config/                   # Configuration files
├── data/                     # Data storage
│   ├── memory/              # Long-term memory storage
│   └── sessions/            # Session data
├── docs/                     # Documentation
├── tests/                    # Test files
├── logs/                     # Application logs
├── .env                      # Environment configuration
├── .env.template            # Environment template
├── requirements.txt         # Python dependencies
├── setup.py                 # Package setup
└── main.py                  # Application entry point
```

## 🔧 Configuration

The application uses environment variables for configuration. Key settings include:

- **LM Studio Connection**: API endpoint and model selection
- **Memory Settings**: Retention limits and importance thresholds
- **UI Preferences**: Interface type and theming
- **Security Options**: Encryption and privacy controls
- **Behavior Settings**: Default personality and learning preferences

See `.env.template` for all available options.

## 🎮 Usage Examples

### Basic Chat
```bash
python main.py
> Hello! How can I help you today?
```

### Memory Management
```bash
# View stored memories
python main.py --show-memories

# Clear session memory
python main.py --clear-session

# Export conversation history
python main.py --export conversations.json
```

### Personality Switching
```bash
# Switch to coach mode
python main.py --style coach

# Use custom personality
python main.py --style-file my_custom_style.yaml
```

## 🧪 Testing

Run the test suite:
```bash
# Install development dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test category
pytest tests/unit/
pytest tests/integration/
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: Report bugs and request features on GitHub Issues
- **Documentation**: Check the `docs/` directory for detailed guides
- **Community**: Join discussions in GitHub Discussions

## 🔮 Roadmap

- [ ] Multi-language support
- [ ] Plugin system for extensions
- [ ] Mobile companion app
- [ ] Advanced analytics dashboard
- [ ] Integration with productivity tools
- [ ] Voice interaction capabilities
- [ ] Collaborative features for teams

## 🙏 Acknowledgments

- [LM Studio](https://lmstudio.ai/) for excellent local LLM hosting
- [Chroma](https://www.trychroma.com/) and [Qdrant](https://qdrant.tech/) for vector database solutions
- [Sentence Transformers](https://www.sbert.net/) for embedding models
- The open-source AI community for inspiration and tools

---

**Built with ❤️ for privacy-conscious AI enthusiasts**