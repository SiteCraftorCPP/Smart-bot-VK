import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv('config.env')

class Config:
    # VK API настройки
    VK_TOKEN = os.getenv('VK_TOKEN')
    VK_GROUP_ID = int(os.getenv('VK_GROUP_ID', 0))
    
    # DeepSeek API настройки (поддержка нескольких ключей для балансировки нагрузки)
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
    DEEPSEEK_API_KEY_2 = os.getenv('DEEPSEEK_API_KEY_2', 'sk-d474df7535064db28a20867c539c2da1')
    DEEPSEEK_API_KEY_3 = os.getenv('DEEPSEEK_API_KEY_3', 'sk-6f29d325b1a0490995e5ed701d6d839e')
    DEEPSEEK_BASE_URL = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')

    # Yandex Vision API настройки
    YANDEX_FOLDER_ID = os.getenv('YANDEX_FOLDER_ID')
    YANDEX_SERVICE_ACCOUNT_ID = os.getenv('YANDEX_SERVICE_ACCOUNT_ID')
    YANDEX_API_KEY_ID = os.getenv('YANDEX_API_KEY_ID')
    YANDEX_API_SECRET_KEY = os.getenv('YANDEX_API_SECRET_KEY')
    
    # YooKassa API настройки
    YOOKASSA_SHOP_ID = os.getenv('YOOKASSA_SHOP_ID', '000000')
    YOOKASSA_API_KEY = os.getenv('YOOKASSA_API_KEY', 'live_8tZcQ0xWYZrURSmJ4jPgi4jg-XUS3wapHITNz63L0zI')

    # Database (PostgreSQL)
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_NAME = os.getenv('DB_NAME', 'smartbot_db')

    # Bot settings
    BOT_PREFIX = os.getenv('BOT_PREFIX', '!')
    MAX_MESSAGE_LENGTH = int(os.getenv('MAX_MESSAGE_LENGTH', 4096))
    USERS_FILE = "users.json"  # Файл для хранения данных пользователей
    MAX_HISTORY_MESSAGES = 10  # Сколько последних сообщений хранить в истории (5 пар)
    
    # Проверяем обязательные переменные
    @classmethod
    def validate(cls):
        required_vars = ['VK_TOKEN', 'DEEPSEEK_API_KEY']
        missing_vars = [var for var in required_vars if not getattr(cls, var)]
        
        if missing_vars:
            raise ValueError(f"Отсутствуют обязательные переменные: {', '.join(missing_vars)}")
        
        return True
