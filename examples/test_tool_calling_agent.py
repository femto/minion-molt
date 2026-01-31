#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Experimental: Test ToolCallingAgent with Moltbook tools.

ToolCallingAgent doesn't depend on stop sequences, so it can work with
models like gpt-5.2 that don't support stop parameter.

Usage:
    python examples/test_tool_calling_agent.py                    # Test with gpt-4.1
    python examples/test_tool_calling_agent.py --model gpt-5.2    # Test with gpt-5.2
    python examples/test_tool_calling_agent.py compare            # Compare agents
"""

import asyncio
import json
import os
import argparse

from minion.agents.tool_calling_agent import ToolCallingAgent
from minion_molt import create_moltbook_tools, set_moltbook_api_key

# Configuration
CREDENTIALS_FILE = "moltbook_credentials.json"

SYSTEM_PROMPT = """You are a helpful AI agent that can interact with Moltbook, a social platform for AI agents.

You have tools to:
- Browse and search posts
- Create posts and comments
- Vote on content
- Follow other agents
- Join communities (submolts)

Use the appropriate tools to help with user requests. When done, use final_answer to provide your response.
"""


def load_credentials() -> dict:
    """Load credentials from file if exists."""
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, "r") as f:
            return json.load(f)
    return {}


async def test_tool_calling_agent(model: str = "gpt-4.1"):
    """Test ToolCallingAgent with Moltbook tools."""
    print("=" * 60)
    print(f"🧪 Testing ToolCallingAgent with {model}")
    print("=" * 60)

    # Load credentials
    credentials = load_credentials()
    if credentials.get("api_key"):
        print(f"📋 Using credentials for: {credentials.get('name')}")
        set_moltbook_api_key(credentials["api_key"])
    else:
        print("⚠️  No credentials found, some features may be limited")

    # Create ToolCallingAgent with Moltbook tools
    moltbook_tools = create_moltbook_tools()

    agent = ToolCallingAgent(
        llm=model,
        tools=moltbook_tools,
        system_prompt=SYSTEM_PROMPT,
        max_steps=10  # Limit steps to avoid timeout
    )
    await agent.setup()

    print(f"\n🤖 Agent created with {len(agent.tools)} tools")
    print(f"   Model: {model}")

    # Test 1: Simple tool call - Get feed
    print("\n" + "-" * 60)
    print("Test 1: Get latest feed (simple tool call)")
    print("-" * 60)

    try:
        response = await agent.run_async("Get the 3 latest posts from Moltbook feed and tell me their titles")
        answer = response.answer if hasattr(response, 'answer') else str(response)
        print(f"✅ Response:\n{answer[:500]}...")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Test 2: Search
    print("\n" + "-" * 60)
    print("Test 2: Search for posts")
    print("-" * 60)

    try:
        response = await agent.run_async("Search for posts about 'agent' on Moltbook")
        answer = response.answer if hasattr(response, 'answer') else str(response)
        print(f"✅ Response:\n{answer[:500]}...")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Test 3: Multi-step reasoning
    print("\n" + "-" * 60)
    print("Test 3: Multi-step (get feed + analyze)")
    print("-" * 60)

    try:
        response = await agent.run_async(
            "Get the latest 5 posts from Moltbook, pick the most interesting one, and explain why."
        )
        answer = response.answer if hasattr(response, 'answer') else str(response)
        print(f"✅ Response:\n{answer[:800]}...")
    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n" + "=" * 60)
    print(f"✅ ToolCallingAgent tests with {model} completed!")
    print("=" * 60)


async def compare_models():
    """Compare ToolCallingAgent across different models."""
    print("=" * 60)
    print("🔬 Comparing ToolCallingAgent across models")
    print("=" * 60)

    # Load credentials
    credentials = load_credentials()
    if credentials.get("api_key"):
        set_moltbook_api_key(credentials["api_key"])

    task = "Get the 3 latest posts from Moltbook and summarize them briefly"

    models = ["gpt-4.1", "gpt-5.2"]

    for model in models:
        print("\n" + "=" * 60)
        print(f"Testing: {model}")
        print("=" * 60)

        try:
            agent = ToolCallingAgent(
                llm=model,
                tools=create_moltbook_tools(),
                system_prompt=SYSTEM_PROMPT,
                max_steps=10
            )
            await agent.setup()

            response = await agent.run_async(task)
            answer = response.answer if hasattr(response, 'answer') else str(response)
            print(f"✅ {model} Response:\n{answer[:600]}...")

        except Exception as e:
            print(f"❌ {model} Error: {e}")

    print("\n" + "=" * 60)
    print("✅ Model comparison completed!")
    print("=" * 60)


async def main():
    parser = argparse.ArgumentParser(description="Test ToolCallingAgent")
    parser.add_argument(
        "--model", "-m",
        type=str,
        default="gpt-4.1",
        help="LLM model to use (default: gpt-4.1)"
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="test",
        choices=["test", "compare"],
        help="Command: test (single model) or compare (multiple models)"
    )

    args = parser.parse_args()

    if args.command == "compare":
        await compare_models()
    else:
        await test_tool_calling_agent(model=args.model)


if __name__ == "__main__":
    asyncio.run(main())
