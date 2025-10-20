@echo off
echo 🚀 Загрузка SmartBot AI на GitHub...

echo.
echo Инициализация Git репозитория...
git init

echo.
echo Добавление файлов...
git add .

echo.
echo Создание коммита...
git commit -m "Initial commit: SmartBot AI VK Bot with DeepSeek integration"

echo.
echo Подключение к GitHub репозиторию...
git remote add origin https://github.com/Beiseek/smartbot-ai.git

echo.
echo Переименование ветки в main...
git branch -M main

echo.
echo Загрузка на GitHub...
git push -u origin main

echo.
echo ✅ Готово! Проект загружен на GitHub!
echo 🔗 Ссылка: https://github.com/Beiseek/smartbot-ai
echo.
echo Теперь вы можете:
echo 1. Развернуть бота на VPS сервере
echo 2. Клонировать репозиторий на другом компьютере
echo 3. Обновлять код через GitHub
echo.
pause
