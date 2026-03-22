#!/usr/bin/env python3
"""День 0, Stage 1: Фото до/после + тизер тренировки (+2.5ч).
Фото: before_after_1.jpg
Кнопка: [Узнать про тренировку] -> callback: learn_workout
"""
import asyncio
import _common

asyncio.run(_common.send_stage(1))
