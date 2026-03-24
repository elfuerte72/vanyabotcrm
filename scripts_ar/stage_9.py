#!/usr/bin/env python3
"""Stage 9 (Upsell 1): Technique Check — 79 AED.
Sent after workout purchase.
Buttons: [فحص التكنيك — 79 درهم] -> buy_now
         [لا شكراً، التمرين بس] -> upsell_decline
"""
import asyncio
import _common

asyncio.run(_common.send_stage(9))
