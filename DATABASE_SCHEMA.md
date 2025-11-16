# 📊 Схема базы данных PostgreSQL - SmartBot AI

## 🗄️ Структура базы данных

### Диаграмма связей

```
┌─────────────────────────────┐
│   subscription_plans        │
├─────────────────────────────┤
│ • id (PK)                   │
│ • plan_name (UK)            │
│ • max_tokens                │
│ • max_requests              │
│ • price                     │
│ • created_at                │
│ • updated_at                │
└─────────────────────────────┘
              │
              │ FK: subscription_type
              │
              ▼
┌─────────────────────────────┐
│         users               │
├─────────────────────────────┤
│ • id (PK)                   │
│ • user_id (UK) ─────────────┼─── VK User ID
│ • profile_link              │
│ • full_name                 │
│ • phone_number              │
│ • subscription_type (FK)    │
│ • subscription_start        │
│ • subscription_end          │
│ • tokens_used               │
│ • tokens_remaining          │
│ • requests_count            │
│ • last_activity             │
│ • created_at                │
│ • updated_at                │
└─────────────────────────────┘
```

## 📋 Таблица: `users`

### Описание полей

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| **id** | SERIAL | PRIMARY KEY | Автоинкремент, внутренний ID |
| **user_id** | BIGINT | UNIQUE, NOT NULL | VK ID пользователя |
| **profile_link** | VARCHAR(255) | NULL | Ссылка на профиль VK |
| **full_name** | VARCHAR(255) | NULL | Имя Фамилия |
| **phone_number** | VARCHAR(20) | NULL | Телефон (из VK API) |
| **subscription_type** | VARCHAR(50) | DEFAULT 'free' | free / lite / pro |
| **subscription_start** | TIMESTAMP | NULL | Дата начала подписки |
| **subscription_end** | TIMESTAMP | NULL | Дата окончания |
| **tokens_used** | INTEGER | DEFAULT 0 | Всего использовано |
| **tokens_remaining** | INTEGER | DEFAULT 15000 | Остаток токенов |
| **requests_count** | INTEGER | DEFAULT 0 | Количество запросов |
| **last_activity** | TIMESTAMP | DEFAULT NOW() | Последняя активность |
| **created_at** | TIMESTAMP | DEFAULT NOW() | Дата регистрации |
| **updated_at** | TIMESTAMP | DEFAULT NOW() | Дата обновления |

### Индексы

```sql
CREATE INDEX idx_user_id ON users(user_id);
CREATE INDEX idx_subscription_type ON users(subscription_type);
CREATE INDEX idx_last_activity ON users(last_activity);
```

### Примеры записей

```sql
-- Бесплатный пользователь
INSERT INTO users (user_id, full_name, profile_link, subscription_type)
VALUES (
    123456789,
    'Иван Иванов',
    'https://vk.com/id123456789',
    'free'
);

-- Pro пользователь
INSERT INTO users (
    user_id, 
    full_name, 
    subscription_type,
    subscription_start,
    subscription_end,
    tokens_remaining
)
VALUES (
    987654321,
    'Мария Петрова',
    'pro',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP + INTERVAL '30 days',
    1000000
);
```

## 📋 Таблица: `subscription_plans`

### Описание полей

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| **id** | SERIAL | PRIMARY KEY | Автоинкремент |
| **plan_name** | VARCHAR(50) | UNIQUE, NOT NULL | free / lite / pro |
| **max_tokens** | INTEGER | NOT NULL | Лимит токенов/месяц |
| **max_requests** | INTEGER | NOT NULL | Лимит запросов/месяц |
| **price** | DECIMAL(10,2) | NOT NULL | Цена в рублях |
| **created_at** | TIMESTAMP | DEFAULT NOW() | Дата создания |
| **updated_at** | TIMESTAMP | DEFAULT NOW() | Дата обновления |

### Данные по умолчанию

```sql
INSERT INTO subscription_plans (plan_name, max_tokens, max_requests, price)
VALUES 
    ('free', 15000, 50, 0.00),
    ('lite', 200000, 1000, 199.00),
    ('pro', 1000000, 10000, 499.00);
```

### Визуализация тарифов

```
┌─────────────────────────────────────────────────┐
│  FREE                                           │
│  • Токенов: 15,000 / месяц                     │
│  • Запросов: 50 / месяц                        │
│  • Цена: 0₽                                     │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│  LITE                                           │
│  • Токенов: 200,000 / месяц                    │
│  • Запросов: 1,000 / месяц                     │
│  • Цена: 199₽                                   │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│  PRO                                            │
│  • Токенов: 1,000,000 / месяц                  │
│  • Запросов: 10,000 / месяц                    │
│  • Цена: 499₽                                   │
└─────────────────────────────────────────────────┘
```

## 🔄 Жизненный цикл пользователя

### 1. Регистрация (первое сообщение)

```sql
INSERT INTO users (
    user_id,
    subscription_type,
    tokens_remaining,
    requests_count
)
VALUES (
    123456789,
    'free',
    15000,
    0
);
```

### 2. Использование (каждый запрос)

```sql
UPDATE users 
SET 
    tokens_used = tokens_used + 1500,
    tokens_remaining = tokens_remaining - 1500,
    requests_count = requests_count + 1,
    last_activity = CURRENT_TIMESTAMP
WHERE user_id = 123456789;
```

### 3. Активация подписки

```sql
UPDATE users 
SET 
    subscription_type = 'pro',
    subscription_start = CURRENT_TIMESTAMP,
    subscription_end = CURRENT_TIMESTAMP + INTERVAL '30 days',
    tokens_used = 0,
    tokens_remaining = 1000000,
    requests_count = 0
WHERE user_id = 123456789;
```

### 4. Истечение подписки

```sql
-- Автоматически проверяется в коде
UPDATE users 
SET 
    subscription_type = 'free',
    subscription_start = NULL,
    subscription_end = NULL,
    tokens_remaining = 15000,
    requests_count = 0
WHERE 
    user_id = 123456789 
    AND subscription_end < CURRENT_TIMESTAMP;
```

## 📊 Аналитические запросы

### Статистика по пользователям

```sql
-- Общее количество пользователей
SELECT COUNT(*) as total_users FROM users;

-- По тарифам
SELECT 
    subscription_type,
    COUNT(*) as count
FROM users 
GROUP BY subscription_type;

-- Активные пользователи (сегодня)
SELECT COUNT(*) 
FROM users 
WHERE last_activity > CURRENT_DATE;
```

### Статистика по токенам

```sql
-- Всего использовано токенов
SELECT SUM(tokens_used) as total_tokens_used FROM users;

-- По тарифам
SELECT 
    subscription_type,
    SUM(tokens_used) as used,
    SUM(tokens_remaining) as remaining,
    AVG(tokens_used) as avg_per_user
FROM users 
GROUP BY subscription_type;

-- Топ-10 пользователей
SELECT 
    full_name,
    tokens_used,
    requests_count,
    subscription_type
FROM users 
ORDER BY tokens_used DESC 
LIMIT 10;
```

### Финансовая аналитика

```sql
-- Доход от активных подписок
SELECT 
    sp.plan_name,
    COUNT(u.id) as active_users,
    sp.price,
    COUNT(u.id) * sp.price as total_revenue
FROM users u
JOIN subscription_plans sp ON u.subscription_type = sp.plan_name
WHERE u.subscription_end > CURRENT_TIMESTAMP
GROUP BY sp.plan_name, sp.price;

-- Потенциальный доход
SELECT 
    subscription_type,
    COUNT(*) as users_count,
    price,
    COUNT(*) * price as potential_revenue
FROM users
JOIN subscription_plans ON users.subscription_type = subscription_plans.plan_name
GROUP BY subscription_type, price;
```

### Retention анализ

```sql
-- Новые пользователи по дням
SELECT 
    DATE(created_at) as date,
    COUNT(*) as new_users
FROM users 
WHERE created_at > CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Активность по дням
SELECT 
    DATE(last_activity) as date,
    COUNT(DISTINCT user_id) as active_users
FROM users 
WHERE last_activity > CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(last_activity)
ORDER BY date DESC;

-- Конверсия в платные тарифы
SELECT 
    COUNT(CASE WHEN subscription_type = 'free' THEN 1 END) as free_users,
    COUNT(CASE WHEN subscription_type IN ('lite', 'pro') THEN 1 END) as paid_users,
    ROUND(
        100.0 * COUNT(CASE WHEN subscription_type IN ('lite', 'pro') THEN 1 END) / 
        COUNT(*), 
        2
    ) as conversion_rate
FROM users;
```

## 🛠️ Maintenance запросы

### Очистка данных

```sql
-- Удалить неактивных бесплатных пользователей (>90 дней)
DELETE FROM users 
WHERE 
    subscription_type = 'free' 
    AND last_activity < CURRENT_TIMESTAMP - INTERVAL '90 days';

-- Архивировать старых пользователей
CREATE TABLE users_archive AS 
SELECT * FROM users 
WHERE last_activity < CURRENT_TIMESTAMP - INTERVAL '180 days';

DELETE FROM users 
WHERE last_activity < CURRENT_TIMESTAMP - INTERVAL '180 days';
```

### Обновление тарифов

```sql
-- Изменить цену тарифа
UPDATE subscription_plans 
SET price = 249.00 
WHERE plan_name = 'lite';

-- Увеличить лимиты
UPDATE subscription_plans 
SET 
    max_tokens = 250000,
    max_requests = 1500
WHERE plan_name = 'lite';
```

## 🔐 Views для упрощения запросов

### Создание полезных представлений

```sql
-- Активные платные пользователи
CREATE VIEW active_paid_users AS
SELECT 
    u.*,
    sp.price,
    (u.subscription_end - CURRENT_TIMESTAMP) as days_left
FROM users u
JOIN subscription_plans sp ON u.subscription_type = sp.plan_name
WHERE 
    u.subscription_end > CURRENT_TIMESTAMP
    AND u.subscription_type != 'free';

-- Статистика по пользователям
CREATE VIEW user_stats AS
SELECT 
    u.user_id,
    u.full_name,
    u.subscription_type,
    u.tokens_used,
    u.tokens_remaining,
    u.requests_count,
    sp.max_tokens,
    sp.max_requests,
    ROUND(100.0 * u.tokens_used / sp.max_tokens, 2) as tokens_usage_percent,
    ROUND(100.0 * u.requests_count / sp.max_requests, 2) as requests_usage_percent
FROM users u
JOIN subscription_plans sp ON u.subscription_type = sp.plan_name;
```

### Использование views

```sql
-- Просмотр активных платных подписок
SELECT * FROM active_paid_users 
ORDER BY days_left ASC;

-- Пользователи с высоким использованием
SELECT * FROM user_stats 
WHERE tokens_usage_percent > 80 OR requests_usage_percent > 80;
```

## 📈 Мониторинг производительности

### Анализ размера таблиц

```sql
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Использование индексов

```sql
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;
```

---

**Полная схема базы данных SmartBot AI готова для работы в pgAdmin 4!** 🎉





