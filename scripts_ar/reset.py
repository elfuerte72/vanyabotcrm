#!/usr/bin/env python3
"""Reset test user to initial AR funnel state (stage 0, language=ar)."""
import asyncio
import _common

asyncio.run(_common.reset_user())
