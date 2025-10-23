import json
import os
from typing import Dict, Optional
from datetime import datetime, timedelta
from config import Config

class UserManager:
    def __init__(self, data_file: str = "users.json"):
        self.data_file = data_file
        self.users = self.load_users()
        self.subscription_plans = {
            'free': {'max_photo': 1, 'max_tokens': 15000, 'price': 0},
            'lite': {'max_photo': 10, 'max_tokens': 200000, 'price': 199},
            'pro': {'max_photo': 50, 'max_tokens': 1000000, 'price': 499}
        }

    def load_users(self) -> Dict:
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def save_users(self):
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения пользователей: {e}")

    def get_user(self, user_id: int) -> Dict:
        user_id_str = str(user_id)
        if user_id_str not in self.users:
            self.users[user_id_str] = {
                'subscription_type': 'free',
                'subscription_expires': None,
                'photo_recognitions_used': 0,
                'extra_photos': 0,
                'tokens_used': 0,
                'created_at': datetime.now().isoformat(),
                'conversation_history': []
            }
            self.save_users()
        
        # Проверяем, есть ли у существующего пользователя новая структура данных
        user_data = self.users[user_id_str]
        # Миграция старых данных
        if 'tokens_used' not in user_data:
            user_data['tokens_used'] = 0
        if 'extra_photos' not in user_data:
            user_data['extra_photos'] = 0
        if 'subscription_type' not in user_data:
            # Если нет - это старый пользователь. Обновляем его.
            user_data['subscription_type'] = 'free'
            user_data['subscription_expires'] = None
            user_data['photo_recognitions_used'] = 0
            user_data['conversation_history'] = [] # Ensure conversation history is initialized
            self.save_users()
            
        if 'conversation_history' not in user_data:
            user_data['conversation_history'] = []

        self.save_users()
        
        return self.users[user_id_str]

    def get_history(self, user_id: int) -> list:
        user = self.get_user(user_id)
        return user.get('conversation_history', [])

    def add_to_history(self, user_id: int, role: str, content: str):
        user = self.get_user(user_id)
        history = user.get('conversation_history', [])
        
        history.append({"role": role, "content": content})
        
        # Обрезаем историю, если она слишком длинная
        if len(history) > Config.MAX_HISTORY_MESSAGES:
            history = history[-Config.MAX_HISTORY_MESSAGES:]
            
        self.users[str(user_id)]['conversation_history'] = history
        self.save_users()

    def clear_history(self, user_id: int):
        user = self.get_user(user_id)
        self.users[str(user_id)]['conversation_history'] = []
        self.save_users()

    def can_recognize_photo(self, user_id: int) -> tuple[bool, str]:
        user = self.get_user(user_id)
        plan_type = user['subscription_type']
        
        # Проверяем, не истекла ли подписка
        if user['subscription_expires'] and datetime.fromisoformat(user['subscription_expires']) < datetime.now():
            user['subscription_type'] = 'free'
            plan_type = 'free'
            self.save_users()
            
        plan_limits = self.subscription_plans.get(plan_type, self.subscription_plans['free'])
        total_photo_limit = plan_limits['max_photo'] + user.get('extra_photos', 0)
        
        if user['photo_recognitions_used'] < total_photo_limit:
            remaining = total_photo_limit - user['photo_recognitions_used']
            return True, f"Доступно распознаваний: {remaining}"
        else:
            return False, self.get_subscription_message(user_id)
    
    def check_token_limit(self, user_id: int) -> tuple[bool, str]:
        user = self.get_user(user_id)
        plan_type = user.get('subscription_type', 'free')
        plan_limits = self.subscription_plans.get(plan_type, self.subscription_plans['free'])
        
        # В бесплатном тарифе лимит жесткий, в платных - нет (только по дням)
        # if plan_type != 'free' and plan_limits['max_tokens'] == 0:
        #    return True, "У вас безлимитные токены в рамках подписки."

        if user.get('tokens_used', 0) < plan_limits['max_tokens']:
            return True, ""
        else:
            msg = f"🚫 **Лимит токенов исчерпан!**\n\nВы использовали {user.get('tokens_used', 0):,} из {plan_limits['max_tokens']:,} доступных токенов.\n\n"
            msg += self.get_subscription_message(user_id, show_photo_limit_exceeded=False)
            return False, msg

    def increment_photo_usage(self, user_id: int):
        user = self.get_user(user_id)
        user['photo_recognitions_used'] += 1
        self.save_users()

    def increment_token_usage(self, user_id: int, amount: int):
        user = self.get_user(user_id)
        user['tokens_used'] = user.get('tokens_used', 0) + amount
        self.save_users()

    def add_photo_recognitions(self, user_id: int, amount: int):
        user = self.get_user(user_id)
        user['extra_photos'] = user.get('extra_photos', 0) + amount
        self.save_users()

    def activate_subscription(self, user_id: int, plan_type: str, days: int = 30):
        if plan_type not in self.subscription_plans:
            return False
        
        user = self.get_user(user_id)
        user['subscription_type'] = plan_type
        user['subscription_expires'] = (datetime.now() + timedelta(days=days)).isoformat()
        user['photo_recognitions_used'] = 0 # Сбрасываем счетчик при новой подписке
        user['tokens_used'] = 0
        user['extra_photos'] = 0
        self.save_users()
        return True

    def get_user_info(self, user_id: int) -> str:
        user = self.get_user(user_id)
        plan_type = user.get('subscription_type', 'free')
        plan_limits = self.subscription_plans.get(plan_type, self.subscription_plans['free'])
        
        if plan_type != 'free' and user['subscription_expires']:
             expires = datetime.fromisoformat(user['subscription_expires'])
             if expires < datetime.now():
                 # Если подписка истекла, показываем как free
                 plan_type = 'free'
                 plan_limits = self.subscription_plans['free']
        
        total_photo_limit = plan_limits['max_photo'] + user.get('extra_photos', 0)
        photo_remaining = total_photo_limit - user['photo_recognitions_used']
        tokens_used = user.get('tokens_used', 0)
        
        info = f"👤 **Ваш профиль**\n\n"
        if plan_type == 'free':
            info += f"💎 **Тариф:** Бесплатный\n"
            info += f"📸 **Распознаваний осталось:** {photo_remaining} из {total_photo_limit}\n"
            info += f"🪙 **Токенов использовано:** {tokens_used:,} из {plan_limits['max_tokens']:,}\n\n"
            info += "💡 Для снятия лимитов оформите подписку."
        else:
            days_left = (datetime.fromisoformat(user['subscription_expires']) - datetime.now()).days
            info += f"💎 **Тариф:** {plan_type.capitalize()} (осталось {days_left} дн.)\n"
            info += f"📸 **Распознаваний осталось:** {photo_remaining} из {total_photo_limit}\n"
            info += f"🪙 **Токенов использовано:** {tokens_used:,} из {plan_limits['max_tokens']:,}\n\n"
        
        return info

    def reset_user_limits(self, user_id: int):
        user = self.get_user(user_id)
        user['subscription_type'] = 'free'
        user['subscription_expires'] = None
        user['photo_recognitions_used'] = 0
        user['tokens_used'] = 0
        user['extra_photos'] = 0
        self.save_users()

    def get_subscription_message(self, user_id: int, show_photo_limit_exceeded: bool = True) -> str:
        header = "🚫 **Лимит на распознавание фото исчерпан!**\n\n" if show_photo_limit_exceeded else ""
        
        message = f"""{header}💎 **Наши тарифы:**
- **Lite (199₽/мес):** 10 фото и 200,000 токенов.
- **Pro (499₽/мес):** 50 фото и 1,000,000 токенов.

📸 **Докупить распознавания:**
- **10 фото:** 50₽
- **25 фото:** 100₽

Для покупки или продления подписки напишите администратору: [ссылка]"""
        return message
