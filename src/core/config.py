"""
Configuration management for Local Chat Companion.

Handles loading and validation of environment variables and application settings.
"""

import os
from pathlib import Path
from typing import Optional, List, Any, Dict
from dataclasses import dataclass, field
from enum import Enum

try:
    # Try Pydantic v2 first
    from pydantic_settings import BaseSettings
    from pydantic import Field, field_validator
    PYDANTIC_V2 = True
except ImportError:
    try:
        # Fallback to Pydantic v1
        from pydantic import BaseSettings, validator, Field
        field_validator = validator
        PYDANTIC_V2 = False
    except ImportError:
        raise ImportError("Neither pydantic v2 with pydantic-settings nor pydantic v1 is available")


class AppMode(str, Enum):
    """Application modes."""
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"


class VectorDBType(str, Enum):
    """Supported vector database types."""
    CHROMA = "chroma"
    QDRANT = "qdrant"


class EmbeddingModelType(str, Enum):
    """Supported embedding model types."""
    SENTENCE_TRANSFORMERS = "sentence-transformers"
    OPENAI = "openai"
    LOCAL = "local"


class UIType(str, Enum):
    """Supported UI types."""
    CLI = "cli"
    WEB = "web"
    DESKTOP = "desktop"


class PersonalityStyle(str, Enum):
    """Available personality styles."""
    FRIEND = "friend"
    COACH = "coach"
    ASSISTANT = "assistant"
    CUSTOM = "custom"


class Config(BaseSettings):
    """Main configuration class for the Local Chat Companion."""
    
    # Application settings
    app_mode: AppMode = Field(default=AppMode.DEVELOPMENT, env="APP_MODE")
    app_name: str = Field(default="Local Chat Companion", env="APP_NAME")
    app_version: str = Field(default="0.1.0", env="APP_VERSION")
    debug: bool = Field(default=True, env="DEBUG")
    
    # LM Studio / Local LLM settings
    lm_studio_api_base: str = Field(default="http://localhost:1234/v1", env="LM_STUDIO_API_BASE")
    lm_studio_api_key: Optional[str] = Field(default=None, env="LM_STUDIO_API_KEY")
    default_model: str = Field(default="local-model", env="DEFAULT_MODEL")
    
    # Model parameters
    max_tokens: int = Field(default=2048, env="MAX_TOKENS")
    temperature: float = Field(default=0.7, env="TEMPERATURE")
    top_p: float = Field(default=0.9, env="TOP_P")
    frequency_penalty: float = Field(default=0.0, env="FREQUENCY_PENALTY")
    presence_penalty: float = Field(default=0.0, env="PRESENCE_PENALTY")
    
    # Memory and storage settings
    vector_db_type: VectorDBType = Field(default=VectorDBType.CHROMA, env="VECTOR_DB_TYPE")
    vector_db_host: str = Field(default="localhost", env="VECTOR_DB_HOST")
    vector_db_port: int = Field(default=6333, env="VECTOR_DB_PORT")
    vector_db_collection: str = Field(default="chat_memories", env="VECTOR_DB_COLLECTION")
    
    sqlite_db_path: str = Field(default="data/companion.db", env="SQLITE_DB_PATH")
    
    # Memory settings
    max_session_memory: int = Field(default=50, env="MAX_SESSION_MEMORY")
    max_long_term_memories: int = Field(default=1000, env="MAX_LONG_TERM_MEMORIES")
    memory_importance_threshold: float = Field(default=0.6, env="MEMORY_IMPORTANCE_THRESHOLD")
    
    # Embedding settings
    embedding_model_type: EmbeddingModelType = Field(default=EmbeddingModelType.SENTENCE_TRANSFORMERS, env="EMBEDDING_MODEL_TYPE")
    sentence_transformer_model: str = Field(default="all-MiniLM-L6-v2", env="SENTENCE_TRANSFORMER_MODEL")
    
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_embedding_model: str = Field(default="text-embedding-ada-002", env="OPENAI_EMBEDDING_MODEL")
    
    # UI settings
    ui_type: UIType = Field(default=UIType.CLI, env="UI_TYPE")
    web_host: str = Field(default="localhost", env="WEB_HOST")
    web_port: int = Field(default=8080, env="WEB_PORT")
    ui_theme: str = Field(default="dark", env="UI_THEME")
    enable_syntax_highlighting: bool = Field(default=True, env="ENABLE_SYNTAX_HIGHLIGHTING")
    
    # Logging settings
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_to_file: bool = Field(default=True, env="LOG_TO_FILE")
    log_file_path: str = Field(default="logs/companion.log", env="LOG_FILE_PATH")
    log_max_size_mb: int = Field(default=10, env="LOG_MAX_SIZE_MB")
    log_backup_count: int = Field(default=5, env="LOG_BACKUP_COUNT")
    
    # Security settings
    encryption_key: Optional[str] = Field(default=None, env="ENCRYPTION_KEY")
    encrypt_data: bool = Field(default=True, env="ENCRYPT_DATA")
    session_timeout: int = Field(default=60, env="SESSION_TIMEOUT")
    
    # Behavior settings
    default_style: PersonalityStyle = Field(default=PersonalityStyle.FRIEND, env="DEFAULT_STYLE")
    enable_learning: bool = Field(default=True, env="ENABLE_LEARNING")
    auto_save_sessions: bool = Field(default=True, env="AUTO_SAVE_SESSIONS")
    enable_content_filtering: bool = Field(default=True, env="ENABLE_CONTENT_FILTERING")
    enable_pii_detection: bool = Field(default=True, env="ENABLE_PII_DETECTION")
    
    # Feedback and analytics
    enable_feedback: bool = Field(default=True, env="ENABLE_FEEDBACK")
    enable_analytics: bool = Field(default=True, env="ENABLE_ANALYTICS")
    
    # Development settings
    dev_mode: bool = Field(default=True, env="DEV_MODE")
    api_debug: bool = Field(default=False, env="API_DEBUG")
    use_test_data: bool = Field(default=False, env="USE_TEST_DATA")
    test_data_path: str = Field(default="tests/fixtures/", env="TEST_DATA_PATH")
    
    # Backup and export settings
    enable_auto_backup: bool = Field(default=True, env="ENABLE_AUTO_BACKUP")
    backup_interval_hours: int = Field(default=24, env="BACKUP_INTERVAL_HOURS")
    backup_retention_days: int = Field(default=30, env="BACKUP_RETENTION_DAYS")
    backup_path: str = Field(default="data/backups/", env="BACKUP_PATH")
    export_formats: List[str] = Field(default=["json", "txt", "markdown"], env="EXPORT_FORMATS")
    
    # Pydantic v2 configuration
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "case_sensitive": False}
        
    @field_validator("export_formats", mode="before")
    @classmethod
    def parse_export_formats(cls, v):
        """Parse comma-separated export formats."""
        if isinstance(v, str):
            return [fmt.strip() for fmt in v.split(",")]
        return v
    
    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v):
        """Validate temperature is between 0 and 2."""
        if not 0 <= v <= 2:
            raise ValueError("Temperature must be between 0 and 2")
        return v
    
    @field_validator("top_p")
    @classmethod
    def validate_top_p(cls, v):
        """Validate top_p is between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError("top_p must be between 0 and 1")
        return v
    
    @field_validator("memory_importance_threshold")
    @classmethod
    def validate_memory_threshold(cls, v):
        """Validate memory importance threshold is between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError("Memory importance threshold must be between 0 and 1")
        return v
    
    def get_data_dir(self) -> Path:
        """Get the data directory path."""
        return Path("data")
    
    def get_logs_dir(self) -> Path:
        """Get the logs directory path."""
        return Path("logs")
    
    def get_config_dir(self) -> Path:
        """Get the config directory path."""
        return Path("config")
    
    def ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        directories = [
            self.get_data_dir(),
            self.get_logs_dir(),
            self.get_config_dir(),
            Path(self.backup_path),
            Path(self.sqlite_db_path).parent,
            Path(self.log_file_path).parent,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_vector_db_config(self) -> Dict[str, Any]:
        """Get vector database configuration."""
        return {
            "type": self.vector_db_type,
            "host": self.vector_db_host,
            "port": self.vector_db_port,
            "collection": self.vector_db_collection,
        }
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration."""
        return {
            "api_base": self.lm_studio_api_base,
            "api_key": self.lm_studio_api_key,
            "model": self.default_model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
        }


def load_config(env_file: Optional[str] = None) -> Config:
    """
    Load configuration from environment variables and .env file.
    
    Args:
        env_file: Optional path to .env file
        
    Returns:
        Loaded configuration object
    """
    if env_file:
        os.environ.setdefault("ENV_FILE", env_file)
    
    config = Config()
    config.ensure_directories()
    
    return config


def get_config() -> Config:
    """Get the global configuration instance."""
    return load_config()