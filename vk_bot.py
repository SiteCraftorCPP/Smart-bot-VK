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
import time

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

            # Анти-дублирование исходящих сообщений: user_id -> (last_text, ts)
            self._last_sent = {}

            logger.info("Бот инициализирован успешно")
        except ValueError as e:
            logger.error(f"Ошибка инициализации бота: {e}")
            raise

    def send_message(self, user_id: int, message: str, keyboard=None):
        """
        Отправляет сообщение пользователю с клавиатурой
        """
        try:
            # Анти-дублирование: если то же сообщение отправлялось <2с назад — пропускаем
            dedup_key = (user_id, (message or "").strip())
            now_ts = time.time()
            last = self._last_sent.get(user_id)
            if last and last[0] == dedup_key[1] and (now_ts - last[1]) < 2.0:
                logger.info("Пропускаем дублирующее исходящее сообщение (анти-дубль)")
                return

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
            self._last_sent[user_id] = (dedup_key[1], now_ts)
            logger.info(f"Сообщение отправлено пользователю {user_id}")
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения: {e}")
    
    async def process_command(self, user_id: int, command: str):
        """
        Обрабатывает команды, введенные пользователем
        """
        logger.info(f"Обработка команды '{command}' от пользователя {user_id}")
        
        admin_command = "adminpasdemkagg@ee11"
        main_command = command.strip()

        if main_command == admin_command:
            user = self.user_manager.get_user(user_id)
            if user.get('admin_unlimited'):
                self.send_message(user_id, "✅ У вас уже есть безлимитный доступ.", self.get_main_keyboard())
                return
            
            if self.user_manager.grant_admin_unlimited(user_id):
                self.send_message(user_id, "✅ Безлимитный доступ активирован.", self.get_main_keyboard())
            else:
                self.send_message(user_id, "❌ Не удалось активировать безлимитный доступ.", self.get_main_keyboard())
        else:
            self.send_message(user_id, "❌ Эта команда недоступна.", self.get_main_keyboard())

    def get_main_keyboard(self):
        """
        Создает главную клавиатуру
        """
        keyboard = VkKeyboard(one_time=False, inline=False)
        keyboard.add_button('🔥 Подписка', color=VkKeyboardColor.POSITIVE)
        keyboard.add_openlink_button('📞 Тех.Поддержка', 'https://vk.com/creativedgecpp')
        keyboard.add_line()
        keyboard.add_button('🪙 Токены', color=VkKeyboardColor.POSITIVE)
        keyboard.add_button('👤 Профиль', color=VkKeyboardColor.POSITIVE)
        return keyboard
    
    def get_subscription_keyboard(self):
        """
        Создает клавиатуру подписки
        """
        keyboard = VkKeyboard(one_time=False)
        keyboard.add_button('🎓 Lite - 300₽/мес', color=VkKeyboardColor.POSITIVE)
        keyboard.add_button('⚡ Больше токенов', color=VkKeyboardColor.SECONDARY)
        keyboard.add_line()
        keyboard.add_button('⭐ Premium - 449₽/мес', color=VkKeyboardColor.POSITIVE)
        keyboard.add_line()
        keyboard.add_button('↩️ Назад', color=VkKeyboardColor.PRIMARY)
        return keyboard
    
    def get_back_keyboard(self):
        """
        Создает клавиатуру "Назад"
        """
        keyboard = VkKeyboard(one_time=False)
        keyboard.add_button('↩️ Назад', color=VkKeyboardColor.PRIMARY)
        return keyboard
    
    def get_tokens_shop_keyboard(self):
        """
        Клавиатура магазина токенов/запросов
        """
        keyboard = VkKeyboard(one_time=False)
        keyboard.add_button('🪙 Купить 150.000 токенов', color=VkKeyboardColor.POSITIVE)
        keyboard.add_line()
        keyboard.add_button('🪙 Купить 30 запросов на обработку фото', color=VkKeyboardColor.SECONDARY)
        keyboard.add_line()
        keyboard.add_button('↩️ Назад', color=VkKeyboardColor.PRIMARY)
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
        if text == "🔥 Подписка":
            # Отправляем нужный текст и показываем меню подписок
            self.send_message(user_id, "👉Просто отправь свой вопрос и я отвечу на него!", self.get_subscription_keyboard())
            
            
        elif text == "🎓 Lite - 300₽/мес":
            message = """- 800.000 токенов в месяц.
- 2 запроса на обработку фото.
💳 Для оплаты нажмите: "Оплатить"."""
            self.send_message(user_id, message, self.get_subscription_keyboard())
            
        elif text == "⭐ Premium - 449₽/мес":
            message = """- 1.000.000 токенов в месяц.
- 50 запросов на обработку фото.
- Приоритетная поддержка
- Расширенные возможности AI
💳 Для оплаты нажмите: "Оплатить"."""
            self.send_message(user_id, message, self.get_subscription_keyboard())
            
        elif text == "⚡ Больше токенов" or text == "🪙 Докупить токены" or text == "📸 Докупить фото": # "Докупить токены" для обратной совместимости
            # Открываем магазин токенов
            self.send_message(user_id, "🪙 Выберите нужный пакет", self.get_tokens_shop_keyboard())
            
        elif text == "🪙 Токены" or text == "📸 Фото и токены":
            # Открываем магазин токенов
            self.send_message(user_id, "🪙 Выберите нужный пакет", self.get_tokens_shop_keyboard())
            
        elif text == "👤 Профиль":
            # Показываем статус подписки и лимиты из БД
            user_info = self.user_manager.get_user_info(user_id)
            self.send_message(user_id, user_info, self.get_main_keyboard())
            
        elif text == "↩️ Назад":
            message = "🏠 Главное меню"
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
        # Проверяем, новый ли это пользователь, и обновляем его профиль
        user_data = self.user_manager.get_user(user_id)
        if not user_data.get('full_name') or not user_data.get('profile_link'):
            self.user_manager.update_user_profile_from_vk(user_id, self.vk)

        # Проверяем, не является ли сообщение командой
        if text.startswith(self.config.BOT_PREFIX):
            command = text[len(self.config.BOT_PREFIX):].lower().strip()
            await self.process_command(user_id, command)
            return

        # Проверяем лимит перед запросом к DeepSeek
        # Для FREE проверяем количество запросов, для LITE/PREMIUM - токены
        can_request, message = self.user_manager.can_make_deepseek_request(user_id)
        if not can_request:
            self.send_message(user_id, message, self.get_main_keyboard())
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
                # Для всех тарифов тратим токены
                self.user_manager.increment_token_usage(user_id, tokens_used)
                # Для FREE увеличиваем счетчик запросов к DeepSeek
                self.user_manager.increment_deepseek_request_count(user_id)
                self.user_manager.add_to_history(user_id, "user", text)
                self.user_manager.add_to_history(user_id, "assistant", response)

                self.send_message(user_id, response, self.get_main_keyboard())
            else:
                # Ошибка: показываем сообщение об ошибке, не сохраняем в историю
                self.send_message(user_id, response, self.get_main_keyboard())
                
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
            self.send_message(user_id, "❌ Произошла ошибка при обработке вашего сообщения.", self.get_main_keyboard())
    
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
                            self.send_message(user_id, "❌ Произошла ошибка при обработке сообщения.")
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
            self.send_message(user_id, "❌ Не удалось получить ссылку на изображение.")
            return

        # Проверяем лимит запросов к Yandex Vision
        can_request, message = self.user_manager.can_make_yandex_request(user_id)
        if not can_request:
            self.send_message(user_id, message, self.get_main_keyboard())
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
        
        # Увеличиваем счетчик запросов к Yandex (для всех тарифов)
        self.user_manager.increment_yandex_request_count(user_id)
        
        # Удаляем временное сообщение
        if thinking_id:
            try:
                self.vk.messages.delete(message_ids=[thinking_id], delete_for_all=1)
            except Exception as e:
                logger.error(f"Ошибка удаления сообщения 'Распознаю...': {e}")

        if not recognized_text or "Ошибка" in recognized_text:
            logger.warning(f"Текст на изображении не распознан или произошла ошибка: {recognized_text}")
            self.send_message(user_id, f"❌ Не удалось распознать текст на изображении. \n({recognized_text})")
            return
        
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
