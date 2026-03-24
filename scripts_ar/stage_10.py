#!/usr/bin/env python3
"""Stage 10 (Upsell 2): 7-Day Personal Coaching — 129 AED.
Sent 24h after workout access.
Buttons: [تدريب 7 أيام — 129 درهم] -> buy_now
         [لا شكراً، كذا تمام] -> upsell_decline
"""
import asyncio
import _common

asyncio.run(_common.send_stage(10))
