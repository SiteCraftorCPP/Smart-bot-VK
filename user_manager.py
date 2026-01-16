import json
import os
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
from config import Config
from db_manager import db_manager # Импортируем наш новый менеджер БД
import logging

logger = logging.getLogger(__name__)

class UserManager:
    def __init__(self):
        # Теперь self.users - это кеш, а не основное хранилище
        self.users_cache = {}
        self.subscription_plans = self._load_subscription_plans()

    def _load_subscription_plans(self):
        """Загружает тарифы из базы данных при старте."""
        plans = db_manager.get_subscription_plans()
        if not plans:
            logger.error("Не удалось загрузить тарифные планы из БД! Используются значения по умолчанию.")
            # Возвращаем запасной вариант, если БД недоступна
            return {
               'free': {'max_tokens': None, 'deepseek_max_requests': 5, 'yandex_max_requests': 2, 'price': 0},
               'lite': {'max_tokens': 250000, 'deepseek_max_requests': None, 'yandex_max_requests': 10, 'price': 149},
               'premium': {'max_tokens': 1000000, 'deepseek_max_requests': None, 'yandex_max_requests': 50, 'price': 299}
            }
        logger.info("Тарифные планы успешно загружены из БД.")
        return plans

    def get_user(self, user_id: int) -> Dict:
        """
        Получает пользователя. Сначала ищет в кеше, если нет - в БД.
        Если нет в БД, создает нового.
        """
        user_id_str = str(user_id)
        if user_id_str in self.users_cache:
            return self.users_cache[user_id_str]

        user_data = db_manager.get_user(user_id)
        
        if not user_data:
            user_data = db_manager.create_user(user_id)

        # Конвертируем datetime объекты в строки для совместимости
        for key, value in user_data.items():
            if isinstance(value, datetime):
                user_data[key] = value.isoformat()
        
        # Гарантируем наличие флага безлимита
        if 'admin_unlimited' not in user_data:
            user_data['admin_unlimited'] = False
        
        # Добавляем в кеш
        self.users_cache[user_id_str] = user_data
        return user_data

    def update_user_profile_from_vk(self, user_id: int, vk_api):
        """
        Получает информацию о пользователе из VK API и сохраняет в БД.
        Вызывается при первом контакте с ботом.
        """
        try:
            # Получаем информацию о пользователе из VK
            user_info = vk_api.users.get(user_ids=user_id, fields='first_name,last_name,phone')[0]
            
            first_name = user_info.get('first_name', '')
            last_name = user_info.get('last_name', '')
            full_name = f"{first_name} {last_name}".strip()
            profile_link = f"https://vk.com/id{user_id}"
            phone_number = user_info.get('phone')
            
            # Сохраняем в БД
            if db_manager.update_user_profile(user_id, full_name=full_name, profile_link=profile_link, phone_number=phone_number):
                # Обновляем кеш
                if str(user_id) in self.users_cache:
                    self.users_cache[str(user_id)]['full_name'] = full_name
                    self.users_cache[str(user_id)]['profile_link'] = profile_link
                    if phone_number:
                        self.users_cache[str(user_id)]['phone_number'] = phone_number
                logger.info(f"Профиль пользователя {user_id} обновлен: {full_name}")
                return True
        except Exception as e:
            logger.error(f"Ошибка получения профиля пользователя {user_id} из VK: {e}")
        return False

    # Методы для работы с историей пока оставляем без изменений,
    # так как хранить историю в БД для каждого сообщения - избыточно.
    # Это лучше делать в кеше (как сейчас) или в Redis.
    def get_history(self, user_id: int) -> list:
        user = self.get_user(user_id)
        # Убедимся, что поле есть, даже если пользователь только что создан
        if 'conversation_history' not in user:
            user['conversation_history'] = []
        return user['conversation_history']

    def add_to_history(self, user_id: int, role: str, content: str):
        user = self.get_user(user_id)
        history = self.get_history(user_id)
        
        history.append({"role": role, "content": content})
        
        if len(history) > Config.MAX_HISTORY_MESSAGES:
            history = history[-Config.MAX_HISTORY_MESSAGES:]
            
        user['conversation_history'] = history
        # Нет необходимости сохранять в БД каждое сообщение

    def clear_history(self, user_id: int):
        user = self.get_user(user_id)
        user['conversation_history'] = []

    def can_make_deepseek_request(self, user_id: int) -> Tuple[bool, str]:
        """Проверяет, может ли пользователь сделать запрос к DeepSeek API"""
        user = self.get_user(user_id)
        plan_type = user.get('subscription_type', 'free')
        
        expires_str = user.get('subscription_end')
        if expires_str:
            try:
                if datetime.fromisoformat(expires_str) < datetime.now():
                    # НЕ сбрасываем токены полностью, сохраняем купленные токены
                    # Просто переводим на free тариф
                    # Сообщаем пользователю об окончании подписки
                    if db_manager.update_user(user_id, subscription_type='free', subscription_start=None, subscription_end=None):
                        user = self.get_user(user_id)
                        plan_type = 'free'
                        
                        # Проверяем, остались ли у пользователя купленные токены
                        tokens_remaining = user.get('tokens_remaining', 0) or 0
                        if tokens_remaining > 0:
                            return False, f"""🔔 Ваша подписка истекла!

💰 У вас осталось {tokens_remaining:,} токенов, которые сохранены.

Для использования бота:
1️⃣ Обновите подписку
2️⃣ Или используйте оставшиеся токены (доступно только с активной подпиской)

🔄 Нажмите "🔥 Подписка" для продления."""
            except (ValueError, TypeError):
                pass
            
        plan_limits = self.subscription_plans.get(plan_type, self.subscription_plans['free'])

        if user.get('admin_unlimited'):
            return True, ""
        
        # Для FREE: проверяем лимит запросов
        if plan_type == 'free':
            deepseek_limit = plan_limits.get('deepseek_max_requests')
            if deepseek_limit is None:
                deepseek_limit = 5
            requests_count = user.get('requests_count', 0)
            if requests_count is None:
                requests_count = 0
            if requests_count < deepseek_limit:
                remaining = deepseek_limit - requests_count
                return True, f"Доступно запросов: {remaining}"
            else:
                return False, self.get_subscription_message()
        
        # Для LITE/PREMIUM: проверяем только токены (контроль токенами)
        tokens_remaining = user.get('tokens_remaining', 0) or 0
        tokens_remaining = int(tokens_remaining)
        if tokens_remaining > 0:
            return True, ""
        else:
            max_tokens = plan_limits.get('max_tokens', 0)
            if max_tokens is None:
                max_tokens = 0
            return False, self.get_subscription_message()
    
    def can_make_yandex_request(self, user_id: int) -> Tuple[bool, str]:
        """Проверяет, может ли пользователь сделать запрос к Yandex Vision API"""
        user = self.get_user(user_id)
        plan_type = user.get('subscription_type', 'free')
        
        expires_str = user.get('subscription_end')
        if expires_str:
            try:
                if datetime.fromisoformat(expires_str) < datetime.now():
                    # НЕ сбрасываем лимиты полностью, сохраняем купленные токены и фото-запросы
                    # Просто переводим на free тариф
                    if db_manager.update_user(user_id, subscription_type='free', subscription_start=None, subscription_end=None):
                        user = self.get_user(user_id)
                        plan_type = 'free'
            except (ValueError, TypeError):
                pass
            
        plan_limits = self.subscription_plans.get(plan_type, self.subscription_plans['free'])

        if user.get('admin_unlimited'):
            return True, ""
        
        yandex_limit = plan_limits.get('yandex_max_requests')
        if yandex_limit is None:
            yandex_limit = 2
        yandex_count = user.get('yandex_requests_count', 0)
        if yandex_count is None:
            yandex_count = 0
        
        # Добавляем купленные фото-запросы к лимиту
        purchased_photo = user.get('purchased_photo_requests', 0) or 0
        total_limit = yandex_limit + purchased_photo
        
        if yandex_count < total_limit:
            remaining = total_limit - yandex_count
            return True, f"Доступно запросов к Yandex: {remaining}"
        else:
            return False, self.get_subscription_message(photo=True)

    def check_token_limit(self, user_id: int) -> Tuple[bool, str]:
        """Проверяет лимит токенов пользователя (только для LITE/PREMIUM)"""
        user = self.get_user(user_id)
        plan_type = user.get('subscription_type', 'free')
        
        # Для FREE не проверяем токены (там контроль по запросам)
        if plan_type == 'free':
            return True, ""
        
        plan_limits = self.subscription_plans.get(plan_type, self.subscription_plans['free'])
        
        # Проверяем оставшиеся токены
        if user.get('admin_unlimited'):
            return True, ""
        tokens_remaining = user.get('tokens_remaining', 0) or 0
        tokens_remaining = int(tokens_remaining)
        
        if tokens_remaining > 0:
            return True, ""
        else:
            return False, self.get_subscription_message()

    def increment_deepseek_request_count(self, user_id: int):
        """Увеличивает счетчик запросов к DeepSeek (только для FREE)"""
        user = self.get_user(user_id)
        plan_type = user.get('subscription_type', 'free')
        
        if user.get('admin_unlimited'):
            return
        
        # Увеличиваем счетчик только для FREE (для LITE/PREMIUM контроль токенами)
        if plan_type == 'free':
            new_count = user.get('requests_count', 0) + 1
            if db_manager.update_user(user_id, requests_count=new_count):
                user['requests_count'] = new_count
    
    def increment_yandex_request_count(self, user_id: int):
        """Увеличивает счетчик запросов к Yandex Vision"""
        user = self.get_user(user_id)
        if user.get('admin_unlimited'):
            return
        new_count = user.get('yandex_requests_count', 0) + 1
        if db_manager.update_user(user_id, yandex_requests_count=new_count):
            user['yandex_requests_count'] = new_count

    def increment_token_usage(self, user_id: int, amount: int):
        """Увеличивает количество использованных токенов и уменьшает остаток"""
        user = self.get_user(user_id)
        if user.get('admin_unlimited'):
            return
        tokens_used = user.get('tokens_used', 0) or 0
        tokens_remaining = user.get('tokens_remaining', 0) or 0
        new_tokens_used = int(tokens_used) + amount
        new_tokens_remaining = max(0, int(tokens_remaining) - amount)
        
        if db_manager.update_user(user_id, tokens_used=new_tokens_used, tokens_remaining=new_tokens_remaining):
            user['tokens_used'] = new_tokens_used
            user['tokens_remaining'] = new_tokens_remaining

    def activate_subscription(self, user_id: int, plan_type: str, days: int = 30):
        """Активирует подписку для пользователя"""
        if plan_type not in self.subscription_plans:
            return False
        
        now = datetime.now()
        expires = now + timedelta(days=days)
        plan_limits = self.subscription_plans[plan_type]
        
        update_data = {
            'subscription_type': plan_type,
            'subscription_start': now,
            'subscription_end': expires,
            'tokens_used': 0,
            'requests_count': 0,
            'yandex_requests_count': 0
        }
        
        # Для LITE/PREMIUM устанавливаем лимит токенов
        if plan_limits.get('max_tokens'):
            update_data['tokens_remaining'] = plan_limits['max_tokens']
        else:
            # Для FREE устанавливаем дефолтное значение
            update_data['tokens_remaining'] = 15000
        
        if db_manager.update_user(user_id, **update_data):
            # Обновляем кеш
            user = self.get_user(user_id)
            user.update({k: v.isoformat() if isinstance(v, datetime) else v for k, v in update_data.items()})
            return True
        return False

    def get_user_info(self, user_id: int) -> str:
        """Возвращает информацию о пользователе"""
        user = self.get_user(user_id)
        plan_type = user.get('subscription_type', 'free')
        
        expires_str = user.get('subscription_end')
        if expires_str and datetime.fromisoformat(expires_str) < datetime.now():
            plan_type = 'free'
               
        plan_limits = self.subscription_plans.get(plan_type, self.subscription_plans['free'])
        tokens_used = user.get('tokens_used', 0) or 0
        tokens_remaining = user.get('tokens_remaining', 0) or 0
        deepseek_count = user.get('requests_count', 0) or 0
        yandex_count = user.get('yandex_requests_count', 0) or 0
        
        tokens_used = int(tokens_used)
        tokens_remaining = int(tokens_remaining)
        deepseek_count = int(deepseek_count)
        yandex_count = int(yandex_count)
        
        if user.get('admin_unlimited'):
            info = "💎 Тариф: Безлимит (админ)\n"
            info += "🤖 Запросов: ∞\n"
            info += "📸 Запросов на решение по фото: ∞\n"
            info += f"📈 Использовано токенов: {tokens_used:,}\n\n"
            info += "💡 Для снятия лимитов оформите подписку."
            return info
        
        plan_name_map = {
            'free': 'Бесплатный',
            'lite': 'Lite',
            'premium': 'Premium'
        }
        plan_label = plan_name_map.get(plan_type, plan_type.capitalize())
        
        if plan_type == 'free':
            deepseek_limit = int(plan_limits.get('deepseek_max_requests') or 5)
            deepseek_value = f"{max(0, deepseek_limit - deepseek_count)} из {deepseek_limit}"
        else:
            max_tokens = int(plan_limits.get('max_tokens') or 0)
            deepseek_value = f"{tokens_remaining:,} токенов из {max_tokens:,}" if max_tokens else f"{tokens_remaining:,} токенов осталось"
        
        yandex_limit = int(plan_limits.get('yandex_max_requests') or 2)
        yandex_value = f"{max(0, yandex_limit - yandex_count)} из {yandex_limit}"
        
        info = f"💎 Тариф: {plan_label}\n"
        info += f"🤖 Запросов: {deepseek_value}\n"
        info += f"📸 Запросов на решение по фото: {yandex_value}\n"
        info += f"📈 Использовано токенов: {tokens_used:,}\n\n"
        info += "💡 Для снятия лимитов оформите подписку."
        return info

    def reset_user_limits(self, user_id: int):
        """Сбрасывает лимиты пользователя до бесплатного тарифа"""
        update_data = {
            'subscription_type': 'free',
            'subscription_start': None,
            'subscription_end': None,
            'tokens_used': 0,
            'tokens_remaining': 15000,
            'requests_count': 0,
            'yandex_requests_count': 0
        }
        if db_manager.update_user(user_id, **update_data):
            # Обновляем кеш
            if str(user_id) in self.users_cache:
                del self.users_cache[str(user_id)]
            return True
        return False
        
    def grant_admin_unlimited(self, user_id: int) -> bool:
        """Предоставляет пользователю безлимитный доступ"""
        user = self.get_user(user_id)
        if user.get('admin_unlimited'):
            return True
        user_id_str = str(user_id)
        if db_manager.update_user(user_id, admin_unlimited=True):
            user['admin_unlimited'] = True
            self.users_cache[user_id_str] = user
            return True
        return False
        
    def add_tokens(self, user_id: int, amount: int) -> bool:
        """Добавляет токены пользователю"""
        return db_manager.add_tokens(user_id, amount)
    
    def add_photo_requests(self, user_id: int, amount: int) -> bool:
        """Добавляет фото-запросы пользователю"""
        return db_manager.add_photo_requests(user_id, amount)
    
    def get_subscription_message(self, photo: bool = False) -> str:
        """Короткое сообщение-приглашение к покупке"""
        prefix = "🚫 Лимит запросов по фото исчерпан!" if photo else "🚫 Лимит запросов исчерпан!"
        message = f"""{prefix}

🌟 Купите подписку или необходимое количество токенов."""
        return message
