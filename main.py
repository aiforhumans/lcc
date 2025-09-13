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

from src.core.cli_config import parse_cli_args, create_config_from_cli
from src.core.logging_config import setup_logging
from src.chat.app import ChatApp
from src.chat.conversation import ConversationManager
from src.chat.lm_studio import LMStudioClient


async def handle_special_commands(args, config):
    """Handle special CLI commands that don't require the full app."""
    
    if args.check_status:
        print("🔍 Checking LM Studio status...")
        async with LMStudioClient(config) as client:
            health = await client.health_check()
            if health["status"] == "healthy":
                print("✅ LM Studio is running and healthy")
                print(f"📊 Total models: {health['total_models']}")
                print(f"🚀 Loaded models: {health['loaded_models']}")
                for model in health['available_models']:
                    print(f"  • {model}")
            else:
                print(f"❌ LM Studio is not healthy: {health.get('error', 'Unknown error')}")
                sys.exit(1)
        return True
    
    if args.list_models:
        print("📋 Listing available models...")
        async with LMStudioClient(config) as client:
            models = await client.list_models()
            if models:
                for model in models:
                    status = "🟢 Loaded" if model.is_loaded else "⚪ Available"
                    print(f"{status} {model.id}")
                    print(f"    Architecture: {model.architecture}")
                    print(f"    Quantization: {model.quantization}")
                    print(f"    Max Context: {model.max_context_length}")
                    print()
            else:
                print("No models found")
        return True
    
    if args.list_conversations:
        print("💾 Listing saved conversations...")
        manager = ConversationManager(config)
        conversations = manager.list_conversations()
        if conversations:
            for conv in conversations:
                print(f"🗂️  {conv['id'][:8]}... - {conv['title']}")
                print(f"    Created: {conv['created_at'][:16]} | Turns: {conv['turns_count']}")
                print()
        else:
            print("No saved conversations found")
        return True
    
    if args.export_conversation:
        conv_id, output_file = args.export_conversation
        print(f"📤 Exporting conversation {conv_id} to {output_file}...")
        manager = ConversationManager(config)
        try:
            conversation = manager.load_conversation(conv_id)
            import json
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(conversation.to_dict(), f, indent=2, ensure_ascii=False)
            print(f"✅ Conversation exported to {output_file}")
        except Exception as e:
            print(f"❌ Export failed: {e}")
            sys.exit(1)
        return True
    
    return False


async def main():
    """Main entry point for the Local Chat Companion."""
    try:
        # Parse command-line arguments
        args = parse_cli_args()
        
        # Create configuration with CLI overrides
        config = create_config_from_cli(args)
        
        # Setup logging
        logger = setup_logging(config)
        logger.info("Starting Local Chat Companion with Phase 1 features")
        
        # Handle special commands that don't require the full app
        if await handle_special_commands(args, config):
            return
        
        # Initialize and run the chat application
        app = ChatApp(config)
        await app.run()
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye! Chat session ended.")
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        if "--debug" in sys.argv:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())