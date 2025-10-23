import requests
import json
from typing import Optional, Dict, Any
from config import Config
import aiohttp
import asyncio
import logging

logger = logging.getLogger(__name__)

class DeepSeekClient:
    def __init__(self):
        self.api_key = Config.DEEPSEEK_API_KEY
        self.base_url = Config.DEEPSEEK_BASE_URL
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    async def generate_response(self, messages: list) -> (str, int):
        """
        Генерирует ответ от DeepSeek на основе истории сообщений.
        Возвращает ответ и количество использованных токенов.
        """
        if not self.api_key:
            return "Нет ключа DeepSeek API", 0

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        # Формируем промпт с контекстом
        system_prompt = "Ты — полезный ИИ-ассистент в боте для ВКонтакте. Твои ответы должны быть только в формате простого текста. Не используй Markdown, LaTeX или любые другие виды форматирования. Для математических формул и символов используй символы Unicode (например, Δ, Ω, ≈, →, α) вместо команд LaTeX (например, \\Delta, \\Omega, \\approx, \\rightarrow, \\alpha). Ответы давай на русском языке. Всегда уделяй первостепенное внимание последнему сообщению от пользователя. Если оно представляет собой новый вопрос или тему, отвечай на него, даже если это противоречит предыдущему контексту."
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                *messages
            ],
            "stream": False
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post("https://api.deepseek.com/chat/completions", headers=headers, json=payload, timeout=45) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data['choices'][0]['message']['content']
                        tokens_used = data['usage']['total_tokens']
                        return content.strip(), tokens_used
                    elif response.status == 402:
                         return "Ошибка: Недостаточно средств на балансе DeepSeek.", 0
                    else:
                        error_text = await response.text()
                        logger.error(f"Ошибка API DeepSeek: {response.status} - {error_text}")
                        return f"Ошибка API DeepSeek: {response.status}", 0
        except aiohttp.ClientConnectorError:
            logger.error("Ошибка соединения с DeepSeek API.")
            return "Ошибка соединения. Серверы DeepSeek могут быть недоступны.", 0
        except asyncio.TimeoutError:
            logger.error("Тайм-аут при запросе к DeepSeek API.")
            return "Сервер DeepSeek слишком долго отвечает. Попробуйте позже.", 0
        except Exception as e:
            logger.error(f"Неизвестная ошибка при работе с DeepSeek: {e}")
            return "Произошла неизвестная ошибка при обращении к AI.", 0
    
    def is_api_available(self) -> bool:
        """
        Проверяет доступность DeepSeek API
        """
        try:
            response = requests.get(
                f"{self.base_url}/models",
                headers=self.headers,
                timeout=10
            )
            return response.status_code == 200
        except:
            return False
