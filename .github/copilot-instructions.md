# GitHub Copilot Instructions for Local Chat Companion

## 🎯 Project Overview

This is a **privacy-focused local chat assistant** with adaptive memory and learning capabilities, designed to work with LM Studio and local language models. The project follows a **10-phase development roadmap** currently in Phase 1 (Core Chat).

## 🏗️ Architecture Patterns

### Configuration-Driven Design
- **Central config system**: `src/core/config.py` using Pydantic with enum-based validation
- **Environment-first**: All settings via `.env` with comprehensive `.env.template`
- **Auto-validation**: Temperature (0-2), top_p (0-1), memory thresholds (0-1) enforced in Config class
- **Directory management**: `config.ensure_directories()` creates required folders on startup

### Modular Component Architecture
```
src/
├── core/         # Foundation: config, logging, utilities
├── chat/         # LLM integration and conversation handling  
├── memory/       # Vector DB, SQLite, session management
└── ui/           # CLI, web, desktop interfaces
```

### Logging Strategy
- **Structured logging**: Uses `structlog` with Rich console output
- **Dual output**: Console (Rich formatting) + file (JSON/plain text)
- **Graceful fallbacks**: ImportError handling for optional dependencies
- **Logger mixing**: `LoggerMixin` class for easy logging integration

## 🔧 Development Workflows

### Environment Setup
```bash
# Essential setup sequence
cp .env.template .env
python -c "from src.core.config import load_config; load_config().ensure_directories()"
pip install -r requirements.txt
python main.py
```

### Configuration Access Pattern
```python
from src.core.config import load_config
config = load_config()
llm_config = config.get_llm_config()  # Returns dict for LM Studio
vector_config = config.get_vector_db_config()  # Returns dict for Chroma/Qdrant
```

### Module Import Convention
- **Relative imports** within `src/` modules: `from ..core.config import Config`
- **Fallback pattern** for development: Path manipulation + absolute imports in except blocks
- **Entry point**: `main.py` adds `src/` to sys.path before imports

## 🗃️ Data Flow & Storage

### Multi-Layer Memory System (Planned)
- **Session memory**: Recent conversation context (max 50 items)
- **Long-term memory**: Vector embeddings in Chroma/Qdrant
- **Structured data**: SQLite for user profiles, preferences, metadata
- **Importance scoring**: Only memories above threshold (0.6) get stored long-term

### LM Studio Integration Pattern
- **API compatibility**: OpenAI-style API at `http://localhost:1234/v1`
- **Local-first**: No cloud dependencies, offline-capable
- **Model agnostic**: Configurable model selection via `DEFAULT_MODEL`

## 🎛️ Configuration Conventions

### Personality & Behavior Config
- **Style presets**: `PersonalityStyle` enum (friend, coach, assistant, custom)
- **Learning controls**: `enable_learning`, `auto_save_sessions` toggles
- **Safety features**: `enable_content_filtering`, `enable_pii_detection`

### Vector Database Flexibility
- **Multi-backend**: `VectorDBType` enum supports Chroma and Qdrant
- **Unified config**: Single interface via `get_vector_db_config()`
- **Collection naming**: Configurable via `VECTOR_DB_COLLECTION`

### Extensibility Points
- **UI types**: Enum supports CLI, web, desktop expansion
- **Embedding models**: Supports sentence-transformers, OpenAI, local models
- **Export formats**: Comma-separated list: "json,txt,markdown"

## 🚀 Phase-Based Development

### Current State (Phase 1)
- **Status**: Basic chat app placeholder in `src/chat/app.py`
- **Next**: LM Studio HTTP client, message handling, conversation loop
- **Testing**: Run `python main.py` to see Phase 0 completion status

### Key Integration Points
- **Chat app entry**: `ChatApp(config)` class in `src/chat/app.py`
- **Async architecture**: All main functions use `asyncio`
- **Graceful shutdown**: Handles KeyboardInterrupt, proper cleanup

## 🧪 Testing & Development

### Development Mode Features
- **Debug flags**: `DEV_MODE`, `API_DEBUG` for enhanced logging
- **Test data**: `USE_TEST_DATA` with configurable `TEST_DATA_PATH`
- **Rich console**: Pretty formatting with syntax highlighting

### Dependency Management
- **Core vs Optional**: Base functionality works with minimal deps
- **Extra groups**: `[dev]`, `[web]`, `[speech]`, `[gui]` in setup.py
- **Graceful degradation**: Try/except imports for enhanced features

## 📝 Code Style Patterns

### Enum-Based Configuration
Use enums for all configuration choices to ensure type safety:
```python
class VectorDBType(str, Enum):
    CHROMA = "chroma"
    QDRANT = "qdrant"
```

### Pydantic Validation
Add custom validators for business logic:
```python
@validator("temperature")
def validate_temperature(cls, v):
    if not 0 <= v <= 2:
        raise ValueError("Temperature must be between 0 and 2")
    return v
```

### Error Handling Philosophy
- **Privacy-first**: Never log sensitive data
- **User-friendly**: Rich console formatting for errors
- **Fallback ready**: ImportError handling for optional dependencies

When contributing, focus on **local-first architecture**, **configuration validation**, and **phase-appropriate development** following the established patterns.