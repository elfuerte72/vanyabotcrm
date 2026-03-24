#!/usr/bin/env python3
"""Stage 0: Before/after photo + intro.
Photo: en_funnel_stage_0.jpg (shared with EN)
Buttons: [احصل على التمرين — 49 درهم] -> buy_now
         [التمرين فعلاً يفرق؟] -> ar_funnel_q_0
"""
import asyncio
import _common

asyncio.run(_common.send_stage(0))
