import requests
import json
from typing import Optional, Dict, Any
from config import Config

class DeepSeekClient:
    def __init__(self):
        self.api_key = Config.DEEPSEEK_API_KEY
        self.base_url = Config.DEEPSEEK_BASE_URL
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    async def generate_response(self, message: str, user_id: int = None) -> tuple[Optional[str], int]:
        """
        Генерирует ответ от DeepSeek API
        Возвращает (ответ, количество_использованных_токенов)
        """
        try:
            # Формируем промпт с контекстом
            system_prompt = """Ты полезный AI-ассистент в ВКонтакте. 
            Отвечай кратко, дружелюбно и по делу. 
            Если вопрос неясен, уточни что именно нужно."""
            
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                "max_tokens": 1000,
                "temperature": 0.7
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data['choices'][0]['message']['content']
                
                # Получаем информацию об использованных токенах
                usage = data.get('usage', {})
                total_tokens = usage.get('total_tokens', 0)
                
                return content, total_tokens
            else:
                print(f"Ошибка DeepSeek API: {response.status_code} - {response.text}")
                return "Извините, произошла ошибка при обработке запроса.", 0
                
        except requests.exceptions.Timeout:
            return "Извините, запрос занял слишком много времени.", 0
        except requests.exceptions.RequestException as e:
            print(f"Ошибка запроса к DeepSeek: {e}")
            return "Извините, произошла ошибка соединения.", 0
        except Exception as e:
            print(f"Неожиданная ошибка: {e}")
            return "Извините, произошла неожиданная ошибка.", 0
    
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
