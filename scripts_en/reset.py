#!/usr/bin/env python3
"""Reset test user to initial EN funnel state (stage 0, language=en)."""
import asyncio
import _common

asyncio.run(_common.reset_user())
