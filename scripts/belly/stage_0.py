#!/usr/bin/env python3
"""Stage 0: Common — zone selection + morning activation link.
Buttons: [Разбудить тело] (URL) + 4 zone buttons
"""
import asyncio
import _common

asyncio.run(_common.send_stage(0))
