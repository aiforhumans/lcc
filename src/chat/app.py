"""
Chat application entry point with full LM Studio integration.

This implements Phase 1: Core Chat functionality with real LLM communication.
"""

import asyncio
from typing import Optional

try:
    from ..core.config import Config
    from ..core.logging_config import get_logger
    from ..ui.cli import CLIInterface
except ImportError:
    # Fallback for development
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent.parent))
    from src.core.config import Config
    from src.core.logging_config import get_logger
    from src.ui.cli import CLIInterface


class ChatApp:
    """Main chat application class with full LM Studio integration."""
    
    def __init__(self, config: Config):
        """Initialize the chat application."""
        self.config = config
        self.logger = get_logger("ChatApp")
        self.running = False
        
        # Initialize the CLI interface
        self.cli = CLIInterface(config)
    
    async def run(self):
        """Run the chat application with full CLI interface."""
        self.logger.info("Starting Local Chat Companion with Phase 1 features")
        self.running = True
        
        try:
            # Run the CLI interface
            await self.cli.run()
            
        except Exception as e:
            self.logger.error("Error in chat application", error=str(e), exc_info=True)
            raise
        
        finally:
            self.running = False
            self.logger.info("Chat application stopped")
    
    async def stop(self):
        """Stop the chat application."""
        self.running = False
        self.logger.info("Stopping chat application")