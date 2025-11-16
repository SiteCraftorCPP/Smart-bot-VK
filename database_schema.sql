-- PostgreSQL Database Schema for SmartBot AI
-- Создание базы данных и таблиц

-- Таблица тарифных планов
CREATE TABLE IF NOT EXISTS subscription_plans (
    id SERIAL PRIMARY KEY,
    plan_name VARCHAR(50) UNIQUE NOT NULL,
    max_tokens INTEGER,
    deepseek_max_requests INTEGER,
    yandex_max_requests INTEGER NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL,
    profile_link VARCHAR(255),
    full_name VARCHAR(255),
    phone_number VARCHAR(20),
    subscription_type VARCHAR(50) DEFAULT 'free',
    subscription_start TIMESTAMP,
    subscription_end TIMESTAMP,
    tokens_used INTEGER DEFAULT 0,
    tokens_remaining INTEGER DEFAULT 15000,
    requests_count INTEGER DEFAULT 0,
    yandex_requests_count INTEGER DEFAULT 0,
    admin_unlimited BOOLEAN DEFAULT FALSE,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subscription_type) REFERENCES subscription_plans(plan_name) ON UPDATE CASCADE
);

-- Индексы для оптимизации запросов
CREATE INDEX IF NOT EXISTS idx_user_id ON users(user_id);
CREATE INDEX IF NOT EXISTS idx_subscription_type ON users(subscription_type);
CREATE INDEX IF NOT EXISTS idx_last_activity ON users(last_activity);

-- Триггер для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_subscription_plans_updated_at BEFORE UPDATE ON subscription_plans
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Заполнение тарифных планов
INSERT INTO subscription_plans (plan_name, max_tokens, deepseek_max_requests, yandex_max_requests, price) 
VALUES 
    ('free', NULL, 5, 2, 0.00),
    ('lite', 800000, NULL, 2, 300.00),
    ('premium', 1000000, NULL, 50, 449.00)
ON CONFLICT (plan_name) DO UPDATE SET
    max_tokens = EXCLUDED.max_tokens,
    deepseek_max_requests = EXCLUDED.deepseek_max_requests,
    yandex_max_requests = EXCLUDED.yandex_max_requests,
    price = EXCLUDED.price;

-- Комментарии к таблицам
COMMENT ON TABLE users IS 'Информация о пользователях VK бота';
COMMENT ON TABLE subscription_plans IS 'Тарифные планы подписок';

COMMENT ON COLUMN users.user_id IS 'VK ID пользователя';
COMMENT ON COLUMN users.profile_link IS 'Ссылка на профиль VK';
COMMENT ON COLUMN users.full_name IS 'ФИО пользователя';
COMMENT ON COLUMN users.phone_number IS 'Номер телефона';
COMMENT ON COLUMN users.subscription_type IS 'Тип подписки: free/lite/pro';
COMMENT ON COLUMN users.tokens_used IS 'Количество использованных токенов';
COMMENT ON COLUMN users.tokens_remaining IS 'Остаток токенов';
COMMENT ON COLUMN users.requests_count IS 'Количество выполненных запросов';
COMMENT ON COLUMN users.admin_unlimited IS 'Флаг пользователей с безлимитным доступом';
COMMENT ON COLUMN users.last_activity IS 'Дата последней активности';



