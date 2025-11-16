-- Миграция существующей БД для новой системы лимитов
-- Выполнить в pgAdmin 4 через Query Tool

-- Шаг 1: Добавить новое поле yandex_requests_count в таблицу users
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS yandex_requests_count INTEGER DEFAULT 0;

ALTER TABLE users 
ADD COLUMN IF NOT EXISTS admin_unlimited BOOLEAN DEFAULT FALSE;

-- Шаг 2: Обновить структуру таблицы subscription_plans
-- Добавляем новые поля
ALTER TABLE subscription_plans 
ADD COLUMN IF NOT EXISTS deepseek_max_requests INTEGER,
ADD COLUMN IF NOT EXISTS yandex_max_requests INTEGER;

-- Шаг 3: Обновляем существующие записи в subscription_plans
-- FREE план
UPDATE subscription_plans 
SET 
    max_tokens = NULL,
    deepseek_max_requests = 5,
    yandex_max_requests = 2
WHERE plan_name = 'free';

-- LITE план
UPDATE subscription_plans 
SET 
    max_tokens = 800000,
    deepseek_max_requests = NULL,
    yandex_max_requests = 2,
    price = 300.00
WHERE plan_name = 'lite';

-- PREMIUM план (ранее мог быть pro)
UPDATE subscription_plans 
SET 
    plan_name = 'premium',
    max_tokens = 1000000,
    deepseek_max_requests = NULL,
    yandex_max_requests = 50,
    price = 449.00
WHERE plan_name IN ('premium', 'pro');

-- Шаг 4: Если нужно переименовать pro в premium
UPDATE users 
SET subscription_type = 'premium' 
WHERE subscription_type = 'pro';

-- Шаг 5: Обнуляем счетчики для новых пользователей (опционально)
UPDATE users 
SET yandex_requests_count = 0 
WHERE yandex_requests_count IS NULL;

-- Проверка: просмотр обновленных данных
SELECT 
    plan_name,
    max_tokens,
    deepseek_max_requests,
    yandex_max_requests,
    price
FROM subscription_plans
ORDER BY price;

