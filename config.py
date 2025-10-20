import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv('config.env')

class Config:
    # VK API настройки
    VK_TOKEN = os.getenv('VK_TOKEN')
    VK_GROUP_ID = int(os.getenv('VK_GROUP_ID', 0))
    
    # DeepSeek API настройки
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
    DEEPSEEK_BASE_URL = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')
    
    # Настройки бота
    BOT_PREFIX = os.getenv('BOT_PREFIX', '!')
    MAX_MESSAGE_LENGTH = int(os.getenv('MAX_MESSAGE_LENGTH', 4096))
    
    # Проверяем обязательные переменные
    @classmethod
    def validate(cls):
        required_vars = ['VK_TOKEN', 'DEEPSEEK_API_KEY']
        missing_vars = [var for var in required_vars if not getattr(cls, var)]
        
        if missing_vars:
            raise ValueError(f"Отсутствуют обязательные переменные: {', '.join(missing_vars)}")
        
        return True
