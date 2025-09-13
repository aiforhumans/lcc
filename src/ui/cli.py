"""
CLI interface for Local Chat Companion.

Provides a rich, interactive command-line interface using Rich for formatting.
"""

import asyncio
import sys
from typing import Optional, List
from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.prompt import Prompt, Confirm
    from rich.markdown import Markdown
    from rich.syntax import Syntax
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich import print as rprint
except ImportError:
    # Fallback if Rich is not available
    Console = None
    Panel = None
    rprint = print

try:
    import structlog
except ImportError:
    structlog = None

from ..core.config import Config
from ..core.logging_config import LoggerMixin
from ..chat.lm_studio import LMStudioClient, LMStudioError, ChatMessage
from ..chat.conversation import ConversationManager


class CLIInterface(LoggerMixin):
    """Rich CLI interface for the chat companion."""
    
    def __init__(self, config: Config):
        """Initialize the CLI interface."""
        self.config = config
        self.console = Console() if Console else None
        self.conversation_manager = ConversationManager(config)
        self.lm_studio_client = None
        
        # CLI state
        self.running = False
        self.current_conversation_id = None
        
        self.logger.info("CLI interface initialized")
    
    def print_welcome(self):
        """Print welcome message and status."""
        if not self.console:
            print("🤖 Local Chat Companion - Welcome!")
            return
        
        welcome_text = f"""
# 🤖 Local Chat Companion

Welcome to your privacy-focused AI chat assistant!

**Configuration:**
- 🎭 Style: {self.config.default_style}
- 🔗 LM Studio: {self.config.lm_studio_api_base}
- 📝 Model: {self.config.default_model}
- 🧠 Session Memory: {self.config.max_session_memory} turns

**Commands:**
- Type your message to chat
- `/help` - Show all commands
- `/new` - Start new conversation
- `/save` - Save current conversation
- `/list` - List saved conversations
- `/load <id>` - Load a conversation
- `/clear` - Clear current conversation
- `/status` - Check LM Studio status
- `/quit` or `/exit` - Exit the application

Type your first message to begin chatting!
"""
        
        panel = Panel(
            Markdown(welcome_text),
            title="🏠 Welcome",
            border_style="bright_blue"
        )
        self.console.print(panel)
    
    def print_error(self, message: str, exception: Optional[Exception] = None):
        """Print an error message."""
        if not self.console:
            print(f"❌ Error: {message}")
            return
        
        error_text = f"❌ **Error:** {message}"
        if exception and self.config.debug:
            error_text += f"\n\n```\n{str(exception)}\n```"
        
        panel = Panel(
            Markdown(error_text),
            title="Error",
            border_style="red"
        )
        self.console.print(panel)
    
    def print_info(self, message: str, title: str = "Info"):
        """Print an info message."""
        if not self.console:
            print(f"ℹ️ {message}")
            return
        
        panel = Panel(
            Markdown(f"ℹ️ {message}"),
            title=title,
            border_style="blue"
        )
        self.console.print(panel)
    
    def print_warning(self, message: str):
        """Print a warning message."""
        if not self.console:
            print(f"⚠️ Warning: {message}")
            return
        
        panel = Panel(
            Markdown(f"⚠️ **Warning:** {message}"),
            title="Warning",
            border_style="yellow"
        )
        self.console.print(panel)
    
    def print_user_message(self, message: str):
        """Print a user message."""
        if not self.console:
            print(f"👤 You: {message}")
            return
        
        panel = Panel(
            Text(message, style="bright_cyan"),
            title="👤 You",
            border_style="cyan"
        )
        self.console.print(panel)
    
    def print_assistant_message(self, message: str, stats: Optional[dict] = None):
        """Print an assistant message with optional stats."""
        if not self.console:
            print(f"🤖 Assistant: {message}")
            return
        
        # Format the message content
        content = Markdown(message)
        
        # Add stats if available
        if stats and self.config.debug:
            stats_text = f"\n\n---\n"
            stats_text += f"*Tokens: {stats.get('tokens', 'N/A')} | "
            stats_text += f"Speed: {stats.get('tokens_per_second', 'N/A'):.1f} tok/s | "
            stats_text += f"Time: {stats.get('generation_time', 'N/A'):.2f}s*"
            content = Markdown(message + stats_text)
        
        panel = Panel(
            content,
            title="🤖 Assistant",
            border_style="green"
        )
        self.console.print(panel)
    
    def show_typing_indicator(self):
        """Show a typing indicator while waiting for response."""
        if not self.console:
            print("🤖 Assistant is thinking...")
            return None
        
        return Progress(
            SpinnerColumn(),
            TextColumn("🤖 Assistant is thinking..."),
            console=self.console,
            transient=True
        )
    
    async def show_status(self):
        """Show LM Studio connection status."""
        if not self.lm_studio_client:
            self.print_error("LM Studio client not initialized")
            return
        
        try:
            with self.show_typing_indicator() or nullcontext():
                health = await self.lm_studio_client.health_check()
            
            if health["status"] == "healthy":
                status_text = f"""
**LM Studio Status:** ✅ Connected

**Models Available:** {health['total_models']}
**Models Loaded:** {health['loaded_models']}

**Loaded Models:**
{chr(10).join(f"• {model}" for model in health['available_models'])}
"""
                self.print_info(status_text, "🔍 LM Studio Status")
            else:
                self.print_error(f"LM Studio is not healthy: {health.get('error', 'Unknown error')}")
                
        except Exception as e:
            self.print_error("Failed to check LM Studio status", e)
    
    def list_conversations(self):
        """List saved conversations."""
        conversations = self.conversation_manager.list_conversations()
        
        if not conversations:
            self.print_info("No saved conversations found.")
            return
        
        if not self.console:
            print("Saved conversations:")
            for conv in conversations[:10]:  # Show first 10
                print(f"- {conv['id'][:8]}: {conv['title']} ({conv['turns_count']} turns)")
            return
        
        table = Table(title="💾 Saved Conversations")
        table.add_column("ID", style="cyan", width=10)
        table.add_column("Title", style="bright_white")
        table.add_column("Turns", justify="right", style="yellow")
        table.add_column("Updated", style="dim")
        
        for conv in conversations[:20]:  # Show first 20
            table.add_row(
                conv['id'][:8] + "...",
                conv['title'][:50],
                str(conv['turns_count']),
                conv['updated_at'][:16]  # YYYY-MM-DD HH:MM
            )
        
        self.console.print(table)
    
    def get_user_input(self) -> str:
        """Get user input with prompt."""
        if not self.console:
            return input("💬 You: ").strip()
        
        try:
            user_input = Prompt.ask(
                "[bright_cyan]💬 You[/bright_cyan]",
                console=self.console
            ).strip()
            return user_input
        except (KeyboardInterrupt, EOFError):
            return "/quit"
    
    def confirm_action(self, message: str) -> bool:
        """Get confirmation from user."""
        if not self.console:
            response = input(f"{message} (y/n): ").lower()
            return response in ['y', 'yes']
        
        return Confirm.ask(message, console=self.console)
    
    async def handle_command(self, command: str) -> bool:
        """Handle CLI commands. Returns True if app should continue."""
        parts = command[1:].split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if cmd in ["quit", "exit", "q"]:
            if self.conversation_manager.current_conversation:
                if self.confirm_action("Save current conversation before exiting?"):
                    self.conversation_manager.save_conversation()
            return False
        
        elif cmd in ["help", "h"]:
            self.show_help()
        
        elif cmd == "new":
            self.conversation_manager.start_new_conversation()
            self.print_info("Started new conversation")
        
        elif cmd == "save":
            if self.conversation_manager.current_conversation:
                filepath = self.conversation_manager.save_conversation()
                self.print_info(f"Conversation saved to {filepath.name}")
            else:
                self.print_warning("No conversation to save")
        
        elif cmd == "list":
            self.list_conversations()
        
        elif cmd == "load":
            if not args:
                self.print_error("Please provide a conversation ID")
            else:
                try:
                    conversation = self.conversation_manager.load_conversation(args)
                    self.conversation_manager.current_conversation = conversation
                    self.print_info(f"Loaded conversation: {conversation.title}")
                except FileNotFoundError:
                    self.print_error(f"Conversation {args} not found")
                except Exception as e:
                    self.print_error("Failed to load conversation", e)
        
        elif cmd == "clear":
            if self.confirm_action("Clear current conversation?"):
                self.conversation_manager.current_conversation = None
                self.print_info("Conversation cleared")
        
        elif cmd == "status":
            await self.show_status()
        
        else:
            self.print_error(f"Unknown command: /{cmd}. Type /help for available commands.")
        
        return True
    
    def show_help(self):
        """Show help information."""
        help_text = """
# 📚 Commands Help

**Conversation Management:**
- `/new` - Start a new conversation
- `/save` - Save the current conversation
- `/load <id>` - Load a saved conversation by ID
- `/list` - List all saved conversations
- `/clear` - Clear the current conversation

**System:**
- `/status` - Check LM Studio connection and model status
- `/help` - Show this help message
- `/quit` or `/exit` - Exit the application

**Chat:**
- Just type your message to chat with the AI
- Conversations are automatically saved when enabled
- Use Ctrl+C to interrupt AI generation

**Tips:**
- Use `/status` to check if your model is loaded
- Conversations preserve context between messages
- Debug info is shown when DEBUG=true in config
"""
        
        if not self.console:
            print(help_text)
            return
        
        panel = Panel(
            Markdown(help_text),
            title="📚 Help",
            border_style="bright_blue"
        )
        self.console.print(panel)
    
    async def run(self):
        """Run the CLI interface."""
        self.running = True
        self.print_welcome()
        
        # Initialize LM Studio client
        self.lm_studio_client = LMStudioClient(self.config)
        
        try:
            async with self.lm_studio_client:
                # Check LM Studio status on startup
                await self.show_status()
                
                # Start with a new conversation
                self.conversation_manager.start_new_conversation()
                
                # Main chat loop
                while self.running:
                    try:
                        user_input = self.get_user_input()
                        
                        if not user_input:
                            continue
                        
                        # Handle commands
                        if user_input.startswith('/'):
                            should_continue = await self.handle_command(user_input)
                            if not should_continue:
                                break
                            continue
                        
                        # Process chat message
                        await self.process_chat_message(user_input)
                        
                    except KeyboardInterrupt:
                        self.print_info("\nUse /quit to exit gracefully")
                        continue
                    except Exception as e:
                        self.logger.error("Unexpected error in chat loop", error=str(e), exc_info=True)
                        self.print_error("An unexpected error occurred", e)
                        continue
        
        except Exception as e:
            self.logger.error("Failed to initialize LM Studio client", error=str(e), exc_info=True)
            self.print_error("Failed to connect to LM Studio. Is it running?", e)
        
        finally:
            self.print_info("👋 Goodbye!")
    
    async def process_chat_message(self, user_input: str):
        """Process a chat message through the LM Studio client."""
        try:
            # Print user message
            self.print_user_message(user_input)
            
            # Add to conversation
            turn = self.conversation_manager.add_user_message(user_input)
            
            # Get messages for LLM
            messages = self.conversation_manager.get_messages_for_llm()
            
            # Show typing indicator and generate response
            with self.show_typing_indicator() or nullcontext():
                response = await self.lm_studio_client.chat_completion(messages)
            
            # Add response to conversation
            self.conversation_manager.add_assistant_response(response)
            
            # Print assistant response
            stats = {
                'tokens': response.usage.total_tokens,
                'tokens_per_second': response.stats.tokens_per_second,
                'generation_time': response.stats.generation_time
            }
            self.print_assistant_message(response.message.content, stats)
            
            # Auto-save if enabled
            self.conversation_manager.auto_save()
            
        except Exception as e:
            self.logger.error("Error processing chat message", error=str(e), exc_info=True)
            self.print_error("Failed to get response from AI", e)


# Context manager for when Rich is not available
class nullcontext:
    """Null context manager for fallback when Rich is not available."""
    def __enter__(self):
        return None
    def __exit__(self, *args):
        pass
