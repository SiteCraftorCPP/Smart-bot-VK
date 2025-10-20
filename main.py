#!/usr/bin/env python3
"""
VK Bot с DeepSeek AI
Главный файл для запуска бота
"""

import sys
import os
import asyncio
from vk_bot import VKBot

def main():
    """
    Главная функция запуска бота
    """
    print("🤖 Запуск VK бота с DeepSeek AI...")
    
    try:
        # Проверяем наличие config.env файла
        if not os.path.exists('config.env'):
            print("❌ Файл config.env не найден!")
            print("Создайте файл config.env и заполните необходимые токены.")
            return
        
        # Создаем и запускаем бота
        bot = VKBot()
        bot.run()
        
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
