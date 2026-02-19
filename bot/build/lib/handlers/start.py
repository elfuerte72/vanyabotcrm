"""Handler for /start command."""

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        "<b>RU:</b>\nПривет! Я помогу тебе рассчитать КБЖУ и составить план питания. "
        "Просто напиши мне!\n\n"
        "<b>EN:</b>\nHi! I'll help you calculate your macros and create a nutrition plan. "
        "Just write to me!\n\n"
        "<b>AR:</b>\nمرحباً! سأساعدك في حساب الماكروز وإنشاء خطة تغذية. "
        "فقط اكتب لي!",
        parse_mode="HTML",
    )
