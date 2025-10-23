@echo off
echo Обновление GitHub репозитория...

echo.
echo Проверяем статус...
git status

echo.
echo Добавляем все изменения...
git add .

echo.
echo Создаем коммит...
git commit -m "Major update: Added conversation memory, token limits, photo packages, and Yandex Vision integration"

echo.
echo Отправляем на GitHub...
git push origin main

echo.
echo Готово! Репозиторий обновлен.
pause
