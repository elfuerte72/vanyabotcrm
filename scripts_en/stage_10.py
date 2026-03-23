#!/usr/bin/env python3
"""Stage 10 (Upsell 2): 7-Day Personal Coaching — 129 AED.
Sent 24h after workout access.
Buttons: [7-Day Coaching — 129 AED] -> buy_now
         [No thanks, I'm good] -> upsell_decline
"""
import asyncio
import _common

asyncio.run(_common.send_stage(10))
