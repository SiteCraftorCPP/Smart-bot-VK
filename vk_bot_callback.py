import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import asyncio
import logging
from typing import Optional
from config import Config
from deepseek_client import DeepSeekClient
from flask import Flask, request, jsonify
import json
import hmac
import hashlib

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VKBotCallback:
    def __init__(self):
        self.config = Config()
        self.config.validate()
        
        # Инициализация VK API
        self.vk_session = vk_api.VkApi(token=self.config.VK_TOKEN)
        self.vk = self.vk_session.get_api()
        
        # Инициализация DeepSeek клиента
        self.deepseek = DeepSeekClient()
        
        # Секретный ключ для Callback API
        self.secret_key = "ggqwFGQG231GQQG"
        
        # Flask приложение для Callback API
        self.app = Flask(__name__)
        self.setup_routes()
        
        logger.info("Бот Callback API инициализирован успешно")
    
    def setup_routes(self):
        """Настройка маршрутов Flask"""
        
        @self.app.route('/callback', methods=['POST'])
        def callback():
            """Обработка Callback API от ВКонтакте"""
            try:
                data = request.get_json()
                logger.info(f"Получен callback: {data}")
                
                # Проверяем тип события
                if data.get('type') == 'confirmation':
                    # Подтверждение сервера
                    logger.info("Подтверждение сервера")
                    return "23895c30"  # Код подтверждения из настроек
                
                elif data.get('type') == 'message_new':
                    # Новое сообщение
                    message_data = data.get('object', {}).get('message', {})
                    user_id = message_data.get('from_id')
                    text = message_data.get('text', '')
                    
                    if user_id and text:
                        logger.info(f"Новое сообщение от {user_id}: {text}")
                        # Запускаем обработку асинхронно
                        asyncio.create_task(self.handle_message(user_id, text))
                
                return "ok"
                
            except Exception as e:
                logger.error(f"Ошибка обработки callback: {e}")
                return "error", 500
    
    def send_message(self, user_id: int, message: str):
        """
        Отправляет сообщение пользователю
        """
        try:
            # Обрезаем сообщение если оно слишком длинное
            if len(message) > self.config.MAX_MESSAGE_LENGTH:
                message = message[:self.config.MAX_MESSAGE_LENGTH-3] + "..."
            
            self.vk.messages.send(
                user_id=user_id,
                message=message,
                random_id=0
            )
            logger.info(f"Сообщение отправлено пользователю {user_id}")
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения: {e}")
    
    def is_command(self, text: str) -> bool:
        """
        Проверяет, является ли сообщение командой
        """
        return text.startswith(self.config.BOT_PREFIX)
    
    def process_command(self, text: str) -> Optional[str]:
        """
        Обрабатывает команды бота
        """
        command = text[1:].lower().strip()
        
        if command == "help" or command == "помощь":
            return """🤖 Доступные команды:
            !help - показать это сообщение
            !ping - проверить работу бота
            !status - статус API
            
            Просто напишите сообщение без префикса для общения с AI!"""
        
        elif command == "ping":
            return "🏓 Pong! Бот работает!"
        
        elif command == "status":
            deepseek_status = "✅ Работает" if self.deepseek.is_api_available() else "❌ Недоступен"
            return f"""📊 Статус сервисов:
            DeepSeek API: {deepseek_status}
            VK API: ✅ Работает"""
        
        return None
    
    async def handle_message(self, user_id: int, text: str):
        """
        Обрабатывает входящие сообщения
        """
        try:
            # Проверяем команды
            if self.is_command(text):
                response = self.process_command(text)
                if response:
                    self.send_message(user_id, response)
                    return
            
            # Если не команда, отправляем в DeepSeek
            logger.info(f"Обработка сообщения от пользователя {user_id}: {text[:50]}...")
            
            # Показываем что бот печатает
            self.vk.messages.setActivity(
                user_id=user_id,
                type='typing'
            )
            
            # Получаем ответ от DeepSeek
            response = await self.deepseek.generate_response(text, user_id)
            
            if response:
                self.send_message(user_id, response)
            else:
                self.send_message(user_id, "Извините, не удалось обработать ваш запрос.")
                
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
            self.send_message(user_id, "Произошла ошибка при обработке вашего сообщения.")
    
    def run(self, host='0.0.0.0', port=5000):
        """
        Запускает Flask сервер для Callback API
        """
        logger.info(f"Запуск Callback API сервера на {host}:{port}")
        logger.info(f"URL для настройки в ВК: http://{host}:{port}/callback")
        self.app.run(host=host, port=port, debug=False)

if __name__ == "__main__":
    bot = VKBotCallback()
    bot.run()
