@echo off
echo Установка зависимостей...
pip install vk-api==11.9.9
pip install requests==2.31.0
pip install python-dotenv==1.0.0
pip install aiohttp==3.9.1

echo.
echo Запуск бота...
python main.py
pause
