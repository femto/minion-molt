"""
Minion-Molt: Minion agent integration with Moltbook social network.

Moltbook is the social network for AI agents where they can post,
comment, upvote, and create communities.
"""

from minion_molt.tools import (
    create_moltbook_tools,
    set_moltbook_api_key,
    get_moltbook_api_key,
    MoltbookRegisterTool,
    MoltbookCreatePostTool,
    MoltbookCommentTool,
    MoltbookVoteTool,
    MoltbookGetFeedTool,
    MoltbookSearchTool,
    MoltbookFollowTool,
    MoltbookCreateSubmoltTool,
    MoltbookSubscribeTool,
    MoltbookHeartbeatTool,
    MoltbookGetProfileTool,
    MoltbookDeletePostTool,
    MoltbookGetSubmoltsTool,
)

from minion_molt.agent import MoltbookAgent

__version__ = "0.1.0"

__all__ = [
    # Agent
    "MoltbookAgent",
    # Tools
    "create_moltbook_tools",
    "set_moltbook_api_key",
    "get_moltbook_api_key",
    "MoltbookRegisterTool",
    "MoltbookCreatePostTool",
    "MoltbookCommentTool",
    "MoltbookVoteTool",
    "MoltbookGetFeedTool",
    "MoltbookSearchTool",
    "MoltbookFollowTool",
    "MoltbookCreateSubmoltTool",
    "MoltbookSubscribeTool",
    "MoltbookHeartbeatTool",
    "MoltbookGetProfileTool",
    "MoltbookDeletePostTool",
    "MoltbookGetSubmoltsTool",
]
