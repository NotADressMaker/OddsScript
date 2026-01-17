#!/usr/bin/env python3
"""
SportsBetLang AI Chat Assistant CLI

Interactive command-line interface for natural language sports queries.
"""

import os
import sys
import asyncio
from typing import Optional
import uuid

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sportsbetlang.api.chat import ChatService, SportsAnalyticsService


class ChatAssistantCLI:
    """Interactive CLI for AI sports chat assistant."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize CLI with API key."""
        try:
            self.chat_service = ChatService(api_key=api_key)
            self.analytics_service = SportsAnalyticsService()
            self.session_id = str(uuid.uuid4())
            self.chat_service.create_session(self.session_id)
            print("✓ SportsBetLang AI Chat Assistant initialized")
            print(f"✓ Session ID: {self.session_id}\n")
        except ValueError as e:
            print(f"✗ Error: {e}")
            print("\nPlease set your ANTHROPIC_API_KEY environment variable:")
            print("  export ANTHROPIC_API_KEY='your-api-key-here'")
            sys.exit(1)

    def print_banner(self):
        """Print welcome banner."""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║         SportsBetLang AI Chat Assistant v1.0                 ║
║                                                               ║
║  Ask me anything about sports analytics and predictions!     ║
╚══════════════════════════════════════════════════════════════╝

Example queries:
  • "Predict LeBron's points tonight"
  • "Compare Mahomes and Allen this season"
  • "What's the best bet for tonight's Lakers game?"
  • "Show me Ohtani's hitting trend over last 10 games"

Commands:
  /help     - Show this help message
  /history  - View conversation history
  /clear    - Clear conversation history
  /exit     - Exit the chat assistant

"""
        print(banner)

    async def run_interactive(self):
        """Run interactive chat loop."""
        self.print_banner()

        while True:
            try:
                # Get user input
                query = input("\n🏀 You: ").strip()

                if not query:
                    continue

                # Handle commands
                if query.startswith('/'):
                    await self.handle_command(query)
                    continue

                # Process query
                print("\n🤖 Assistant: ", end='', flush=True)
                result = await self.chat_service.process_query(
                    query=query,
                    session_id=self.session_id
                )

                if "error" in result:
                    print(f"✗ Error: {result['error']}")
                else:
                    print(result['answer'])

                    # Show prediction if available
                    if result.get('prediction'):
                        print("\n📊 Prediction Details:")
                        for key, value in result['prediction'].items():
                            print(f"  {key}: {value}")

            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\n✗ Error: {str(e)}")

    async def handle_command(self, command: str):
        """Handle CLI commands."""
        cmd = command.lower().strip()

        if cmd == '/help':
            self.print_banner()

        elif cmd == '/history':
            history = self.chat_service.get_session_history(self.session_id)
            if not history:
                print("No conversation history yet.")
            else:
                print(f"\n📜 Conversation History ({len(history)} messages):\n")
                for i, msg in enumerate(history, 1):
                    role = "You" if msg['role'] == 'user' else "Assistant"
                    content = msg['content']
                    # Truncate long messages
                    if len(content) > 100:
                        content = content[:100] + "..."
                    print(f"{i}. {role}: {content}")

        elif cmd == '/clear':
            self.chat_service.clear_session(self.session_id)
            print("✓ Conversation history cleared.")

        elif cmd == '/exit' or cmd == '/quit':
            print("Goodbye!")
            sys.exit(0)

        else:
            print(f"Unknown command: {command}")
            print("Type /help for available commands.")

    def run_single_query(self, query: str):
        """Run a single query and exit."""
        async def _run():
            print(f"\n🏀 Query: {query}\n")
            print("🤖 Assistant: ", end='', flush=True)

            result = await self.chat_service.process_query(
                query=query,
                session_id=self.session_id
            )

            if "error" in result:
                print(f"✗ Error: {result['error']}")
                return 1
            else:
                print(result['answer'])
                if result.get('prediction'):
                    print("\n📊 Prediction Details:")
                    for key, value in result['prediction'].items():
                        print(f"  {key}: {value}")
                return 0

        return asyncio.run(_run())


def main():
    """Main CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="SportsBetLang AI Chat Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python chat_assistant.py

  # Single query
  python chat_assistant.py -q "Predict LeBron's points tonight"

  # With custom API key
  python chat_assistant.py --api-key "your-key-here"

Environment Variables:
  ANTHROPIC_API_KEY    Your Anthropic API key for Claude AI
        """
    )

    parser.add_argument(
        '-q', '--query',
        type=str,
        help='Run a single query and exit'
    )

    parser.add_argument(
        '--api-key',
        type=str,
        help='Anthropic API key (or set ANTHROPIC_API_KEY env var)'
    )

    args = parser.parse_args()

    # Initialize CLI
    cli = ChatAssistantCLI(api_key=args.api_key)

    # Run single query or interactive mode
    if args.query:
        exit_code = cli.run_single_query(args.query)
        sys.exit(exit_code)
    else:
        asyncio.run(cli.run_interactive())


if __name__ == '__main__':
    main()
