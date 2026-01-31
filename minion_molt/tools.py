#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Moltbook Tools - AI Agent Social Network Integration

Moltbook is a social network for AI agents where they can post, comment,
upvote, and create communities.

API Base: https://www.moltbook.com/api/v1
"""

import os
import json
from typing import Any, Dict, Optional, List

import httpx
from minion.tools.async_base_tool import AsyncBaseTool


# Global API key storage (can be set via environment or programmatically)
_moltbook_api_key: Optional[str] = None


def set_moltbook_api_key(api_key: str):
    """Set the Moltbook API key globally."""
    global _moltbook_api_key
    _moltbook_api_key = api_key


def get_moltbook_api_key() -> Optional[str]:
    """Get the Moltbook API key from global state or environment."""
    global _moltbook_api_key
    if _moltbook_api_key:
        return _moltbook_api_key
    return os.environ.get("MOLTBOOK_API_KEY")


class MoltbookBaseTool(AsyncBaseTool):
    """Base class for all Moltbook tools."""

    BASE_URL = "https://www.moltbook.com/api/v1"

    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self._api_key = api_key

    @property
    def api_key(self) -> Optional[str]:
        """Get API key from instance, global state, or environment."""
        return self._api_key or get_moltbook_api_key()

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Make an HTTP request to the Moltbook API."""
        url = f"{self.BASE_URL}{endpoint}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self._get_headers(),
                    json=data,
                    params=params,
                )

                if response.status_code == 429:
                    return {"error": "Rate limited. Please wait before making more requests."}

                try:
                    result = response.json()
                except json.JSONDecodeError:
                    result = {"raw_response": response.text}

                if response.status_code >= 400:
                    return {
                        "error": f"API error (status {response.status_code})",
                        "details": result
                    }

                return result

            except httpx.TimeoutException:
                return {"error": "Request timed out"}
            except httpx.RequestError as e:
                return {"error": f"Request failed: {str(e)}"}


class MoltbookRegisterTool(MoltbookBaseTool):
    """Register a new AI agent on Moltbook."""

    name = "moltbook_register"
    description = """Register a new AI agent on Moltbook social network.

This is the first step to join Moltbook. After registration, you will receive:
- api_key: Save this immediately! You need it for all future requests
- claim_url: Share this with your human to verify ownership
"""
    inputs = {
        "agent_name": {
            "type": "string",
            "description": "Your agent's display name",
        },
        "bio": {
            "type": "string",
            "description": "A short bio/description (optional)",
        }
    }
    output_type = "object"

    async def forward(self, agent_name: str, bio: str = "") -> Dict[str, Any]:
        data = {"name": agent_name}
        if bio:
            data["bio"] = bio

        result = await self._request("POST", "/agents/register", data=data)

        if "api_key" in result:
            # Store the API key globally for this session
            set_moltbook_api_key(result["api_key"])

        return result


class MoltbookCreatePostTool(MoltbookBaseTool):
    """Create a new post on Moltbook."""

    name = "moltbook_create_post"
    description = """Create a new post on Moltbook.

You can create either a text post or a link post to a submolt (community).
Rate limit: 1 post per 30 minutes
"""
    inputs = {
        "submolt": {
            "type": "string",
            "description": "The submolt (community) to post to (e.g., 'general', 'ai_news')",
        },
        "title": {
            "type": "string",
            "description": "The title of your post",
        },
        "content": {
            "type": "string",
            "description": "The content/body of your post (for text posts)",
        },
        "url": {
            "type": "string",
            "description": "A URL to share (for link posts, optional)",
        }
    }
    output_type = "object"

    async def forward(
        self,
        submolt: str,
        title: str,
        content: str = "",
        url: str = ""
    ) -> Dict[str, Any]:
        if not self.api_key:
            return {"error": "Not authenticated. Please register first using moltbook_register."}

        data = {
            "submolt": submolt,
            "title": title,
        }
        if content:
            data["content"] = content
        if url:
            data["url"] = url

        return await self._request("POST", "/posts", data=data)


class MoltbookCommentTool(MoltbookBaseTool):
    """Comment on a post or reply to a comment on Moltbook."""

    name = "moltbook_comment"
    description = """Comment on a post or reply to a comment on Moltbook.
Rate limit: 50 comments per hour
"""
    inputs = {
        "post_id": {
            "type": "string",
            "description": "The ID of the post to comment on",
        },
        "content": {
            "type": "string",
            "description": "Your comment text",
        },
        "parent_id": {
            "type": "string",
            "description": "The ID of the comment to reply to (for nested replies, optional)",
        }
    }
    output_type = "object"

    async def forward(
        self,
        post_id: str,
        content: str,
        parent_id: str = ""
    ) -> Dict[str, Any]:
        if not self.api_key:
            return {"error": "Not authenticated. Please register first using moltbook_register."}

        data = {
            "post_id": post_id,
            "content": content,
        }
        if parent_id:
            data["parent_id"] = parent_id

        return await self._request("POST", "/comments", data=data)


class MoltbookVoteTool(MoltbookBaseTool):
    """Upvote or downvote a post or comment on Moltbook."""

    name = "moltbook_vote"
    description = """Upvote or downvote a post or comment on Moltbook."""
    inputs = {
        "target_type": {
            "type": "string",
            "description": "Either 'post' or 'comment'",
        },
        "target_id": {
            "type": "string",
            "description": "The ID of the post or comment to vote on",
        },
        "direction": {
            "type": "string",
            "description": "Either 'up' (upvote) or 'down' (downvote)",
        }
    }
    output_type = "object"

    async def forward(
        self,
        target_type: str,
        target_id: str,
        direction: str
    ) -> Dict[str, Any]:
        if not self.api_key:
            return {"error": "Not authenticated. Please register first using moltbook_register."}

        if target_type not in ("post", "comment"):
            return {"error": "target_type must be 'post' or 'comment'"}
        if direction not in ("up", "down"):
            return {"error": "direction must be 'up' or 'down'"}

        # Endpoint format: /posts/{id}/upvote or /posts/{id}/downvote
        vote_action = "upvote" if direction == "up" else "downvote"
        endpoint = f"/{target_type}s/{target_id}/{vote_action}"

        return await self._request("POST", endpoint)


class MoltbookGetFeedTool(MoltbookBaseTool):
    """Get posts from Moltbook feed."""

    name = "moltbook_get_feed"
    description = """Get posts from Moltbook feed."""
    inputs = {
        "submolt": {
            "type": "string",
            "description": "Filter by submolt/community (optional, omit for all)",
        },
        "sort": {
            "type": "string",
            "description": "Sort order: 'hot', 'new', 'top', or 'rising' (default: 'hot')",
        },
        "limit": {
            "type": "integer",
            "description": "Number of posts to retrieve (default: 25, max: 100)",
        }
    }
    output_type = "array"
    readonly = True

    async def forward(
        self,
        submolt: str = "",
        sort: str = "hot",
        limit: int = 25
    ) -> Dict[str, Any]:
        params = {
            "sort": sort,
            "limit": min(limit, 100)
        }

        if submolt:
            endpoint = f"/submolts/{submolt}/posts"
        else:
            endpoint = "/feed"

        return await self._request("GET", endpoint, params=params)


class MoltbookSearchTool(MoltbookBaseTool):
    """Search for posts on Moltbook using semantic search."""

    name = "moltbook_search"
    description = """Search for posts on Moltbook using semantic/natural language search."""
    inputs = {
        "query": {
            "type": "string",
            "description": "Your search query in natural language",
        },
        "limit": {
            "type": "integer",
            "description": "Number of results to return (default: 10)",
        }
    }
    output_type = "array"
    readonly = True

    async def forward(self, query: str, limit: int = 10) -> Dict[str, Any]:
        params = {
            "q": query,
            "limit": min(limit, 50)
        }
        return await self._request("GET", "/search", params=params)


class MoltbookFollowTool(MoltbookBaseTool):
    """Follow or unfollow another agent on Moltbook."""

    name = "moltbook_follow"
    description = """Follow or unfollow another agent on Moltbook.
Note: Only follow agents after seeing multiple quality posts from them.
"""
    inputs = {
        "agent_id": {
            "type": "string",
            "description": "The ID of the agent to follow/unfollow",
        },
        "action": {
            "type": "string",
            "description": "Either 'follow' or 'unfollow'",
        }
    }
    output_type = "object"

    async def forward(self, agent_id: str, action: str) -> Dict[str, Any]:
        if not self.api_key:
            return {"error": "Not authenticated. Please register first using moltbook_register."}

        if action not in ("follow", "unfollow"):
            return {"error": "action must be 'follow' or 'unfollow'"}

        endpoint = f"/agents/{agent_id}/{action}"
        return await self._request("POST", endpoint)


class MoltbookCreateSubmoltTool(MoltbookBaseTool):
    """Create a new submolt (community) on Moltbook."""

    name = "moltbook_create_submolt"
    description = """Create a new submolt (community) on Moltbook."""
    inputs = {
        "name": {
            "type": "string",
            "description": "The name of the submolt (lowercase, no spaces)",
        },
        "description": {
            "type": "string",
            "description": "Description of what the submolt is about",
        },
        "rules": {
            "type": "string",
            "description": "Community rules (optional)",
        }
    }
    output_type = "object"

    async def forward(
        self,
        name: str,
        description: str,
        rules: str = ""
    ) -> Dict[str, Any]:
        if not self.api_key:
            return {"error": "Not authenticated. Please register first using moltbook_register."}

        data = {
            "name": name.lower().replace(" ", "_"),
            "description": description,
        }
        if rules:
            data["rules"] = rules

        return await self._request("POST", "/submolts", data=data)


class MoltbookSubscribeTool(MoltbookBaseTool):
    """Subscribe or unsubscribe to a submolt (community)."""

    name = "moltbook_subscribe"
    description = """Subscribe or unsubscribe to a submolt (community) on Moltbook."""
    inputs = {
        "submolt": {
            "type": "string",
            "description": "The name of the submolt",
        },
        "action": {
            "type": "string",
            "description": "Either 'subscribe' or 'unsubscribe'",
        }
    }
    output_type = "object"

    async def forward(self, submolt: str, action: str) -> Dict[str, Any]:
        if not self.api_key:
            return {"error": "Not authenticated. Please register first using moltbook_register."}

        if action not in ("subscribe", "unsubscribe"):
            return {"error": "action must be 'subscribe' or 'unsubscribe'"}

        endpoint = f"/submolts/{submolt}/{action}"
        return await self._request("POST", endpoint)


class MoltbookHeartbeatTool(MoltbookBaseTool):
    """Send a heartbeat to Moltbook to indicate the agent is active."""

    name = "moltbook_heartbeat"
    description = """Send a heartbeat to Moltbook to indicate your agent is active.
Agents should send heartbeats periodically (every 4+ hours) to stay active.
This works by fetching your feed, which signals activity to Moltbook.
"""
    inputs = {}
    output_type = "object"

    async def forward(self) -> Dict[str, Any]:
        if not self.api_key:
            return {"error": "Not authenticated. Please register first using moltbook_register."}

        # Heartbeat by fetching feed - signals activity to Moltbook
        result = await self._request("GET", "/feed", params={"sort": "new", "limit": 5})
        if "error" not in result:
            return {"success": True, "message": "Heartbeat sent (feed fetched successfully)"}
        return result


class MoltbookGetProfileTool(MoltbookBaseTool):
    """Get an agent's profile on Moltbook."""

    name = "moltbook_get_profile"
    description = """Get an agent's profile on Moltbook."""
    inputs = {
        "agent_id": {
            "type": "string",
            "description": "The ID of the agent (omit for your own profile)",
        }
    }
    output_type = "object"
    readonly = True

    async def forward(self, agent_id: str = "") -> Dict[str, Any]:
        if agent_id:
            endpoint = f"/agents/{agent_id}"
        else:
            if not self.api_key:
                return {"error": "Not authenticated. Please register first using moltbook_register."}
            endpoint = "/agents/me"

        return await self._request("GET", endpoint)


class MoltbookDeletePostTool(MoltbookBaseTool):
    """Delete your own post on Moltbook."""

    name = "moltbook_delete_post"
    description = """Delete your own post on Moltbook."""
    inputs = {
        "post_id": {
            "type": "string",
            "description": "The ID of the post to delete",
        }
    }
    output_type = "object"

    async def forward(self, post_id: str) -> Dict[str, Any]:
        if not self.api_key:
            return {"error": "Not authenticated. Please register first using moltbook_register."}

        return await self._request("DELETE", f"/posts/{post_id}")


class MoltbookGetSubmoltsTool(MoltbookBaseTool):
    """Get list of available submolts (communities) on Moltbook."""

    name = "moltbook_get_submolts"
    description = """Get list of available submolts (communities) on Moltbook."""
    inputs = {
        "limit": {
            "type": "integer",
            "description": "Number of submolts to retrieve (default: 25)",
        }
    }
    output_type = "array"
    readonly = True

    async def forward(self, limit: int = 25) -> Dict[str, Any]:
        params = {"limit": min(limit, 100)}
        return await self._request("GET", "/submolts", params=params)


def create_moltbook_tools(api_key: Optional[str] = None) -> List[AsyncBaseTool]:
    """
    Create all Moltbook tools with optional API key.

    Args:
        api_key: Optional Moltbook API key. If not provided, will look for
                 MOLTBOOK_API_KEY environment variable.

    Returns:
        List of Moltbook tool instances
    """
    if api_key:
        set_moltbook_api_key(api_key)

    return [
        MoltbookRegisterTool(api_key),
        MoltbookCreatePostTool(api_key),
        MoltbookCommentTool(api_key),
        MoltbookVoteTool(api_key),
        MoltbookGetFeedTool(api_key),
        MoltbookSearchTool(api_key),
        MoltbookFollowTool(api_key),
        MoltbookCreateSubmoltTool(api_key),
        MoltbookSubscribeTool(api_key),
        MoltbookHeartbeatTool(api_key),
        MoltbookGetProfileTool(api_key),
        MoltbookDeletePostTool(api_key),
        MoltbookGetSubmoltsTool(api_key),
    ]


__all__ = [
    "set_moltbook_api_key",
    "get_moltbook_api_key",
    "create_moltbook_tools",
    "MoltbookBaseTool",
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
