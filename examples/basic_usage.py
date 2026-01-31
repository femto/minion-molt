#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Basic usage example for minion-molt.

This example shows how to use a Minion agent with Moltbook tools.

Usage:
    cd /Users/femtozheng/python-project/minion-molt
    python examples/basic_usage.py
"""

import asyncio
import json
import os
from minion_molt import MoltbookAgent, create_moltbook_tools, set_moltbook_api_key

# Configuration
LLM_MODEL = "gpt-4.1"  # Model to use (must support stop sequences for CodeAgent)
CREDENTIALS_FILE = "moltbook_credentials.json"


def load_credentials() -> dict:
    """Load credentials from file if exists."""
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, "r") as f:
            return json.load(f)
    return {}


async def main():
    print("=" * 50)
    print("🦞 Minion-Molt Basic Usage")
    print("=" * 50)

    # Load credentials if available
    credentials = load_credentials()
    if credentials.get("api_key"):
        print(f"📋 Loaded credentials for: {credentials.get('name')}")
        set_moltbook_api_key(credentials["api_key"])
    else:
        print("⚠️  No credentials found. Some features may require registration.")
        print("   Run: python examples/example_register.py")

    # Create agent
    agent = MoltbookAgent(llm=LLM_MODEL)
    await agent.setup()

    # Search for content (works without auth)
    print("\n--- 🔍 Searching ---")
    response = await agent.run_async(
        "Search for posts about AI agents"
    )
    print(response.answer)
    print()

    # Get feed (requires auth)
    if credentials.get("api_key"):
        print("\n--- 📰 Getting Feed ---")
        response = await agent.run_async(
            "Get the latest posts from the Moltbook feed"
        )
        print(response.answer)
        print()


async def method2_with_existing_agent():
    """Method 2: Add Moltbook tools to an existing agent."""
    from minion.agents.code_agent import CodeAgent

    print("=" * 50)
    print("Adding Moltbook tools to existing agent")
    print("=" * 50)

    # Load credentials if available
    credentials = load_credentials()
    if credentials.get("api_key"):
        set_moltbook_api_key(credentials["api_key"])

    # Get Moltbook tools
    moltbook_tools = create_moltbook_tools()

    # Add to your existing agent
    agent = CodeAgent(
        llm=LLM_MODEL,
        tools=moltbook_tools,
        system_prompt="You are an AI agent that can interact with Moltbook social network."
    )

    # Setup the agent
    await agent.setup()

    # Use the agent
    response = await agent.run_async("What tools do I have available?")
    print(response.answer)
    print()


if __name__ == "__main__":
    asyncio.run(main())
    # asyncio.run(method2_with_existing_agent())
