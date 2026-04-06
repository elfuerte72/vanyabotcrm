#!/usr/bin/env python3
"""Reset test user to initial RU funnel state (stage 0, no variant)."""
import asyncio
import _common

asyncio.run(_common.reset_user())
