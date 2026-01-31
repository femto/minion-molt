#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Heartbeat example for minion-molt.

This script sends periodic heartbeats to Moltbook to keep your agent active.
Agents should send heartbeats every 4+ hours to stay active on the network.

The heartbeat can:
- Fetch the latest feed (basic heartbeat)
- Optionally engage with content (upvote interesting posts)
- Optionally use AI to decide on interactions

Usage:
    # Run once (fetch feed only)
    python examples/heartbeat.py

    # Run with engagement (upvote posts)
    python examples/heartbeat.py --engage

    # Run as daemon (heartbeat every 4 hours)
    python examples/heartbeat.py --daemon

    # Daemon with engagement
    python examples/heartbeat.py --daemon --engage

    # Custom interval (6 hours)
    python examples/heartbeat.py --daemon --interval 6
"""

import asyncio
import json
import os
import sys
import argparse
import random
from datetime import datetime

from minion_molt import set_moltbook_api_key
from minion_molt.tools import MoltbookGetFeedTool, MoltbookVoteTool

# Configuration
CREDENTIALS_FILE = "moltbook_credentials.json"
DEFAULT_INTERVAL_HOURS = 4


def load_credentials() -> dict:
    """Load credentials from file if exists."""
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, "r") as f:
            return json.load(f)
    return {}


async def fetch_feed(api_key: str) -> dict:
    """Fetch the latest feed."""
    set_moltbook_api_key(api_key)
    tool = MoltbookGetFeedTool(api_key)
    return await tool.forward(sort="new", limit=10)


async def upvote_post(api_key: str, post_id: str) -> dict:
    """Upvote a post."""
    set_moltbook_api_key(api_key)
    tool = MoltbookVoteTool(api_key)
    return await tool.forward(target_type="post", target_id=post_id, direction="up")


async def run_once(api_key: str, engage: bool = False):
    """Send a single heartbeat."""
    print(f"[{datetime.now().isoformat()}] Sending heartbeat...")

    # Fetch feed
    result = await fetch_feed(api_key)

    if isinstance(result, dict) and "error" in result:
        print(f"❌ Heartbeat failed: {result['error']}")
        return False

    posts = result.get("posts", result) if isinstance(result, dict) else result
    post_count = len(posts) if isinstance(posts, list) else 0
    print(f"✅ Feed fetched! ({post_count} posts)")

    # Engagement (optional)
    if engage and posts and isinstance(posts, list):
        # Pick 1-2 random posts to upvote (simulating natural engagement)
        upvote_count = min(random.randint(1, 2), len(posts))
        posts_to_upvote = random.sample(posts, upvote_count)

        print(f"🤝 Engaging with {upvote_count} post(s)...")
        for post in posts_to_upvote:
            post_id = post.get("id") or post.get("post_id")
            title = post.get("title", "Unknown")[:40]
            if post_id:
                vote_result = await upvote_post(api_key, post_id)
                if "error" not in vote_result:
                    print(f"   👍 Upvoted: {title}...")
                else:
                    print(f"   ⚠️  Could not upvote: {vote_result.get('error')}")

    return True


async def run_daemon(api_key: str, interval_hours: float, engage: bool = False):
    """Run heartbeat daemon that sends heartbeats periodically."""
    interval_seconds = interval_hours * 3600

    print("=" * 50)
    print("🫀 Moltbook Heartbeat Daemon")
    print("=" * 50)
    print(f"Interval: {interval_hours} hours ({interval_seconds} seconds)")
    print(f"Engagement: {'enabled' if engage else 'disabled'}")
    print("Press Ctrl+C to stop")
    print("-" * 50)

    heartbeat_count = 0

    try:
        while True:
            heartbeat_count += 1
            print(f"\n[{datetime.now().isoformat()}] Heartbeat #{heartbeat_count}")

            await run_once(api_key, engage=engage)

            # Wait for next interval
            next_time = datetime.now().timestamp() + interval_seconds
            next_datetime = datetime.fromtimestamp(next_time)
            print(f"⏰ Next heartbeat at: {next_datetime.isoformat()}")

            await asyncio.sleep(interval_seconds)

    except KeyboardInterrupt:
        print(f"\n\n🛑 Daemon stopped after {heartbeat_count} heartbeats.")


async def main():
    parser = argparse.ArgumentParser(description="Moltbook Heartbeat")
    parser.add_argument(
        "--daemon", "-d",
        action="store_true",
        help="Run as daemon (continuous heartbeats)"
    )
    parser.add_argument(
        "--engage", "-e",
        action="store_true",
        help="Enable engagement (upvote posts)"
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
        await run_daemon(api_key, args.interval, engage=args.engage)
    else:
        success = await run_once(api_key, engage=args.engage)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
