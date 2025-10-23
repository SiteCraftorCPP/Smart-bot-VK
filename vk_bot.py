import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id
import asyncio
import logging
from typing import Optional
from config import Config
from user_manager import UserManager
from deepseek_client import DeepSeekClient
from yandex_vision_client import YandexVisionClient

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VKBot:
    def __init__(self):
        try:
            # Инициализация конфига
            self.config = Config
            self.config.validate()

            # Инициализация компонентов
            self.vk_session = vk_api.VkApi(token=self.config.VK_TOKEN)
            self.longpoll = VkBotLongPoll(self.vk_session, self.config.VK_GROUP_ID)
            self.vk = self.vk_session.get_api()
            self.user_manager = UserManager()
            self.deepseek = DeepSeekClient()
            self.vision_client = YandexVisionClient()

            logger.info("Бот инициализирован успешно")
        except ValueError as e:
            logger.error(f"Ошибка инициализации бота: {e}")
            raise

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
                try:
                    keyboard_json = keyboard.get_keyboard()
                    params['keyboard'] = keyboard_json
                    logger.info(f"Отправка с клавиатурой: {keyboard_json}")
                except Exception as e:
                    logger.error(f"Ошибка создания клавиатуры: {e}")
            
            self.vk.messages.send(**params)
            logger.info(f"Сообщение отправлено пользователю {user_id}")
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения: {e}")
    
    async def process_command(self, user_id: int, command: str):
        """
        Обрабатывает команды, введенные пользователем
        """
        logger.info(f"Обработка команды '{command}' от пользователя {user_id}")
        
        # Разделяем команду и возможные аргументы
        parts = command.split()
        main_command = parts[0]
        args = parts[1:]

        if main_command in ["help", "помощь"]:
            user_info = self.user_manager.get_user_info(user_id)
            help_text = f"""{user_info}

📋 **Основные команды:**
- `!help` или `!помощь` - это сообщение
- `!subscribe` или `!подписка` - информация о тарифах
- `!ping` - проверка работы бота
- `!reset` или `!сброс` - сбросить историю диалога

🤖 Для общения с AI просто напишите свой вопрос.
📸 Для распознавания текста отправьте изображение.
"""
            self.send_message(user_id, help_text, self.get_main_keyboard())
            
        elif main_command in ["subscribe", "подписка"]:
            sub_text = self.user_manager.get_subscription_message(user_id)
            self.send_message(user_id, sub_text, self.get_main_keyboard())

        elif main_command == "ping":
            self.send_message(user_id, "Pong! 퐁!", self.get_main_keyboard())
        
        elif main_command in ["reset", "сброс"]:
            self.user_manager.clear_history(user_id)
            self.send_message(user_id, "✅ Контекст диалога был очищен.", self.get_main_keyboard())
            
        # Секретные команды для администратора
        elif main_command == "besplatno52":
            self.user_manager.reset_user_limits(user_id)
            self.send_message(user_id, "✅ Ваши лимиты сброшены до бесплатного тарифа.", self.get_main_keyboard())
            
        elif main_command == "fofpan52":
            self.user_manager.activate_subscription(user_id, 'pro')
            self.send_message(user_id, f"✅ Подписка 'Pro' успешно активирована на 30 дней!", self.get_main_keyboard())

        elif main_command == "add_photos":
            if not args or not args[0].isdigit():
                self.send_message(user_id, "Использование: `!add_photos <количество>`")
                return
            amount = int(args[0])
            self.user_manager.add_photo_recognitions(user_id, amount)
            self.send_message(user_id, f"✅ Вам добавлено {amount} распознаваний фото.")

    def get_main_keyboard(self):
        """
        Создает главную клавиатуру
        """
        keyboard = VkKeyboard(one_time=False, inline=False)
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
            
        elif text == "🪙 Докупить токены" or text == "📸 Докупить фото": # "Докупить токены" для обратной совместимости
            message = self.user_manager.get_subscription_message(user_id, show_photo_limit_exceeded=False)
            self.send_message(user_id, message, self.get_subscription_keyboard())
            
        elif text == "🪙 Токены" or text == "📸 Фото и токены":
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
            # Обработка текстовых команд для навигации
            if "подписка" in text.lower() or "подписаться" in text.lower():
                message = """💎 **Меню подписки**

Выберите действие:

💎 **Подписка Стандарт** - 299₽/месяц
• 1,000,000 токенов в месяц
• Приоритетная поддержка
• Расширенные возможности AI

🪙 **Пакеты токенов:**
• 200,000 токенов - 99₽
• 500,000 токенов - 199₽

💳 **Для оплаты:** напишите "оплатить подписку"
📞 **Свяжитесь с нами:** https://vk.com/creativedgecpp"""
                self.send_message(user_id, message)
                
            elif "поддержка" in text.lower() or "техподдержка" in text.lower():
                message = """🛠 **Техподдержка**

По всем вопросам обращайтесь к нам:
🔗 https://vk.com/creativedgecpp

Мы поможем решить любые проблемы!"""
                self.send_message(user_id, message)
                
            elif "токены" in text.lower():
                # Показываем информацию о токенах
                user_info = self.user_manager.get_user_info(user_id)
                self.send_message(user_id, user_info)
                
            elif "оплатить подписку" in text.lower() or "купить подписку" in text.lower():
                message = """💳 **Оплата подписки**

Спасибо за интерес к подписке!

📞 **Свяжитесь с нами:**
🔗 https://vk.com/creativedgecpp

Мы поможем оформить подписку и настроить оплату."""
                self.send_message(user_id, message)
                
            elif "купить токены" in text.lower() or "докупить токены" in text.lower():
                message = """🪙 **Покупка токенов**

💰 **Доступные пакеты:**
• 200,000 токенов - 99₽
• 500,000 токенов - 199₽

📞 **Для заказа:**
🔗 https://vk.com/creativedgecpp

Укажите желаемый пакет: 200,000 или 500,000 токенов."""
                self.send_message(user_id, message)
            else:
                return False  # Не обработано
        return True  # Обработано
    
    async def handle_message(self, user_id: int, text: str, is_photo_recognition: bool = False):
        """
        Обрабатывает входящее текстовое сообщение
        """
        # Проверяем, не является ли сообщение командой
        if text.startswith(self.config.BOT_PREFIX):
            command = text[len(self.config.BOT_PREFIX):].lower().strip()
            await self.process_command(user_id, command)
            return

        # Проверяем лимит токенов перед запросом
        can_request, message = self.user_manager.check_token_limit(user_id)
        if not can_request:
            self.send_message(user_id, message)
            return

        # Получаем историю диалога
        history = self.user_manager.get_history(user_id)
        # Добавляем текущее сообщение для отправки в API
        api_call_history = history + [{"role": "user", "content": text}]

        try:
            # Отправляем "Думаю..."
            thinking_id = None
            try:
                thinking_message = self.vk.messages.send(
                    user_id=user_id,
                    message="🤔 Думаю...",
                    random_id=get_random_id()
                )
                # vk.messages.send может вернуть int (id) или dict
                if isinstance(thinking_message, int):
                    thinking_id = thinking_message
                elif isinstance(thinking_message, dict):
                    thinking_id = thinking_message.get('message_id')

                if thinking_id:
                    logger.info(f"Отправлено сообщение 'Думаю...' (id: {thinking_id}) для пользователя {user_id}")
                else:
                    logger.warning("Не удалось получить ID для сообщения 'Думаю...'.")
            except Exception as e:
                logger.error(f"Ошибка отправки сообщения 'Думаю...': {e}")
                thinking_id = None
            
            # Получаем ответ от DeepSeek
            response, tokens_used = await self.deepseek.generate_response(api_call_history)
            
            # Удаляем сообщение "Думаю..." если оно было отправлено
            if thinking_id:
                try:
                    self.vk.messages.delete(
                        message_ids=[thinking_id],
                        delete_for_all=1
                    )
                    logger.info(f"Удалено сообщение 'Думаю...' (id: {thinking_id}) для пользователя {user_id}")
                except Exception as e:
                    logger.error(f"Ошибка удаления сообщения (id: {thinking_id}): {e}")
            
            # Проверяем, был ли ответ успешным
            if tokens_used > 0:
                # Успех: сохраняем диалог в историю и тратим лимиты
                self.user_manager.increment_token_usage(user_id, tokens_used)
                self.user_manager.add_to_history(user_id, "user", text)
                self.user_manager.add_to_history(user_id, "assistant", response)

                # Если это был ответ на фото, добавляем инфо о лимитах на фото
                if is_photo_recognition:
                    user = self.user_manager.get_user(user_id)
                    plan_type = user.get('subscription_type', 'free')
                    plan_limits = self.user_manager.subscription_plans.get(plan_type, self.user_manager.subscription_plans['free'])
                    remaining = plan_limits['max_photo'] - user['photo_recognitions_used']
                    response += f"\n\n📸 **Распознаваний осталось:** {remaining} из {plan_limits['max_photo']}"
                
                self.send_message(user_id, response, self.get_main_keyboard())
            else:
                # Ошибка: показываем сообщение об ошибке, не сохраняем в историю
                self.send_message(user_id, response, self.get_main_keyboard())
                
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
                if event.type == VkBotEventType.MESSAGE_NEW:
                    message = event.message
                    logger.info(f"Новое сообщение от {message.from_id}: {message.text}")
                    
                    if message.from_id < 0 or message.from_id == -self.config.VK_GROUP_ID:
                        continue
                    
                    user_id = message.from_id
                    text = message.text or ""
                    
                    has_images = False
                    try:
                        message_info = self.vk.messages.getById(message_ids=message.id)
                        if message_info and 'items' in message_info and len(message_info['items']) > 0:
                            message_data = message_info['items'][0]
                            attachments = message_data.get('attachments', [])
                            for attachment in attachments:
                                if attachment.get('type') == 'photo':
                                    has_images = True
                                    photo_data = attachment.get('photo', {})
                                    best_url = self.get_largest_photo_url(photo_data)
                                    logger.info(f"Получено изображение от {user_id}. URL: {best_url}")
                                    asyncio.run(self.handle_image_message(user_id, best_url, text))
                                    break
                    except Exception as e:
                        logger.error(f"Ошибка получения вложений: {e}")
                    
                    if not has_images and text:
                        logger.info(f"Обрабатываем сообщение: {text}")

                        # Сначала проверяем, не является ли это нажатием кнопки или навигационной командой
                        if self.handle_button_press(user_id, text):
                            continue  # Если да, то команда обработана, переходим к следующему событию

                        # Если нет, то обрабатываем как сообщение для AI
                        try:
                            asyncio.run(self.handle_message(user_id, text))
                        except Exception as e:
                            logger.error(f"Ошибка обработки сообщения: {e}")
                            self.send_message(user_id, "Произошла ошибка при обработке сообщения.")
                else:
                    logger.info(f"Игнорируем событие типа: {event.type}")
                        
        except KeyboardInterrupt:
            logger.info("Остановка бота...")
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}")
            logger.error(f"Тип ошибки: {type(e).__name__}")
            import traceback
            logger.error(f"Трассировка: {traceback.format_exc()}")
                
    def get_largest_photo_url(self, photo_data: dict) -> str:
        """
        Находит URL самого большого изображения из данных вложения.
        """
        if not photo_data or 'sizes' not in photo_data:
            return None
        
        sizes = photo_data['sizes']
        # Сортируем по ширине, чтобы найти самую большую
        sizes.sort(key=lambda x: x.get('width', 0), reverse=True)
        
        return sizes[0].get('url') if sizes else None

    async def handle_image_message(self, user_id: int, image_url: str, user_text: str):
        """
        Обрабатывает сообщение с изображением.
        """
        if not image_url:
            self.send_message(user_id, "Не удалось получить ссылку на изображение.")
            return

        # Проверяем, может ли пользователь распознать фото
        can_recognize, message = self.user_manager.can_recognize_photo(user_id)
        if not can_recognize:
            self.send_message(user_id, message)
            return

        # Отправляем временное сообщение
        thinking_id = None
        try:
            thinking_message = self.vk.messages.send(
                user_id=user_id,
                message="🔍 Распознаю текст на изображении...",
                random_id=get_random_id()
            )
            if isinstance(thinking_message, int):
                thinking_id = thinking_message
            elif isinstance(thinking_message, dict):
                thinking_id = thinking_message.get('message_id')
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения 'Распознаю...': {e}")

        # Распознаем текст
        recognized_text = self.vision_client.recognize_text(image_url)
        
        # Удаляем временное сообщение
        if thinking_id:
            try:
                self.vk.messages.delete(message_ids=[thinking_id], delete_for_all=1)
            except Exception as e:
                logger.error(f"Ошибка удаления сообщения 'Распознаю...': {e}")

        if not recognized_text or "Ошибка" in recognized_text:
            logger.warning(f"Текст на изображении не распознан или произошла ошибка: {recognized_text}")
            self.send_message(user_id, f"Не удалось распознать текст на изображении. \n({recognized_text})")
            return
            
        # Успех! Списываем попытку распознавания.
        self.user_manager.increment_photo_usage(user_id)
        
        # Формируем новый промпт для DeepSeek, учитывая текст пользователя
        if user_text:
            new_prompt = f"Пользователь прислал изображение и написал: \"{user_text}\". На изображении распознан следующий текст: \"{recognized_text}\". Выполни инструкцию пользователя, основываясь на тексте с изображения."
        else:
            new_prompt = f"Пользователь прислал изображение. Распознанный на нем текст: \"{recognized_text}\". Проанализируй этот текст и ответь на его основе."

        # Передаем на обработку как обычное сообщение
        await self.handle_message(user_id, new_prompt, is_photo_recognition=True)

if __name__ == "__main__":
    bot = VKBot()
    bot.run()
