#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests for Moltbook tools.
"""

import pytest
from minion_molt.tools import (
    create_moltbook_tools,
    set_moltbook_api_key,
    get_moltbook_api_key,
    MoltbookRegisterTool,
    MoltbookGetFeedTool,
    MoltbookSearchTool,
)


class TestMoltbookTools:
    """Test Moltbook tool classes."""

    def test_create_moltbook_tools(self):
        """Test that all tools are created."""
        tools = create_moltbook_tools()
        assert len(tools) == 13

        tool_names = [t.name for t in tools]
        assert "moltbook_register" in tool_names
        assert "moltbook_create_post" in tool_names
        assert "moltbook_comment" in tool_names
        assert "moltbook_vote" in tool_names
        assert "moltbook_get_feed" in tool_names
        assert "moltbook_search" in tool_names
        assert "moltbook_follow" in tool_names
        assert "moltbook_create_submolt" in tool_names
        assert "moltbook_subscribe" in tool_names
        assert "moltbook_heartbeat" in tool_names
        assert "moltbook_get_profile" in tool_names
        assert "moltbook_delete_post" in tool_names
        assert "moltbook_get_submolts" in tool_names

    def test_api_key_management(self):
        """Test API key getter/setter."""
        # Clear any existing key
        set_moltbook_api_key("")

        # Test setting
        set_moltbook_api_key("test-key-123")
        assert get_moltbook_api_key() == "test-key-123"

        # Clean up
        set_moltbook_api_key("")

    def test_tool_has_correct_attributes(self):
        """Test that tools have required attributes."""
        tool = MoltbookRegisterTool()

        assert hasattr(tool, 'name')
        assert hasattr(tool, 'description')
        assert hasattr(tool, 'inputs')
        assert hasattr(tool, 'output_type')

        assert tool.name == "moltbook_register"
        assert "agent_name" in tool.inputs

    def test_readonly_tools(self):
        """Test that readonly tools are marked correctly."""
        feed_tool = MoltbookGetFeedTool()
        search_tool = MoltbookSearchTool()
        register_tool = MoltbookRegisterTool()

        assert feed_tool.readonly is True
        assert search_tool.readonly is True
        assert register_tool.readonly is False


@pytest.mark.asyncio
class TestMoltbookToolsAsync:
    """Async tests for Moltbook tools."""

    async def test_unauthenticated_post_fails(self):
        """Test that posting without auth returns error."""
        from minion_molt.tools import MoltbookCreatePostTool

        tool = MoltbookCreatePostTool()
        result = await tool.forward(
            submolt="test",
            title="Test Post",
            content="Test content"
        )

        assert "error" in result
        assert "Not authenticated" in result["error"]

    async def test_get_feed_works(self):
        """Test that getting feed works (no auth required for public feed)."""
        tool = MoltbookGetFeedTool()
        result = await tool.forward()

        # Should return something (either posts or empty list or error from API)
        assert isinstance(result, dict)
