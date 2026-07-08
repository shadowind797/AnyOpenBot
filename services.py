import httpx
from bs4 import BeautifulSoup

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)


async def fetch_url(url: str) -> str:
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        resp = await client.get(url, headers={"User-Agent": _USER_AGENT})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        body = soup.find("body")
        if body is None:
            raise ValueError("Не удалось найти содержимое страницы")
        return body.get_text(strip=True)


async def call_llm(text: str, proxy_url: str, model: str) -> str:
    prompt = (
        "Ты — помощник для очистки и форматирования текста статьи.\n\n"
        "Ниже дан текст веб-страницы, извлечённый из тега <body>.\n"
        "Твоя задача:\n"
        "1. Удали всё, что не является основным содержанием статьи:\n"
        "   навигацию, меню, рекламу, футер, SEO-текст, cookie-уведомления, виджеты.\n"
        "2. Немного сократи текст, но сохрани все ключевые мысли, факты, "
        "аргументы и выводы. Это не краткое содержание, а очищенная статья.\n"
        "3. Сохрани язык оригинала статьи.\n"
        "4. Отформатируй текст для Telegram (MarkdownV2):\n"
        "   - Заголовки выделяй *жирным*\n"
        "   - Важные термины выделяй _курсивом_\n"
        "   - Ссылки оформляй как [текст](URL)\n"
        "5. НЕ пиши ничего от себя — только очищенный текст статьи.\n"
        "6. Разделяй абзацы пустыми строками.\n\n"
        f"=== ТЕКСТ СТРАНИЦЫ ===\n{text}\n=== КОНЕЦ ТЕКСТА ==="
    )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
        ],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 8192,
        },
    }

    api_url = f"{proxy_url.rstrip('/')}/v1beta/models/{model}:generateContent"

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(api_url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        candidates = data.get("candidates", [])
        if not candidates:
            raise ValueError("Модель не вернула результат")
        return candidates[0]["content"]["parts"][0]["text"]
