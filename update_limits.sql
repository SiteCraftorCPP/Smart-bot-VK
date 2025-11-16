-- Команда для обновления лимитов в pgAdmin 4
-- Скопируйте и выполните в Query Tool

-- Шаг 1: Добавить новое поле yandex_requests_count если его нет
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS yandex_requests_count INTEGER DEFAULT 0;

ALTER TABLE users 
ADD COLUMN IF NOT EXISTS admin_unlimited BOOLEAN DEFAULT FALSE;

-- Шаг 2: Добавить новые поля в subscription_plans если их нет
ALTER TABLE subscription_plans 
ADD COLUMN IF NOT EXISTS deepseek_max_requests INTEGER,
ADD COLUMN IF NOT EXISTS yandex_max_requests INTEGER;

-- Если yandex_max_requests не может быть NULL, нужно сначала добавить с NULL, потом обновить
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'subscription_plans' 
        AND column_name = 'yandex_max_requests'
    ) THEN
        ALTER TABLE subscription_plans 
        ADD COLUMN yandex_max_requests INTEGER;
    END IF;
END $$;

-- Шаг 3: Обновить данные в subscription_plans
-- FREE план
UPDATE subscription_plans 
SET 
    max_tokens = NULL,
    deepseek_max_requests = 5,
    yandex_max_requests = 2,
    price = 0.00
WHERE plan_name = 'free';

-- LITE план
UPDATE subscription_plans 
SET 
    max_tokens = 800000,
    deepseek_max_requests = NULL,
    yandex_max_requests = 2,
    price = 300.00
WHERE plan_name = 'lite';

-- PREMIUM план (если был pro, то переименуем)
UPDATE subscription_plans 
SET 
    plan_name = 'premium',
    max_tokens = 1000000,
    deepseek_max_requests = NULL,
    yandex_max_requests = 50,
    price = 449.00
WHERE plan_name IN ('premium', 'pro');

-- Если нет записи для premium, создаем
INSERT INTO subscription_plans (plan_name, max_tokens, deepseek_max_requests, yandex_max_requests, price)
SELECT 'premium', 1000000, NULL, 50, 449.00
WHERE NOT EXISTS (SELECT 1 FROM subscription_plans WHERE plan_name = 'premium');

-- Шаг 4: Обновить пользователей (переименовать pro в premium)
UPDATE users 
SET subscription_type = 'premium' 
WHERE subscription_type = 'pro';

-- Шаг 5: Обнулить yandex_requests_count для всех пользователей (если нужно)
UPDATE users 
SET yandex_requests_count = 0 
WHERE yandex_requests_count IS NULL;

-- Проверка: посмотреть результат
SELECT 
    plan_name,
    max_tokens,
    deepseek_max_requests,
    yandex_max_requests,
    price
FROM subscription_plans
ORDER BY price;



