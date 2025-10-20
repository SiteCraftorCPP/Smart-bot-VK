import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id
import asyncio
import logging
from typing import Optional
from config import Config
from deepseek_client import DeepSeekClient
from user_manager import UserManager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VKBot:
    def __init__(self):
        self.config = Config()
        self.config.validate()
        
        # Инициализация VK API
        self.vk_session = vk_api.VkApi(token=self.config.VK_TOKEN)
        self.vk = self.vk_session.get_api()
        
        # Инициализация DeepSeek клиента
        self.deepseek = DeepSeekClient()
        
        # Инициализация менеджера пользователей
        self.user_manager = UserManager()
        
        # Инициализация Long Poll
        self.longpoll = VkBotLongPoll(self.vk_session, self.config.VK_GROUP_ID)
        
        logger.info("Бот инициализирован успешно")
    
    def send_message(self, user_id: int, message: str, keyboard=None):
        """
        Отправляет сообщение пользователю с клавиатурой
        """
        try:
            # Обрезаем сообщение если оно слишком длинное
            if len(message) > self.config.MAX_MESSAGE_LENGTH:
                message = message[:self.config.MAX_MESSAGE_LENGTH-3] + "..."
            
            params = {
                'user_id': user_id,
                'message': message,
                'random_id': get_random_id()
            }
            
            if keyboard:
                params['keyboard'] = keyboard.get_keyboard()
            
            self.vk.messages.send(**params)
            logger.info(f"Сообщение отправлено пользователю {user_id}")
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения: {e}")
    
    def get_main_keyboard(self):
        """
        Создает главную клавиатуру
        """
        keyboard = VkKeyboard(one_time=False)
        keyboard.add_button('📋 Подписка', color=VkKeyboardColor.PRIMARY)
        keyboard.add_button('🛠 Техподдержка', color=VkKeyboardColor.SECONDARY)
        keyboard.add_line()
        keyboard.add_button('🪙 Токены', color=VkKeyboardColor.POSITIVE)
        keyboard.add_button('❓ Помощь', color=VkKeyboardColor.POSITIVE)
        return keyboard
    
    def get_subscription_keyboard(self):
        """
        Создает клавиатуру подписки
        """
        keyboard = VkKeyboard(one_time=False)
        keyboard.add_button('💎 Подписка Стандарт', color=VkKeyboardColor.PRIMARY)
        keyboard.add_button('🪙 Докупить токены', color=VkKeyboardColor.POSITIVE)
        keyboard.add_line()
        keyboard.add_button('🔙 Назад', color=VkKeyboardColor.NEGATIVE)
        return keyboard
    
    def get_back_keyboard(self):
        """
        Создает клавиатуру "Назад"
        """
        keyboard = VkKeyboard(one_time=False)
        keyboard.add_button('🔙 Назад', color=VkKeyboardColor.NEGATIVE)
        return keyboard
    
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
            !tokens - показать информацию о токенах
            
            Просто напишите сообщение без префикса для общения с AI!"""
        
        elif command == "ping":
            return "🏓 Pong! Бот работает!"
        
        elif command == "status":
            deepseek_status = "✅ Работает" if self.deepseek.is_api_available() else "❌ Недоступен"
            return f"""📊 Статус сервисов:
            DeepSeek API: {deepseek_status}
            VK API: ✅ Работает"""
        
        elif command == "tokens" or command == "токены":
            # Показываем информацию о токенах пользователя
            user_info = self.user_manager.get_user_info(user_id)
            return user_info
        
        return None
    
    def handle_button_press(self, user_id: int, text: str):
        """
        Обрабатывает нажатия кнопок
        """
        if text == "📋 Подписка":
            message = """💎 **Меню подписки**

Выберите действие:"""
            self.send_message(user_id, message, self.get_subscription_keyboard())
            
        elif text == "🛠 Техподдержка":
            message = """🛠 **Техподдержка**

По всем вопросам обращайтесь к нам:
🔗 https://vk.com/creativedgecpp

Мы поможем решить любые проблемы!"""
            self.send_message(user_id, message, self.get_back_keyboard())
            
        elif text == "💎 Подписка Стандарт":
            message = """💎 **Подписка Стандарт**

💰 **Стоимость:** 299₽/месяц

✅ **Включено:**
• 1,000,000 токенов в месяц
• Приоритетная поддержка
• Расширенные возможности AI
• Безлимитные команды

💳 **Для оплаты напишите:** "Оплатить подписку"
Мы свяжемся с вами для оформления платежа."""
            self.send_message(user_id, message, self.get_subscription_keyboard())
            
        elif text == "🪙 Докупить токены":
            message = """🪙 **Покупка токенов**

💰 **Доступные пакеты:**
• 200,000 токенов - 99₽
• 500,000 токенов - 199₽

💳 **Для покупки напишите:** "Купить токены"
Укажите желаемый пакет: 200,000 или 500,000 токенов."""
            self.send_message(user_id, message, self.get_subscription_keyboard())
            
        elif text == "🪙 Токены":
            # Показываем информацию о токенах
            user_info = self.user_manager.get_user_info(user_id)
            self.send_message(user_id, user_info, self.get_main_keyboard())
            
        elif text == "❓ Помощь":
            # Добавляем информацию о пользователе
            user_info = self.user_manager.get_user_info(user_id)
            message = f"""❓ **Помощь**

{user_info}

🤖 **Основные функции:**
• Общение с AI (просто напишите сообщение)
• Команды: !ping, !help, !status, !tokens
• Подписка и покупка токенов

📋 **Кнопки:**
• **Подписка** - оформить подписку или купить токены
• **Техподдержка** - связаться с нами
• **Токены** - показать информацию о токенах
• **Помощь** - эта справка

💡 **Совет:** Используйте кнопки для удобной навигации!"""
            self.send_message(user_id, message, self.get_main_keyboard())
            
        elif text == "🔙 Назад":
            message = """🏠 **Главное меню**

Выберите действие:"""
            self.send_message(user_id, message, self.get_main_keyboard())
            
        else:
            # Обработка текстовых команд для покупки
            if "оплатить подписку" in text.lower() or "купить подписку" in text.lower():
                message = """💳 **Оплата подписки**

Спасибо за интерес к подписке!

📞 **Свяжитесь с нами:**
🔗 https://vk.com/creativedgecpp

Мы поможем оформить подписку и настроить оплату."""
                self.send_message(user_id, message, self.get_back_keyboard())
                
            elif "купить токены" in text.lower() or "докупить токены" in text.lower():
                message = """🪙 **Покупка токенов**

💰 **Доступные пакеты:**
• 200,000 токенов - 99₽
• 500,000 токенов - 199₽

📞 **Для заказа:**
🔗 https://vk.com/creativedgecpp

Укажите желаемый пакет: 200,000 или 500,000 токенов."""
                self.send_message(user_id, message, self.get_back_keyboard())
            else:
                return False  # Не обработано
        return True  # Обработано
    
    async def handle_message(self, user_id: int, text: str):
        """
        Обрабатывает входящие сообщения
        """
        try:
            # Проверяем нажатия кнопок
            if self.handle_button_press(user_id, text):
                return
            
            # Проверяем команды
            if self.is_command(text):
                response = self.process_command(text)
                if response:
                    self.send_message(user_id, response, self.get_main_keyboard())
                    return
            
            # Проверяем лимиты для AI запросов
            can_request, limit_message = self.user_manager.can_make_request(user_id)
            
            if not can_request:
                # Лимит исчерпан, показываем сообщение о подписке
                subscription_message = self.user_manager.get_subscription_message(user_id)
                self.send_message(user_id, subscription_message, self.get_subscription_keyboard())
                return
            
            # Если не команда и не кнопка, отправляем в DeepSeek
            logger.info(f"Обработка сообщения от пользователя {user_id}: {text[:50]}...")
            logger.info(f"Лимит: {limit_message}")
            
            # Показываем что бот печатает
            self.vk.messages.setActivity(
                user_id=user_id,
                type='typing'
            )
            
            # Получаем ответ от DeepSeek
            response, tokens_used = await self.deepseek.generate_response(text, user_id)
            
            if response:
                # Увеличиваем счетчик пробных запросов
                self.user_manager.increment_trial_request(user_id)
                
                # Если у пользователя есть подписка, тратим токены
                user = self.user_manager.get_user(user_id)
                if user['subscription_active']:
                    # Тратим токены (входящие + исходящие)
                    self.user_manager.consume_tokens(user_id, tokens_used)
                    
                    # Обновляем информацию о пользователе
                    user = self.user_manager.get_user(user_id)
                    
                    # Вычисляем потраченные токены за все время
                    total_given = 1000000
                    tokens_spent_total = total_given - user['tokens_remaining']
                    
                    response += f"\n\n🪙 **Токенов использовано в этом запросе:** {tokens_used:,}"
                    response += f"\n🪙 **Токенов потрачено всего:** {tokens_spent_total:,}"
                    response += f"\n🪙 **Токенов осталось:** {user['tokens_remaining']:,}"
                else:
                    # Для пробных пользователей показываем лимит
                    remaining = user['max_trial_requests'] - user['trial_requests']
                    response += f"\n\n🆓 **Пробных запросов осталось:** {remaining}"
                
                self.send_message(user_id, response, self.get_main_keyboard())
            else:
                self.send_message(user_id, "Извините, не удалось обработать ваш запрос.", self.get_main_keyboard())
                
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
            self.send_message(user_id, "Произошла ошибка при обработке вашего сообщения.", self.get_main_keyboard())
    
    def run(self):
        """
        Запускает бота
        """
        logger.info("Запуск бота...")
        logger.info(f"ID группы: {self.config.VK_GROUP_ID}")
        logger.info("Ожидание сообщений...")
        
        try:
            for event in self.longpoll.listen():
                logger.info(f"Получено событие: {event.type}")
                
                if event.type == VkBotEventType.MESSAGE_NEW:
                    message = event.message
                    logger.info(f"Новое сообщение от {message.from_id}: {message.text}")
                    
                    # Игнорируем исходящие сообщения
                    if message.from_id < 0:
                        logger.info("Игнорируем исходящее сообщение")
                        continue
                    
                    # Игнорируем сообщения от самого бота
                    if message.from_id == -self.config.VK_GROUP_ID:
                        logger.info("Игнорируем сообщение от бота")
                        continue
                    
                    user_id = message.from_id
                    text = message.text
                    
                    if text:
                        logger.info(f"Обрабатываем сообщение: {text}")
                        # Запускаем обработку синхронно
                        asyncio.run(self.handle_message(user_id, text))
                else:
                    logger.info(f"Игнорируем событие типа: {event.type}")
                        
        except KeyboardInterrupt:
            logger.info("Остановка бота...")
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}")
            logger.error(f"Тип ошибки: {type(e).__name__}")
            import traceback
            logger.error(f"Трассировка: {traceback.format_exc()}")

if __name__ == "__main__":
    bot = VKBot()
    bot.run()
