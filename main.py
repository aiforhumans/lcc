#!/usr/bin/env python3
"""
Local Chat Companion - Main Entry Point

A privacy-focused local chat assistant with adaptive memory and learning capabilities.
"""

import asyncio
import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.core.config import load_config
from src.core.logging_config import setup_logging
from src.chat.app import ChatApp


async def main():
    """Main entry point for the Local Chat Companion."""
    try:
        # Load configuration
        config = load_config()
        
        # Setup logging
        logger = setup_logging(config)
        logger.info("Starting Local Chat Companion")
        
        # Initialize and run the chat application
        app = ChatApp(config)
        await app.run()
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye! Chat session ended.")
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())