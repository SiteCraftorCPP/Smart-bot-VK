# 🚀 Руководство по развертыванию бота

## Вариант 1: Heroku (бесплатно)

### 1. Установи Heroku CLI
```bash
# Скачай с https://devcenter.heroku.com/articles/heroku-cli
```

### 2. Войди в Heroku
```bash
heroku login
```

### 3. Создай приложение
```bash
heroku create smartbot-ai
```

### 4. Настрой переменные окружения
```bash
heroku config:set VK_TOKEN=твой_vk_токен
heroku config:set VK_GROUP_ID=233388296
heroku config:set DEEPSEEK_API_KEY=твой_deepseek_ключ
```

### 5. Загрузи код
```bash
git init
git add .
git commit -m "Initial commit"
git push heroku main
```

### 6. Запусти бота
```bash
heroku ps:scale worker=1
```

## Вариант 2: VPS (рекомендуется)

### 1. Купи VPS
- Timeweb: 200₽/месяц
- Beget: 300₽/месяц

### 2. Подключись к серверу
```bash
ssh root@your-server-ip
```

### 3. Установи Python
```bash
apt update
apt install python3 python3-pip git
```

### 4. Загрузи код
```bash
git clone https://github.com/your-repo/smartbot.git
cd smartbot
```

### 5. Установи зависимости
```bash
pip3 install -r requirements.txt
```

### 6. Настрой переменные
```bash
nano config.env
# Добавь свои токены
```

### 7. Запусти бота
```bash
python3 main.py
```

### 8. Настрой автозапуск (systemd)
```bash
sudo nano /etc/systemd/system/smartbot.service
```

Содержимое файла:
```ini
[Unit]
Description=SmartBot AI
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/smartbot
ExecStart=/usr/bin/python3 main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable smartbot
sudo systemctl start smartbot
```

## Вариант 3: Railway

### 1. Зарегистрируйся на railway.app
### 2. Подключи GitHub репозиторий
### 3. Настрой переменные окружения
### 4. Деплой автоматический

## 🔧 Мониторинг

### Проверка статуса (VPS):
```bash
sudo systemctl status smartbot
sudo systemctl restart smartbot
```

### Логи (VPS):
```bash
sudo journalctl -u smartbot -f
```

### Heroku логи:
```bash
heroku logs --tail
```
