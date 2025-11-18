import requests
import uuid
import logging
from typing import Optional, Dict, Any
from config import Config

logger = logging.getLogger(__name__)

class YooKassaClient:
    """Клиент для работы с ЮКасса API"""
    
    def __init__(self):
        self.shop_id = str(Config.YOOKASSA_SHOP_ID).strip() if Config.YOOKASSA_SHOP_ID else None
        self.api_key = str(Config.YOOKASSA_API_KEY).strip() if Config.YOOKASSA_API_KEY else None
        self.base_url = "https://api.yookassa.ru/v3"
        
        # Детальное логирование для диагностики
        logger.info(f"Инициализация YooKassaClient:")
        logger.info(f"  Shop ID: {self.shop_id[:4] + '***' if self.shop_id and len(self.shop_id) > 4 else 'НЕ УСТАНОВЛЕН'}")
        logger.info(f"  API Key: {self.api_key[:10] + '***' if self.api_key and len(self.api_key) > 10 else 'НЕ УСТАНОВЛЕН'}")
        
        # Проверяем наличие обязательных параметров
        if not self.shop_id or self.shop_id == '000000' or self.shop_id == 'None':
            logger.error("❌ YOOKASSA_SHOP_ID не настроен или равен 000000!")
            logger.error("   Проверьте config.env - должно быть: YOOKASSA_SHOP_ID=1189237")
        if not self.api_key or self.api_key == 'None':
            logger.error("❌ YOOKASSA_API_KEY не настроен!")
            logger.error("   Проверьте config.env - должен быть указан полный ключ")
        
    def create_payment(self, amount: float, description: str, user_id: int, payment_type: str) -> Optional[Dict]:
        """
        Создает платеж в ЮКассе
        
        Args:
            amount: Сумма платежа в рублях
            description: Описание платежа
            user_id: ID пользователя VK
            payment_type: Тип платежа (lite/premium/tokens/photo)
            
        Returns:
            Словарь с данными платежа или None при ошибке
        """
        try:
            # Проверяем наличие обязательных параметров перед запросом
            if not self.shop_id or self.shop_id == '000000' or self.shop_id == 'None':
                logger.error("❌ Shop ID не настроен! Невозможно создать платеж.")
                return None
            if not self.api_key or self.api_key == 'None':
                logger.error("❌ API Key не настроен! Невозможно создать платеж.")
                return None
            
            idempotence_key = str(uuid.uuid4())
            
            payload = {
                "amount": {
                    "value": f"{amount:.2f}",
                    "currency": "RUB"
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": "https://vk.com/im"
                },
                "capture": True,
                "description": description,
                "metadata": {
                    "user_id": str(user_id),
                    "payment_type": payment_type
                },
                "receipt": {
                    "customer": {
                        "email": f"user_{user_id}@vk.bot"
                    },
                    "items": [
                        {
                            "description": description,
                            "quantity": "1",
                            "amount": {
                                "value": f"{amount:.2f}",
                                "currency": "RUB"
                            },
                            "vat_code": 1  # НДС не облагается
                        }
                    ]
                }
            }
            
            headers = {
                "Idempotence-Key": idempotence_key,
                "Content-Type": "application/json"
            }
            
            # Логируем запрос (без чувствительных данных)
            logger.info(f"Создание платежа: сумма={amount}₽, тип={payment_type}, user_id={user_id}")
            logger.debug(f"Shop ID: {self.shop_id}, API Key: {self.api_key[:15]}...")
            
            response = requests.post(
                f"{self.base_url}/payments",
                json=payload,
                headers=headers,
                auth=(self.shop_id, self.api_key),
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                payment_data = response.json()
                logger.info(f"Создан платеж {payment_data['id']} для пользователя {user_id}")
                return payment_data
            else:
                error_text = response.text
                logger.error(f"Ошибка создания платежа: {response.status_code}")
                logger.error(f"Ответ от API: {error_text}")
                
                # Пытаемся распарсить JSON ответ для более детальной информации
                try:
                    error_json = response.json()
                    error_type = error_json.get('type', 'unknown')
                    error_code = error_json.get('code', 'unknown')
                    error_description = error_json.get('description', 'Нет описания')
                    
                    logger.error(f"Тип ошибки: {error_type}")
                    logger.error(f"Код ошибки: {error_code}")
                    logger.error(f"Описание: {error_description}")
                except:
                    pass
                
                # Более детальная обработка ошибок
                if response.status_code == 401:
                    logger.error("=" * 60)
                    logger.error("❌ ОШИБКА АУТЕНТИФИКАЦИИ ЮКАССЫ (401)")
                    logger.error("=" * 60)
                    logger.error("Возможные причины:")
                    logger.error("1. Shop ID неверный или не соответствует API ключу")
                    logger.error("2. API ключ неверный, истек или был удален")
                    logger.error("3. Shop ID и API ключ от разных аккаунтов (test/live)")
                    logger.error("")
                    logger.error("Текущие значения:")
                    logger.error(f"  Shop ID: {self.shop_id}")
                    logger.error(f"  API Key: {self.api_key[:20]}..." if self.api_key else "  API Key: НЕ УСТАНОВЛЕН")
                    logger.error("")
                    logger.error("Что проверить:")
                    logger.error("1. В личном кабинете ЮКассы → Настройки → Общие настройки")
                    logger.error("   Убедитесь, что Shop ID совпадает с указанным в config.env")
                    logger.error("2. В личном кабинете ЮКассы → Настройки → API ключи")
                    logger.error("   Убедитесь, что используете СЕКРЕТНЫЙ ключ (Secret Key), а не публичный")
                    logger.error("   Проверьте, что ключ активен и не истек")
                    logger.error("3. Если используете live_ ключ, убедитесь, что магазин активирован для продакшена")
                    logger.error("4. Если используете test_ ключ, убедитесь, что Shop ID тоже от тестового аккаунта")
                    logger.error("=" * 60)
                
                return None
                
        except Exception as e:
            logger.error(f"Исключение при создании платежа: {e}")
            return None
    
    def check_payment_status(self, payment_id: str) -> Optional[Dict]:
        """
        Проверяет статус платежа
        
        Args:
            payment_id: ID платежа в ЮКассе
            
        Returns:
            Словарь с данными платежа или None при ошибке
        """
        try:
            response = requests.get(
                f"{self.base_url}/payments/{payment_id}",
                auth=(self.shop_id, self.api_key),
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Ошибка проверки статуса платежа: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Исключение при проверке статуса платежа: {e}")
            return None
    
    def is_payment_succeeded(self, payment_id: str) -> bool:
        """
        Проверяет, успешно ли завершен платеж
        
        Args:
            payment_id: ID платежа в ЮКассе
            
        Returns:
            True если платеж успешен, False иначе
        """
        payment_data = self.check_payment_status(payment_id)
        if payment_data:
            return payment_data.get('status') == 'succeeded'
        return False

