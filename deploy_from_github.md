# 🚀 Развертывание SmartBot AI с GitHub

## 📋 Быстрое развертывание на VPS:

### **1. Клонирование репозитория:**
```bash
git clone https://github.com/Beiseek/smartbot-ai.git
cd smartbot-ai
```

### **2. Настройка конфигурации:**
```bash
cp config.env.example config.env
nano config.env
```

**Добавьте в config.env:**
```env
VK_TOKEN=your_vk_token_here
VK_GROUP_ID=233388296
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
BOT_PREFIX=!
MAX_MESSAGE_LENGTH=4096
```

### **3. Установка зависимостей:**
```bash
pip3 install -r requirements.txt
```

### **4. Настройка автозапуска:**
```bash
# Копируем service файл
sudo cp smartbot.service /etc/systemd/system/

# Перезагружаем systemd
sudo systemctl daemon-reload

# Включаем автозапуск
sudo systemctl enable smartbot

# Запускаем бота
sudo systemctl start smartbot
```

### **5. Проверка работы:**
```bash
# Статус бота
sudo systemctl status smartbot

# Логи
sudo journalctl -u smartbot -f
```

## 🔄 Обновление кода:

### **На VPS сервере:**
```bash
cd smartbot-ai
git pull origin main
sudo systemctl restart smartbot
```

### **Локальная разработка:**
```bash
# Внесите изменения в код
git add .
git commit -m "Описание изменений"
git push origin main

# На VPS сервере
git pull origin main
sudo systemctl restart smartbot
```

## 📊 Мониторинг:

### **Проверка статуса:**
```bash
sudo systemctl status smartbot
```

### **Просмотр логов:**
```bash
# Все логи
sudo journalctl -u smartbot

# Последние логи
sudo journalctl -u smartbot -f

# Логи за последний час
sudo journalctl -u smartbot --since "1 hour ago"
```

### **Перезапуск:**
```bash
sudo systemctl restart smartbot
```

## 🔧 Управление:

### **Остановка:**
```bash
sudo systemctl stop smartbot
```

### **Запуск:**
```bash
sudo systemctl start smartbot
```

### **Отключение автозапуска:**
```bash
sudo systemctl disable smartbot
```

## 📁 Структура на сервере:

```
/root/smartbot-ai/
├── main.py                 # Главный файл
├── vk_bot.py             # Логика бота
├── deepseek_client.py    # DeepSeek API
├── user_manager.py       # Пользователи
├── config.py             # Конфигурация
├── config.env            # Токены (НЕ в Git)
├── users.json            # База данных (НЕ в Git)
├── requirements.txt      # Зависимости
├── start_bot.sh         # Скрипт запуска
├── smartbot.service      # Systemd сервис
└── README.md            # Документация
```

## 🔒 Безопасность:

### **Файлы, которые НЕ в Git:**
- ✅ `config.env` - содержит токены
- ✅ `users.json` - база данных пользователей
- ✅ `*.log` - файлы логов

### **Резервное копирование:**
```bash
# Создание бэкапа
tar -czf smartbot-backup-$(date +%Y%m%d).tar.gz /root/smartbot-ai/

# Восстановление
tar -xzf smartbot-backup-YYYYMMDD.tar.gz -C /
```

## 🎯 Готово!

После выполнения всех шагов у вас будет:
- ✅ **Работающий бот** на VPS сервере
- ✅ **Автозапуск** при перезагрузке сервера
- ✅ **Мониторинг** через systemd
- ✅ **Обновления** через GitHub
- ✅ **Безопасность** токенов

**Удачного развертывания!** 🚀
