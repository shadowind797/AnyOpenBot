import re
from aiogram import Router, types
from aiogram.filters import Command

from config import PROXY_URL, MODEL_NAME
from services import fetch_url, call_llm

router = Router()
URL_RE = re.compile(r"https?://[^\s]+")


def _split_text(text: str, max_len: int = 4000) -> list[str]:
    if len(text) <= max_len:
        return [text]
    parts = []
    while text:
        if len(text) <= max_len:
            parts.append(text)
            break
        split_at = text.rfind("\n", 0, max_len)
        if split_at == -1:
            split_at = text.rfind(". ", 0, max_len)
            if split_at != -1:
                split_at += 1
            else:
                split_at = max_len
        parts.append(text[:split_at].strip())
        text = text[split_at:].strip()
    return parts


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Привет! Отправь мне ссылку на статью, "
        "и я очищу её от мусора.\n"
        "Просто вставь URL и отправь."
    )


@router.message()
async def handle_url(message: types.Message):
    if not message.text:
        return

    text = message.text.strip()
    match = URL_RE.search(text)
    if not match:
        await message.answer(
            "❌ Пожалуйста, отправьте ссылку на статью "
            "(URL должен начинаться с http:// или https://)"
        )
        return

    url = match.group(0)
    status = await message.answer("⏳ Загружаю страницу...")

    try:
        body = await fetch_url(url)
    except Exception as e:
        await status.edit_text(f"❌ Не удалось загрузить страницу: {e}")
        return

    await status.edit_text("🧠 Отправляю нейросети...")

    try:
        result = await call_llm(body, PROXY_URL, MODEL_NAME)
    except Exception as e:
        await status.edit_text(f"❌ Ошибка при обработке: {e}")
        return

    await status.delete()

    parts = _split_text(result)
    for i, part in enumerate(parts):
        text = part
        if len(parts) > 1:
            text = f"📄 Часть {i + 1}/{len(parts)}\n\n{part}"
        try:
            await message.answer(
                text,
                parse_mode="MarkdownV2",
                disable_web_page_preview=True,
            )
        except Exception:
            await message.answer(text, disable_web_page_preview=True)
