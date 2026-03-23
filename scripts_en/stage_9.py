#!/usr/bin/env python3
"""Stage 9 (Upsell 1): Technique check — 79 AED.
Sent after purchase.
Buttons: [Technique Check — 79 AED] -> buy_now
         [No thanks, just workout] -> upsell_decline
"""
import asyncio
import _common

asyncio.run(_common.send_stage(9))
