#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для проверки конфигурации бота
"""

import os
import sys
import io
from dotenv import load_dotenv

# Исправление кодировки для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Загружаем переменные окружения
config_file = 'config.env'
if not os.path.exists(config_file):
    print(f"❌ Файл {config_file} не найден!")
    print(f"📝 Создайте файл {config_file} на основе config.env.example")
    sys.exit(1)

load_dotenv(config_file)

# Обязательные переменные
required_vars = {
    'VK_TOKEN': 'VK API токен',
    'VK_GROUP_ID': 'ID группы VK',
    'DEEPSEEK_API_KEY': 'DeepSeek API ключ (основной)',
    'YOOKASSA_SHOP_ID': 'YooKassa Shop ID',
    'YOOKASSA_API_KEY': 'YooKassa API ключ',
}

# Опциональные переменные (для балансировки)
optional_vars = {
    'DEEPSEEK_API_KEY_2': 'DeepSeek API ключ #2 (опционально)',
    'DEEPSEEK_API_KEY_3': 'DeepSeek API ключ #3 (опционально)',
    'YANDEX_FOLDER_ID': 'Yandex Vision Folder ID',
    'YANDEX_SERVICE_ACCOUNT_ID': 'Yandex Vision Service Account ID',
    'YANDEX_API_KEY_ID': 'Yandex Vision API Key ID',
    'YANDEX_API_SECRET_KEY': 'Yandex Vision Secret Key',
    'DB_HOST': 'PostgreSQL хост',
    'DB_PORT': 'PostgreSQL порт',
    'DB_USER': 'PostgreSQL пользователь',
    'DB_PASSWORD': 'PostgreSQL пароль',
    'DB_NAME': 'PostgreSQL база данных',
}

print("🔍 Проверка конфигурации...\n")
print("=" * 60)

# Проверяем обязательные переменные
print("\n✅ ОБЯЗАТЕЛЬНЫЕ ПЕРЕМЕННЫЕ:")
print("-" * 60)
all_ok = True
missing_vars = []

for var, description in required_vars.items():
    value = os.getenv(var)
    if not value or value.strip() in ['', '000000', 'your_yookassa_shop_id_here', 'your_yookassa_api_key_here', 'your_vk_token_here', 'your_group_id_here', 'your_deepseek_api_key_here']:
        print(f"❌ {var:25} - ОТСУТСТВУЕТ или неверное значение")
        print(f"   Описание: {description}")
        all_ok = False
        missing_vars.append(var)
    else:
        # Показываем только первые и последние символы для безопасности
        masked_value = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
        print(f"✅ {var:25} - OK ({masked_value})")

# Проверяем опциональные переменные
print("\n📋 ОПЦИОНАЛЬНЫЕ ПЕРЕМЕННЫЕ:")
print("-" * 60)
optional_missing = []

for var, description in optional_vars.items():
    value = os.getenv(var)
    if not value or value.strip() in ['', 'твой_folder_id', 'твой_service_account_id', 'твой_key_id']:
        print(f"⚠️  {var:25} - не указано")
        optional_missing.append(var)
    else:
        if 'SECRET' in var or 'KEY' in var or 'PASSWORD' in var:
            masked_value = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
        else:
            masked_value = value
        print(f"✅ {var:25} - OK ({masked_value})")

# Итоговый результат
print("\n" + "=" * 60)
if all_ok:
    print("✅ ВСЕ ОБЯЗАТЕЛЬНЫЕ ПЕРЕМЕННЫЕ НАСТРОЕНЫ ПРАВИЛЬНО!")
    print("\n📝 Рекомендации:")
    if optional_missing:
        print(f"   - Указано {len(optional_vars) - len(optional_missing)}/{len(optional_vars)} опциональных переменных")
        if 'DEEPSEEK_API_KEY_2' in optional_missing:
            print("   - Для балансировки нагрузки рекомендуется добавить DEEPSEEK_API_KEY_2 и DEEPSEEK_API_KEY_3")
        if 'YANDEX_SERVICE_ACCOUNT_ID' in optional_missing:
            print("   - Для работы с изображениями требуется настроить Yandex Vision API")
        if 'DB_HOST' in optional_missing:
            print("   - Для продакшена рекомендуется использовать PostgreSQL")
    print("\n🚀 Бот готов к запуску!")
    sys.exit(0)
else:
    print("❌ ОБНАРУЖЕНЫ ПРОБЛЕМЫ В КОНФИГУРАЦИИ!")
    print(f"\n📝 Отсутствуют или неверно указаны переменные:")
    for var in missing_vars:
        print(f"   - {var}")
    print(f"\n💡 Убедитесь, что все обязательные переменные указаны в {config_file}")
    print(f"   Используйте config.env.example как шаблон")
    sys.exit(1)
