import psycopg2
from psycopg2 import pool, extras
from config import Config
import logging
import json
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.use_postgres = True
        self.users_file = "users.json"
        self.connection_pool = None
        
        try:
            # Создаем пул соединений PostgreSQL
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                1,  # минимум соединений
                10, # максимум соединений
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME
            )
            
            if self.connection_pool:
                logger.info("✅ Пул соединений PostgreSQL успешно создан.")
                self._init_database()
            
        except (Exception, psycopg2.DatabaseError) as err:
            logger.warning(f"⚠️ Не удалось подключиться к PostgreSQL: {err}")
            logger.info("🔄 Переключаемся на файловое хранилище users.json")
            self.use_postgres = False
            self._init_json_storage()

    def _init_database(self):
        """Инициализация базы данных - создание таблиц"""
        conn = self.get_connection()
        if not conn:
            return
        
        try:
            cursor = conn.cursor()
            
            # --- Миграция схемы ---
            # Проверяем и добавляем столбцы в subscription_plans
            cursor.execute("ALTER TABLE subscription_plans ADD COLUMN IF NOT EXISTS deepseek_max_requests INTEGER;")
            cursor.execute("ALTER TABLE subscription_plans ADD COLUMN IF NOT EXISTS yandex_max_requests INTEGER;")
            
            # Проверяем и добавляем столбцы в users
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS yandex_requests_count INTEGER DEFAULT 0;")
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS admin_unlimited BOOLEAN DEFAULT FALSE;")
            
            # --- Создание таблиц (если их нет) ---
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS subscription_plans (
                    id SERIAL PRIMARY KEY,
                    plan_name VARCHAR(50) UNIQUE NOT NULL,
                    max_tokens INTEGER,
                    price DECIMAL(10, 2) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Обновляем структуру, если поля все еще отсутствуют 
            # (на случай, если таблица была создана только что)
            cursor.execute("ALTER TABLE subscription_plans ADD COLUMN IF NOT EXISTS deepseek_max_requests INTEGER;")
            cursor.execute("ALTER TABLE subscription_plans ADD COLUMN IF NOT EXISTS yandex_max_requests INTEGER;")

            # Создаем таблицу пользователей
            cursor.execute("""
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
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    admin_unlimited BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # И здесь тоже добавляем поле, если таблица только что создана
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS yandex_requests_count INTEGER DEFAULT 0;")
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS admin_unlimited BOOLEAN DEFAULT FALSE;")
            
            # Создаем индексы
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON users(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_subscription_type ON users(subscription_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_last_activity ON users(last_activity)")
            
            # Вставляем/Обновляем тарифные планы
            cursor.execute("""
                INSERT INTO subscription_plans (plan_name, max_tokens, deepseek_max_requests, yandex_max_requests, price) 
                VALUES 
                    ('free', NULL, 5, 2, 0.00),
                    ('lite', 250000, NULL, 10, 149.00),
                    ('premium', 1000000, NULL, 50, 299.00)
                ON CONFLICT (plan_name) DO UPDATE SET
                    max_tokens = EXCLUDED.max_tokens,
                    deepseek_max_requests = EXCLUDED.deepseek_max_requests,
                    yandex_max_requests = EXCLUDED.yandex_max_requests,
                    price = EXCLUDED.price,
                    updated_at = CURRENT_TIMESTAMP
            """)
            
            conn.commit()
            logger.info("✅ База данных инициализирована и структура обновлена.")
            
        except (Exception, psycopg2.DatabaseError) as err:
            logger.error(f"❌ Ошибка инициализации БД: {err}")
            conn.rollback()
        finally:
            cursor.close()
            self.put_connection(conn)

    def _init_json_storage(self):
        """Инициализация JSON хранилища"""
        if not os.path.exists(self.users_file):
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
            logger.info(f"📄 Создан файл {self.users_file}")

    def _load_users(self):
        """Загружает пользователей из JSON файла"""
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_users(self, users):
        """Сохраняет пользователей в JSON файл"""
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(users, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения в JSON: {e}")
            return False

    def get_connection(self):
        """Получает соединение из пула"""
        if not self.use_postgres or not self.connection_pool:
            return None
        try:
            return self.connection_pool.getconn()
        except (Exception, psycopg2.DatabaseError) as err:
            logger.error(f"❌ Не удалось получить соединение из пула: {err}")
            return None

    def put_connection(self, conn):
        """Возвращает соединение в пул"""
        if conn and self.connection_pool:
            self.connection_pool.putconn(conn)

    def get_user(self, user_id):
        """Получает данные пользователя из БД или JSON"""
        if not self.use_postgres:
            users = self._load_users()
            user_data = users.get(str(user_id))
            if user_data:
                # Конвертируем строки дат обратно в datetime объекты
                for key in ['subscription_start', 'subscription_end', 'last_activity', 'created_at']:
                    if key in user_data and user_data[key]:
                        try:
                            user_data[key] = datetime.fromisoformat(user_data[key])
                        except:
                            pass
            return user_data
            
        conn = self.get_connection()
        if not conn:
            return None
            
        try:
            cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
            cursor.execute("""
                SELECT * FROM users WHERE user_id = %s
            """, (user_id,))
            user_data = cursor.fetchone()
            cursor.close()
            
            if user_data:
                return dict(user_data)
            return None
            
        except (Exception, psycopg2.DatabaseError) as err:
            logger.error(f"❌ Ошибка получения пользователя {user_id}: {err}")
            return None
        finally:
            self.put_connection(conn)

    def create_user(self, user_id):
        """Создает нового пользователя в БД или JSON"""
        if not self.use_postgres:
            users = self._load_users()
            if str(user_id) not in users:
                users[str(user_id)] = {
                    'user_id': user_id,
                    'subscription_type': 'free',
                    'subscription_start': None,
                    'subscription_end': None,
                    'tokens_used': 0,
                    'tokens_remaining': 15000,
                    'requests_count': 0,
                    'yandex_requests_count': 0,
                    'admin_unlimited': False,
                    'phone_number': None,
                    'created_at': datetime.now().isoformat(),
                    'last_activity': datetime.now().isoformat(),
                    'full_name': None,
                    'profile_link': None
                }
                self._save_users(users)
                logger.info(f"✅ Создан новый пользователь с ID: {user_id}")
            return users.get(str(user_id))
            
        conn = self.get_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
            cursor.execute("""
                INSERT INTO users (user_id, subscription_type, tokens_remaining, requests_count, yandex_requests_count, last_activity)
                VALUES (%s, 'free', 15000, 0, 0, CURRENT_TIMESTAMP)
                RETURNING *
            """, (user_id,))
            
            user_data = cursor.fetchone()
            conn.commit()
            cursor.close()
            
            logger.info(f"✅ Создан новый пользователь с ID: {user_id}")
            return dict(user_data) if user_data else None
            
        except psycopg2.IntegrityError:
            conn.rollback()
            logger.warning(f"⚠️ Попытка создать дублирующегося пользователя с ID: {user_id}")
            return self.get_user(user_id)
        except (Exception, psycopg2.DatabaseError) as err:
            conn.rollback()
            logger.error(f"❌ Ошибка создания пользователя {user_id}: {err}")
            return None
        finally:
            self.put_connection(conn)

    def update_user(self, user_id, **kwargs):
        """Обновляет данные пользователя в БД или JSON"""
        if not self.use_postgres:
            users = self._load_users()
            if str(user_id) in users:
                # Конвертируем datetime объекты в строки
                for key, value in kwargs.items():
                    if isinstance(value, datetime):
                        kwargs[key] = value.isoformat()
                
                users[str(user_id)].update(kwargs)
                users[str(user_id)]['last_activity'] = datetime.now().isoformat()
                self._save_users(users)
                logger.info(f"✅ Данные пользователя {user_id} обновлены: {kwargs}")
                return True
            return False
            
        conn = self.get_connection()
        if not conn:
            return False
            
        fields = []
        values = []
        
        # Всегда обновляем last_activity
        kwargs['last_activity'] = datetime.now()
        
        for key, value in kwargs.items():
            fields.append(f"{key} = %s")
            values.append(value)
        
        if not fields:
            return False
            
        values.append(user_id)
        
        try:
            cursor = conn.cursor()
            update_query = f"UPDATE users SET {', '.join(fields)} WHERE user_id = %s"
            cursor.execute(update_query, tuple(values))
            conn.commit()
            cursor.close()
            
            logger.info(f"✅ Данные пользователя {user_id} обновлены")
            return True
            
        except (Exception, psycopg2.DatabaseError) as err:
            conn.rollback()
            logger.error(f"❌ Ошибка обновления пользователя {user_id}: {err}")
            return False
        finally:
            self.put_connection(conn)
    
    def get_subscription_plans(self):
        """Получает все тарифные планы из БД или возвращает по умолчанию"""
        if not self.use_postgres:
            # Возвращаем планы по умолчанию для JSON режима
            return {
                'free': {'max_tokens': None, 'deepseek_max_requests': 5, 'yandex_max_requests': 2, 'price': 0},
                'lite': {'max_tokens': 250000, 'deepseek_max_requests': None, 'yandex_max_requests': 10, 'price': 149},
                'premium': {'max_tokens': 1000000, 'deepseek_max_requests': None, 'yandex_max_requests': 50, 'price': 299}
            }
            
        conn = self.get_connection()
        if not conn:
            return {}
            
        try:
            cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
            cursor.execute("SELECT * FROM subscription_plans")
            plans_list = cursor.fetchall()
            cursor.close()
            
            plans = {}
            for plan in plans_list:
                plan_dict = dict(plan)
                plans[plan_dict['plan_name']] = {
                    'max_tokens': plan_dict.get('max_tokens'),
                    'deepseek_max_requests': plan_dict.get('deepseek_max_requests'),
                    'yandex_max_requests': plan_dict.get('yandex_max_requests'),
                    'price': float(plan_dict['price'])
                }
            
            return plans
            
        except (Exception, psycopg2.DatabaseError) as err:
            logger.error(f"❌ Ошибка получения тарифных планов: {err}")
            return {}
        finally:
            self.put_connection(conn)

    def update_user_profile(self, user_id, full_name=None, profile_link=None, phone_number=None):
        """Обновляет профильную информацию пользователя"""
        update_data = {}
        if full_name:
            update_data['full_name'] = full_name
        if profile_link:
            update_data['profile_link'] = profile_link
        if phone_number:
            update_data['phone_number'] = phone_number
        
        if update_data:
            return self.update_user(user_id, **update_data)
        return True

    def add_tokens(self, user_id: int, amount: int) -> bool:
        """Добавляет токены пользователю"""
        user = self.get_user(user_id)
        if not user:
            return False
        
        current_tokens = user.get('tokens_remaining', 0) or 0
        new_tokens = current_tokens + amount
        
        return self.update_user(user_id, tokens_remaining=new_tokens)
    
    def add_photo_requests(self, user_id: int, amount: int) -> bool:
        """Добавляет фото-запросы пользователю (увеличивает лимит Yandex)"""
        # Для этого мы будем хранить дополнительное поле purchased_photo_requests
        conn = self.get_connection()
        if not conn:
            # Для JSON режима
            if not self.use_postgres:
                users = self._load_users()
                user_id_str = str(user_id)
                if user_id_str in users:
                    current = users[user_id_str].get('purchased_photo_requests', 0) or 0
                    users[user_id_str]['purchased_photo_requests'] = current + amount
                    return self._save_users(users)
            return False
        
        try:
            cursor = conn.cursor()
            
            # Добавляем столбец если его нет
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS purchased_photo_requests INTEGER DEFAULT 0;")
            
            # Обновляем значение
            cursor.execute("""
                UPDATE users 
                SET purchased_photo_requests = COALESCE(purchased_photo_requests, 0) + %s,
                    last_activity = CURRENT_TIMESTAMP
                WHERE user_id = %s
            """, (amount, user_id))
            
            conn.commit()
            cursor.close()
            return True
            
        except (Exception, psycopg2.DatabaseError) as err:
            conn.rollback()
            logger.error(f"❌ Ошибка добавления фото-запросов пользователю {user_id}: {err}")
            return False
        finally:
            self.put_connection(conn)
    
    def close(self):
        """Закрывает все соединения в пуле"""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("🔒 Пул соединений PostgreSQL закрыт")

# Создаем один экземпляр на весь проект
db_manager = DatabaseManager()
