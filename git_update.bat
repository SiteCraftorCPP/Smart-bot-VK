@echo off
chcp 65001 >nul
echo Обновление GitHub репозитория...
echo.

echo Проверяем статус Git...
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
echo.
echo Что было добавлено:
echo - Память диалога (последние 10 сообщений)
echo - Лимиты по токенам для всех тарифов
echo - Пакеты фото (10 за 50₽, 25 за 100₽)
echo - Yandex Vision API для распознавания текста
echo - Новые секретные команды для админа
echo.
pause
