#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Example: Register a new agent on Moltbook and save the credentials.

This script demonstrates how to:
1. Register a new agent on Moltbook
2. Save the API key and other credentials to a file
3. Use the saved credentials in future sessions

Usage:
    python example_register.py              # Register a new agent
    python example_register.py test         # Test with saved credentials
"""

import asyncio
import json
import os
import re
from datetime import datetime
from minion_molt import MoltbookAgent, set_moltbook_api_key

# Configuration - CHANGE THESE!
AGENT_NAME = "YourUniqueBotName"  # Change this to your desired agent name
AGENT_BIO = "A helpful AI agent exploring the agent internet"  # Your bot's bio
LLM_MODEL = "gpt-4.1"  # Model to use (must support stop sequences for CodeAgent)
CREDENTIALS_FILE = "moltbook_credentials.json"


def save_credentials(credentials: dict):
    """Save credentials to a JSON file."""
    credentials["saved_at"] = datetime.now().isoformat()
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(credentials, f, indent=2)
    print(f"\n✅ Credentials saved to: {CREDENTIALS_FILE}")


def load_credentials() -> dict:
    """Load credentials from file if exists."""
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, "r") as f:
            return json.load(f)
    return {}


def extract_credentials_from_response(response, agent_name: str, bio: str) -> dict:
    """Extract credentials from agent response."""
    raw = str(response.raw_response) if hasattr(response, 'raw_response') else str(response)

    credentials = {
        "name": agent_name,
        "bio": bio,
    }

    # Extract API key
    api_key_match = re.search(r'moltbook_sk_[\w-]+', raw)
    if api_key_match:
        credentials["api_key"] = api_key_match.group(0)

    # Extract claim URL
    claim_url_match = re.search(r'https://moltbook\.com/claim/[\w-]+', raw)
    if claim_url_match:
        credentials["claim_url"] = claim_url_match.group(0)

    # Extract profile URL
    profile_url_match = re.search(r'https://moltbook\.com/u/[\w-]+', raw)
    if profile_url_match:
        credentials["profile_url"] = profile_url_match.group(0)

    # Extract verification code
    verify_match = re.search(r'verification[_\s]*code[:\s]*([a-zA-Z]+-[A-Z0-9]+)', raw, re.IGNORECASE)
    if verify_match:
        credentials["verification_code"] = verify_match.group(1)

    return credentials


async def register_agent():
    """Register a new agent on Moltbook."""
    print("=" * 60)
    print("🦞 Moltbook Agent Registration")
    print("=" * 60)

    # Check if already registered
    existing = load_credentials()
    if existing.get("api_key"):
        print(f"\n📋 Found existing credentials for: {existing.get('name')}")
        print(f"   API Key: {existing.get('api_key')[:25]}...")
        print(f"   Profile: {existing.get('profile_url')}")

        use_existing = input("\nUse existing credentials? (y/n): ").strip().lower()
        if use_existing == 'y':
            set_moltbook_api_key(existing["api_key"])
            print("✅ Using existing credentials.")
            return existing
        else:
            print("📝 Proceeding with new registration...")

    # Create agent
    print(f"\n🤖 Creating agent with model: {LLM_MODEL}")
    agent = MoltbookAgent(llm=LLM_MODEL)
    await agent.setup()

    print(f"\n📝 Registering agent: {AGENT_NAME}")
    print(f"   Bio: {AGENT_BIO}")
    print("-" * 60)

    # Register on Moltbook
    response = await agent.run_async(
        f"Register me on Moltbook with name '{AGENT_NAME}' and bio '{AGENT_BIO}'"
    )

    # Print response
    answer = response.answer if hasattr(response, 'answer') else str(response)
    print("\n📬 Registration Response:")
    print(answer)

    # Extract credentials
    credentials = extract_credentials_from_response(response, AGENT_NAME, AGENT_BIO)

    if credentials.get("api_key"):
        print("\n" + "=" * 60)
        print("🔑 IMPORTANT: Your credentials")
        print("=" * 60)
        print(f"\n   API Key: {credentials['api_key']}")
        if credentials.get("claim_url"):
            print(f"   Claim URL: {credentials['claim_url']}")
        if credentials.get("profile_url"):
            print(f"   Profile: {credentials['profile_url']}")
        if credentials.get("verification_code"):
            print(f"   Verification: {credentials['verification_code']}")

        save_credentials(credentials)

        print("\n" + "-" * 60)
        print("📋 Next Steps:")
        print("   1. Share the claim_url with your human to verify ownership")
        print("   2. Set up heartbeat to keep your agent active")
        print("   3. Use the API key in your code:")
        print(f'      set_moltbook_api_key("{credentials["api_key"]}")')
        print("-" * 60)

        return credentials
    else:
        print("\n⚠️  Could not extract API key automatically.")
        print("   Check the response above for your credentials.")
        return None


async def test_with_credentials():
    """Test using saved credentials."""
    credentials = load_credentials()
    if not credentials.get("api_key"):
        print("❌ No saved credentials found. Run registration first:")
        print("   python example_register.py")
        return

    print("=" * 60)
    print(f"🧪 Testing with saved credentials: {credentials.get('name')}")
    print("=" * 60)

    # Set the API key
    set_moltbook_api_key(credentials["api_key"])

    # Create agent
    agent = MoltbookAgent(llm=LLM_MODEL)
    await agent.setup()

    # Test: Get feed
    print("\n--- 📰 Getting Feed ---")
    response = await agent.run_async("Get the latest posts from Moltbook feed")
    print(response.answer if hasattr(response, 'answer') else response)

    # Test: Search
    print("\n--- 🔍 Searching ---")
    response = await agent.run_async("Search for posts about AI")
    print(response.answer if hasattr(response, 'answer') else response)

    print("\n✅ Tests completed!")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        asyncio.run(test_with_credentials())
    else:
        asyncio.run(register_agent())
