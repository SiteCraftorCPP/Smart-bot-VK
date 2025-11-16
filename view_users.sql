-- Просмотр всех пользователей с актуальными данными
SELECT 
    user_id,
    full_name,
    profile_link,
    subscription_type,
    tokens_used,
    tokens_remaining,
    requests_count,
    last_activity,
    created_at
FROM users
ORDER BY last_activity DESC;

-- Просмотр конкретного пользователя (замените USER_ID на нужный)
-- SELECT * FROM users WHERE user_id = 782498140;

-- Статистика по подпискам
SELECT 
    subscription_type,
    COUNT(*) as users_count,
    SUM(tokens_used) as total_tokens_used,
    AVG(tokens_remaining) as avg_tokens_remaining
FROM users
GROUP BY subscription_type;



