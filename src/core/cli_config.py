"""
Command-line argument parsing and configuration overrides for Local Chat Companion.
"""

import argparse
import sys
from typing import Dict, Any, Optional
from pathlib import Path

from ..core.config import Config, AppMode, VectorDBType, UIType, PersonalityStyle


class CLIConfig:
    """Command-line configuration parser and override handler."""
    
    def __init__(self):
        """Initialize the CLI configuration parser."""
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the command-line argument parser."""
        parser = argparse.ArgumentParser(
            prog="Local Chat Companion",
            description="A privacy-focused local chat assistant with adaptive memory and learning capabilities",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python main.py                                    # Start with default settings
  python main.py --style coach --debug             # Use coach personality with debug mode
  python main.py --model my-model --temperature 0.8 # Use specific model and temperature
  python main.py --list-conversations              # List saved conversations
  python main.py --load-conversation abc123        # Load specific conversation
  python main.py --lm-studio-url http://localhost:1234/v1  # Custom LM Studio URL
  
Configuration:
  Settings can be configured via .env file or command-line arguments.
  Command-line arguments override .env file settings.
  See .env.template for all available configuration options.
"""
        )
        
        # Basic options
        parser.add_argument(
            "--version",
            action="version",
            version="Local Chat Companion 0.1.0"
        )
        
        parser.add_argument(
            "--debug",
            action="store_true",
            help="Enable debug mode with verbose logging"
        )
        
        parser.add_argument(
            "--config",
            type=str,
            metavar="FILE",
            help="Path to custom .env configuration file"
        )
        
        # LM Studio settings
        lm_group = parser.add_argument_group("LM Studio Options")
        lm_group.add_argument(
            "--lm-studio-url",
            type=str,
            metavar="URL",
            help="LM Studio API base URL (default: http://localhost:1234/v1)"
        )
        
        lm_group.add_argument(
            "--model",
            type=str,
            metavar="MODEL",
            help="Default model name to use"
        )
        
        lm_group.add_argument(
            "--temperature",
            type=float,
            metavar="TEMP",
            help="Sampling temperature (0.0 to 2.0)"
        )
        
        lm_group.add_argument(
            "--max-tokens",
            type=int,
            metavar="TOKENS",
            help="Maximum tokens to generate"
        )
        
        # Personality and behavior
        behavior_group = parser.add_argument_group("Behavior Options")
        behavior_group.add_argument(
            "--style",
            type=str,
            choices=[style.value for style in PersonalityStyle],
            help="Personality style (friend, coach, assistant, custom)"
        )
        
        behavior_group.add_argument(
            "--no-learning",
            action="store_true",
            help="Disable learning from conversations"
        )
        
        behavior_group.add_argument(
            "--no-auto-save",
            action="store_true",
            help="Disable automatic saving of conversations"
        )
        
        # UI options
        ui_group = parser.add_argument_group("Interface Options")
        ui_group.add_argument(
            "--ui",
            type=str,
            choices=[ui.value for ui in UIType],
            help="User interface type (cli, web, desktop)"
        )
        
        ui_group.add_argument(
            "--theme",
            type=str,
            help="UI theme (dark, light, etc.)"
        )
        
        # Memory settings
        memory_group = parser.add_argument_group("Memory Options")
        memory_group.add_argument(
            "--max-session-memory",
            type=int,
            metavar="TURNS",
            help="Maximum number of conversation turns to keep in session memory"
        )
        
        memory_group.add_argument(
            "--vector-db",
            type=str,
            choices=[db.value for db in VectorDBType],
            help="Vector database type (chroma, qdrant)"
        )
        
        # Conversation management
        conv_group = parser.add_argument_group("Conversation Management")
        conv_group.add_argument(
            "--list-conversations",
            action="store_true",
            help="List all saved conversations and exit"
        )
        
        conv_group.add_argument(
            "--load-conversation",
            type=str,
            metavar="ID",
            help="Load a specific conversation by ID"
        )
        
        conv_group.add_argument(
            "--export-conversation",
            type=str,
            nargs=2,
            metavar=("ID", "FILE"),
            help="Export conversation to file (ID FILE)"
        )
        
        conv_group.add_argument(
            "--new-conversation",
            action="store_true",
            help="Start a new conversation (don't load previous)"
        )
        
        # System options
        system_group = parser.add_argument_group("System Options")
        system_group.add_argument(
            "--check-status",
            action="store_true",
            help="Check LM Studio status and exit"
        )
        
        system_group.add_argument(
            "--list-models",
            action="store_true",
            help="List available models and exit"
        )
        
        system_group.add_argument(
            "--data-dir",
            type=str,
            metavar="DIR",
            help="Custom data directory path"
        )
        
        return parser
    
    def parse_args(self, args: Optional[list] = None) -> argparse.Namespace:
        """Parse command-line arguments."""
        return self.parser.parse_args(args)
    
    def create_config_overrides(self, args: argparse.Namespace) -> Dict[str, Any]:
        """Create configuration overrides from parsed arguments."""
        overrides = {}
        
        # Map CLI arguments to config environment variables
        arg_mapping = {
            'debug': 'DEBUG',
            'lm_studio_url': 'LM_STUDIO_API_BASE',
            'model': 'DEFAULT_MODEL',
            'temperature': 'TEMPERATURE',
            'max_tokens': 'MAX_TOKENS',
            'style': 'DEFAULT_STYLE',
            'ui': 'UI_TYPE',
            'theme': 'UI_THEME',
            'max_session_memory': 'MAX_SESSION_MEMORY',
            'vector_db': 'VECTOR_DB_TYPE',
            'data_dir': 'DATA_DIR'
        }
        
        # Process direct mappings
        for arg_name, env_var in arg_mapping.items():
            value = getattr(args, arg_name, None)
            if value is not None:
                overrides[env_var] = str(value)
        
        # Handle special cases
        if getattr(args, 'no_learning', False):
            overrides['ENABLE_LEARNING'] = 'false'
        
        if getattr(args, 'no_auto_save', False):
            overrides['AUTO_SAVE_SESSIONS'] = 'false'
        
        return overrides
    
    def load_config_with_overrides(self, args: argparse.Namespace) -> Config:
        """Load configuration with command-line overrides."""
        import os
        
        # Apply environment overrides
        overrides = self.create_config_overrides(args)
        original_values = {}
        
        for key, value in overrides.items():
            original_values[key] = os.environ.get(key)
            os.environ[key] = value
        
        try:
            # Load config with custom env file if specified
            from ..core.config import load_config
            config = load_config(getattr(args, 'config', None))
            return config
        finally:
            # Restore original environment values
            for key, original_value in original_values.items():
                if original_value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = original_value


def parse_cli_args() -> argparse.Namespace:
    """Parse command-line arguments and return the namespace."""
    cli_config = CLIConfig()
    return cli_config.parse_args()


def create_config_from_cli(args: Optional[argparse.Namespace] = None) -> Config:
    """Create a configuration object from CLI arguments."""
    if args is None:
        args = parse_cli_args()
    
    cli_config = CLIConfig()
    return cli_config.load_config_with_overrides(args)