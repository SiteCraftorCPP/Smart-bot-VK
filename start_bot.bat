@echo off
echo 🤖 Запуск SmartBot AI...

echo.
echo Проверка файлов...
if not exist "main.py" (
    echo ❌ Файл main.py не найден!
    pause
    exit
)

if not exist "config.env" (
    echo ❌ Файл config.env не найден!
    echo Создайте файл config.env с вашими токенами
    pause
    exit
)

echo ✅ Файлы найдены

echo.
echo Запуск бота...
python main.py

echo.
echo Бот остановлен
pause
