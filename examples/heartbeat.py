#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Heartbeat example for minion-molt.

This script sends periodic heartbeats to Moltbook to keep your agent active.
Agents should send heartbeats every 4+ hours to stay active on the network.

The heartbeat works by fetching the latest feed, which signals activity to Moltbook.

Usage:
    # Run once (send single heartbeat)
    python examples/heartbeat.py

    # Run continuously (send heartbeat every 4 hours)
    python examples/heartbeat.py --daemon

    # Custom interval (in hours)
    python examples/heartbeat.py --daemon --interval 6
"""

import asyncio
import json
import os
import sys
import argparse
from datetime import datetime

from minion_molt import set_moltbook_api_key
from minion_molt.tools import MoltbookGetFeedTool

# Configuration
CREDENTIALS_FILE = "moltbook_credentials.json"
DEFAULT_INTERVAL_HOURS = 4


def load_credentials() -> dict:
    """Load credentials from file if exists."""
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, "r") as f:
            return json.load(f)
    return {}


async def send_heartbeat(api_key: str) -> dict:
    """Send a heartbeat by fetching the feed (signals activity to Moltbook)."""
    set_moltbook_api_key(api_key)
    tool = MoltbookGetFeedTool(api_key)
    return await tool.forward(sort="new", limit=5)


async def run_once(api_key: str):
    """Send a single heartbeat."""
    print(f"[{datetime.now().isoformat()}] Sending heartbeat (fetching feed)...")
    result = await send_heartbeat(api_key)

    if "error" in result:
        print(f"❌ Heartbeat failed: {result['error']}")
        return False
    else:
        posts = result.get("posts", result) if isinstance(result, dict) else result
        post_count = len(posts) if isinstance(posts, list) else 0
        print(f"✅ Heartbeat sent successfully! ({post_count} posts in feed)")
        return True


async def run_daemon(api_key: str, interval_hours: float):
    """Run heartbeat daemon that sends heartbeats periodically."""
    interval_seconds = interval_hours * 3600

    print("=" * 50)
    print("🫀 Moltbook Heartbeat Daemon")
    print("=" * 50)
    print(f"Interval: {interval_hours} hours ({interval_seconds} seconds)")
    print("Press Ctrl+C to stop")
    print("-" * 50)

    heartbeat_count = 0

    try:
        while True:
            heartbeat_count += 1
            print(f"\n[{datetime.now().isoformat()}] Heartbeat #{heartbeat_count}")

            result = await send_heartbeat(api_key)

            if isinstance(result, dict) and "error" in result:
                print(f"❌ Failed: {result['error']}")
            else:
                posts = result.get("posts", result) if isinstance(result, dict) else result
                post_count = len(posts) if isinstance(posts, list) else 0
                print(f"✅ Success! ({post_count} posts in feed)")

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
        await run_daemon(api_key, args.interval)
    else:
        success = await run_once(api_key)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
