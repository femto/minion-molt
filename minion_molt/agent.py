#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MoltbookAgent - A Minion agent specialized for Moltbook social network.
"""

from dataclasses import dataclass
from typing import Optional

from minion.agents.code_agent import CodeAgent
from minion_molt.tools import create_moltbook_tools, set_moltbook_api_key


MOLTBOOK_SYSTEM_PROMPT = """You are a helpful assistant that can interact with Moltbook, a social platform for AI agents.

You have tools to:
- Register on Moltbook
- Browse and search posts
- Create posts and comments
- Vote on content
- Follow other agents
- Join communities (submolts)

Please use the appropriate tools to help with user requests.
"""


@dataclass
class MoltbookAgent(CodeAgent):
    """
    A Minion agent specialized for Moltbook social network.

    This agent comes pre-configured with all Moltbook tools and
    a system prompt optimized for social interaction. Uses CodeAgent
    for code-based reasoning and tool execution.

    Example:
        ```python
        agent = MoltbookAgent(llm="gpt-4.1")
        await agent.setup()

        # Register and start interacting
        response = await agent.run_async("Register me on Moltbook as 'MyAIBot'")
        print(response.answer)

        # Browse and engage
        response = await agent.run_async("Search for posts about AI agents")
        print(response.answer)
        ```
    """

    name: str = "MoltbookAgent"
    api_key: Optional[str] = None

    def __post_init__(self):
        """Initialize with Moltbook tools and system prompt."""
        # Set API key if provided
        if self.api_key:
            set_moltbook_api_key(self.api_key)

        # Add Moltbook tools
        moltbook_tools = create_moltbook_tools(self.api_key)
        if self.tools is None:
            self.tools = moltbook_tools
        else:
            self.tools = list(self.tools) + moltbook_tools

        # Set system prompt if not already set
        if not self.system_prompt:
            self.system_prompt = MOLTBOOK_SYSTEM_PROMPT

        # Call parent post_init
        super().__post_init__()


def create_moltbook_agent(
    llm: str = "gpt-4.1",
    api_key: Optional[str] = None,
    **kwargs
) -> MoltbookAgent:
    """
    Create a MoltbookAgent with the specified configuration.

    Args:
        llm: The LLM model to use (default: gpt-4.1)
        api_key: Optional Moltbook API key
        **kwargs: Additional arguments passed to MoltbookAgent

    Returns:
        Configured MoltbookAgent instance
    """
    return MoltbookAgent(
        llm=llm,
        api_key=api_key,
        **kwargs
    )


__all__ = ["MoltbookAgent", "create_moltbook_agent", "MOLTBOOK_SYSTEM_PROMPT"]
