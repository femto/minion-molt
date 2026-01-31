#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Heartbeat example for minion-molt.

This script sends periodic heartbeats to Moltbook to keep your agent active.
Agents should send heartbeats every 4+ hours to stay active on the network.

The heartbeat uses the MoltbookAgent with AI reasoning to:
- Browse the latest feed
- Decide which posts are worth engaging with
- Upvote, comment, or follow based on content quality

Usage:
    # Run once (AI decides engagement)
    python examples/heartbeat.py

    # Run as daemon (heartbeat every 4 hours)
    python examples/heartbeat.py --daemon

    # Custom interval (6 hours)
    python examples/heartbeat.py --daemon --interval 6
"""

import asyncio
import json
import os
import sys
import argparse
from datetime import datetime

from minion_molt import MoltbookAgent, set_moltbook_api_key

# Configuration
CREDENTIALS_FILE = "moltbook_credentials.json"
DEFAULT_INTERVAL_HOURS = 4
DEFAULT_MODEL = "gpt-4.1"

HEARTBEAT_PROMPT = """Check the Moltbook feed for new posts. Browse through the latest posts and engage naturally:

1. First, get the latest feed (limit 10 posts)
2. Read through the posts and find ones that are interesting or valuable
3. If you find posts worth engaging with:
   - Upvote quality content that contributes to the community
   - Optionally leave a thoughtful comment if you have something meaningful to add
   - Consider following authors who consistently post good content
4. Don't engage with everything - be selective like a real community member
5. Summarize what you found and what actions you took

Be authentic - only engage with content you genuinely find interesting or valuable."""


def load_credentials() -> dict:
    """Load credentials from file if exists."""
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, "r") as f:
            return json.load(f)
    return {}


async def run_heartbeat(api_key: str, model: str = "gpt-4.1") -> bool:
    """Run a single heartbeat with AI-driven engagement."""
    print(f"[{datetime.now().isoformat()}] Starting heartbeat...")

    # Set API key
    set_moltbook_api_key(api_key)

    # Create agent
    agent = MoltbookAgent(llm=model)
    await agent.setup()

    # Run heartbeat with AI reasoning
    print("🤖 Agent is browsing feed and deciding on engagement...")
    response = await agent.run_async(HEARTBEAT_PROMPT)

    # Print response
    answer = response.answer if hasattr(response, 'answer') else str(response)
    print("\n📋 Heartbeat Summary:")
    print("-" * 40)
    print(answer)
    print("-" * 40)

    return True


async def run_daemon(api_key: str, interval_hours: float, model: str = "gpt-4.1"):
    """Run heartbeat daemon that sends heartbeats periodically."""
    interval_seconds = interval_hours * 3600

    print("=" * 50)
    print("🫀 Moltbook Heartbeat Daemon (AI-Powered)")
    print("=" * 50)
    print(f"Model: {model}")
    print(f"Interval: {interval_hours} hours ({interval_seconds} seconds)")
    print("Press Ctrl+C to stop")
    print("-" * 50)

    heartbeat_count = 0

    try:
        while True:
            heartbeat_count += 1
            print(f"\n{'='*50}")
            print(f"Heartbeat #{heartbeat_count}")
            print(f"{'='*50}")

            try:
                await run_heartbeat(api_key, model=model)
            except Exception as e:
                print(f"❌ Heartbeat error: {e}")

            # Wait for next interval
            next_time = datetime.now().timestamp() + interval_seconds
            next_datetime = datetime.fromtimestamp(next_time)
            print(f"\n⏰ Next heartbeat at: {next_datetime.isoformat()}")

            await asyncio.sleep(interval_seconds)

    except KeyboardInterrupt:
        print(f"\n\n🛑 Daemon stopped after {heartbeat_count} heartbeats.")


async def main():
    parser = argparse.ArgumentParser(description="Moltbook Heartbeat (AI-Powered)")
    parser.add_argument(
        "--daemon", "-d",
        action="store_true",
        help="Run as daemon (continuous heartbeats)"
    )
    parser.add_argument(
        "--interval", "-i",
        type=float,
        default=DEFAULT_INTERVAL_HOURS,
        help=f"Heartbeat interval in hours (default: {DEFAULT_INTERVAL_HOURS})"
    )
    parser.add_argument(
        "--api-key", "-k",
        type=str,
        help="Moltbook API key (optional, uses saved credentials if not provided)"
    )
    parser.add_argument(
        "--model", "-m",
        type=str,
        default=DEFAULT_MODEL,
        help=f"LLM model to use (default: {DEFAULT_MODEL})"
    )

    args = parser.parse_args()

    # Get API key
    api_key = args.api_key
    if not api_key:
        credentials = load_credentials()
        api_key = credentials.get("api_key")

    if not api_key:
        print("❌ No API key found!")
        print("   Either:")
        print("   1. Run registration first: python examples/example_register.py")
        print("   2. Provide API key: python examples/heartbeat.py --api-key YOUR_KEY")
        sys.exit(1)

    print(f"📋 Using API key: {api_key[:25]}...")

    if args.daemon:
        await run_daemon(api_key, args.interval, model=args.model)
    else:
        success = await run_heartbeat(api_key, model=args.model)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
