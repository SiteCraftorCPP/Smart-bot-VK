# 🚀 Простые команды для GitHub

## 📋 Команды для загрузки:

### **1. Очистка и инициализация:**
```bash
git init
git add .
git commit -m "Initial commit: SmartBot AI VK Bot with DeepSeek integration"
```

### **2. Подключение к GitHub:**
```bash
git remote add origin https://github.com/Beiseek/smartbot-ai.git
git branch -M main
```

### **3. Загрузка:**
```bash
git push -u origin main
```

## 🔧 Если есть ошибки:

### **Удалить существующий remote:**
```bash
git remote remove origin
git remote add origin https://github.com/Beiseek/smartbot-ai.git
```

### **Принудительная загрузка:**
```bash
git push -f origin main
```

## 📁 Что загружается:

✅ **Код бота:**
- main.py, vk_bot.py, deepseek_client.py
- user_manager.py, config.py
- requirements.txt

✅ **Документация:**
- README.md, vps_setup.md
- deploy_from_github.md, github_setup.md

✅ **Развертывание:**
- start_bot.sh, smartbot.service
- config.env.example

❌ **НЕ загружается:**
- config.env (токены)
- users.json (база данных)
- __pycache__/ (кэш)

## 🎯 После загрузки:

**Ссылка:** https://github.com/Beiseek/smartbot-ai

**Для VPS:**
```bash
git clone https://github.com/Beiseek/smartbot-ai.git
cd smartbot-ai
cp config.env.example config.env
nano config.env  # Добавь токены
```
