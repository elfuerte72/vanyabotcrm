#!/usr/bin/env python3
"""Сбросить тестового пользователя в начальное состояние."""
import asyncio
import _common

asyncio.run(_common.reset_user())
