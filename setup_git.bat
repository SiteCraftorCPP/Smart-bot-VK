@echo off
echo Инициализация Git репозитория...

git init
git add .
git commit -m "Initial commit: SmartBot AI VK Bot with DeepSeek integration"

echo.
echo Репозиторий инициализирован!
echo.
echo Теперь создайте репозиторий на GitHub:
echo 1. Перейдите на https://github.com/new
echo 2. Назовите репозиторий: smartbot-ai
echo 3. Сделайте его публичным или приватным
echo 4. НЕ добавляйте README, .gitignore или лицензию
echo 5. Нажмите "Create repository"
echo.
echo После создания репозитория выполните:
echo git remote add origin https://github.com/YOUR_USERNAME/smartbot-ai.git
echo git branch -M main
echo git push -u origin main
echo.
pause
