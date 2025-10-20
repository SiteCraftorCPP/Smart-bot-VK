import json
import os
from typing import Dict, Optional
from datetime import datetime, timedelta

class UserManager:
    def __init__(self, data_file: str = "users.json"):
        self.data_file = data_file
        self.users = self.load_users()
    
    def load_users(self) -> Dict:
        """
        Загружает данные пользователей из файла
        """
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_users(self):
        """
        Сохраняет данные пользователей в файл
        """
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения пользователей: {e}")
    
    def get_user(self, user_id: int) -> Dict:
        """
        Получает данные пользователя
        """
        if str(user_id) not in self.users:
            self.users[str(user_id)] = {
                'trial_requests': 0,
                'max_trial_requests': 5,
                'subscription_active': False,
                'subscription_expires': None,
                'tokens_remaining': 0,
                'created_at': datetime.now().isoformat()
            }
            self.save_users()
        
        return self.users[str(user_id)]
    
    def can_make_request(self, user_id: int) -> tuple[bool, str]:
        """
        Проверяет, может ли пользователь сделать запрос
        Возвращает (может_ли, сообщение)
        """
        user = self.get_user(user_id)
        
        # Проверяем активную подписку
        if user['subscription_active']:
            if user['subscription_expires']:
                expires = datetime.fromisoformat(user['subscription_expires'])
                if datetime.now() < expires:
                    return True, "Подписка активна"
                else:
                    # Подписка истекла
                    user['subscription_active'] = False
                    self.save_users()
        
        # Проверяем пробные запросы
        if user['trial_requests'] < user['max_trial_requests']:
            return True, f"Пробный запрос {user['trial_requests'] + 1}/{user['max_trial_requests']}"
        
        # Лимит исчерпан
        return False, "Лимит пробных запросов исчерпан"
    
    def increment_trial_request(self, user_id: int):
        """
        Увеличивает счетчик пробных запросов
        """
        user = self.get_user(user_id)
        user['trial_requests'] += 1
        self.save_users()
    
    def activate_subscription(self, user_id: int, days: int = 30):
        """
        Активирует подписку на указанное количество дней
        """
        user = self.get_user(user_id)
        user['subscription_active'] = True
        user['subscription_expires'] = (datetime.now() + timedelta(days=days)).isoformat()
        user['tokens_remaining'] = 1000000  # 1,000,000 токенов при активации
        self.save_users()
    
    def add_tokens(self, user_id: int, tokens: int):
        """
        Добавляет токены пользователю
        """
        user = self.get_user(user_id)
        user['tokens_remaining'] = user.get('tokens_remaining', 0) + tokens
        self.save_users()
    
    def consume_tokens(self, user_id: int, tokens: int = 1):
        """
        Тратит токены пользователя
        """
        user = self.get_user(user_id)
        if user['tokens_remaining'] >= tokens:
            user['tokens_remaining'] -= tokens
            self.save_users()
            return True
        return False
    
    def get_user_info(self, user_id: int) -> str:
        """
        Возвращает информацию о пользователе
        """
        user = self.get_user(user_id)
        
        if user['subscription_active']:
            expires = datetime.fromisoformat(user['subscription_expires'])
            days_left = (expires - datetime.now()).days
            
            # Вычисляем потраченные токены
            total_given = 1000000  # 1 миллион токенов при активации
            tokens_spent = total_given - user['tokens_remaining']
            
            return f"""👤 **Ваш профиль**

💎 **Подписка:** Активна
⏰ **Осталось дней:** {days_left}
🪙 **Токенов потрачено:** {tokens_spent:,}
🪙 **Токенов осталось:** {user['tokens_remaining']:,}

✅ Вы можете пользоваться всеми функциями бота!"""
        else:
            remaining_trial = user['max_trial_requests'] - user['trial_requests']
            return f"""👤 **Ваш профиль**

🆓 **Пробный период:** {remaining_trial} запросов осталось
💎 **Подписка:** Неактивна

⚠️ После исчерпания пробных запросов потребуется подписка."""
    
    def get_subscription_message(self, user_id: int) -> str:
        """
        Возвращает сообщение о необходимости подписки
        """
        return f"""🚫 **Лимит пробных запросов исчерпан!**

🆓 Вы использовали все {self.get_user(user_id)['max_trial_requests']} пробных запросов.

💎 **Для продолжения работы оформите подписку:**

✅ **Подписка Стандарт** - 299₽/месяц
• 1,000,000 токенов в месяц
• Приоритетная поддержка
• Расширенные возможности AI

🪙 **Или купите токены:**
• 200,000 токенов - 99₽
• 500,000 токенов - 199₽

📞 **Свяжитесь с нами:** https://vk.com/creativedgecpp"""
