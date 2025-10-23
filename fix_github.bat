@echo off
echo Исправление GitHub подключения...

echo.
echo Удаление старого remote...
git remote remove origin

echo.
echo Добавление правильного remote...
git remote add origin https://github.com/Beiseek/smartbot-ai.git

echo.
echo Проверка remote...
git remote -v

echo.
echo Загрузка на GitHub...
git push -u origin main

echo.
echo ✅ Готово!
echo 🔗 Ссылка: https://github.com/Beiseek/smartbot-ai
pause
