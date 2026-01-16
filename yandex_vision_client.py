import jwt
import time
import requests
import logging
import base64
from datetime import datetime, timedelta
from config import Config

logger = logging.getLogger(__name__)

class YandexVisionClient:
    def __init__(self):
        self.folder_id = Config.YANDEX_FOLDER_ID
        
        # Поддержка нескольких аккаунтов для распределения нагрузки
        self.accounts = []
        
        # Первый аккаунт
        if Config.YANDEX_SERVICE_ACCOUNT_ID and Config.YANDEX_API_KEY_ID and Config.YANDEX_API_SECRET_KEY:
            self.accounts.append({
                'service_account_id': Config.YANDEX_SERVICE_ACCOUNT_ID,
                'key_id': Config.YANDEX_API_KEY_ID,
                'secret_key': Config.YANDEX_API_SECRET_KEY.replace('\\n', '\n'),
                'iam_token': None,
                'token_expires_at': None
            })
        
        # Второй аккаунт
        if Config.YANDEX_SERVICE_ACCOUNT_ID_2 and Config.YANDEX_API_KEY_ID_2 and Config.YANDEX_API_SECRET_KEY_2:
            self.accounts.append({
                'service_account_id': Config.YANDEX_SERVICE_ACCOUNT_ID_2,
                'key_id': Config.YANDEX_API_KEY_ID_2,
                'secret_key': Config.YANDEX_API_SECRET_KEY_2.replace('\\n', '\n'),
                'iam_token': None,
                'token_expires_at': None
            })
        
        # Третий аккаунт
        if Config.YANDEX_SERVICE_ACCOUNT_ID_3 and Config.YANDEX_API_KEY_ID_3 and Config.YANDEX_API_SECRET_KEY_3:
            self.accounts.append({
                'service_account_id': Config.YANDEX_SERVICE_ACCOUNT_ID_3,
                'key_id': Config.YANDEX_API_KEY_ID_3,
                'secret_key': Config.YANDEX_API_SECRET_KEY_3.replace('\\n', '\n'),
                'iam_token': None,
                'token_expires_at': None
            })
        
        if not self.accounts:
            logger.warning("⚠️ Нет доступных аккаунтов Yandex Vision!")
        else:
            logger.info(f"✅ Инициализировано {len(self.accounts)} аккаунтов Yandex Vision для распределения нагрузки")
        
        self.current_account_index = 0

    def _get_next_account(self) -> dict:
        """Возвращает следующий аккаунт по кругу (round-robin)"""
        if not self.accounts:
            return None
        
        account = self.accounts[self.current_account_index]
        self.current_account_index = (self.current_account_index + 1) % len(self.accounts)
        return account

    def _get_iam_token(self, account: dict) -> str:
        """
        Получает IAM-токен для аутентификации в Yandex Cloud.
        Токен кешируется и обновляется по истечении срока действия.
        """
        if account['iam_token'] and account['token_expires_at'] and account['token_expires_at'] > datetime.now():
            return account['iam_token']

        logger.info(f"IAM-токен устарел или отсутствует для аккаунта {account['service_account_id'][:10]}... Получение нового токена...")
        
        now = int(time.time())
        payload = {
            'aud': 'https://iam.api.cloud.yandex.net/iam/v1/tokens',
            'iss': account['service_account_id'],
            'iat': now,
            'exp': now + 3600  # Токен живет 1 час
        }

        try:
            # Формируем JWT
            encoded_token = jwt.encode(
                payload,
                account['secret_key'],
                algorithm='PS256',
                headers={'kid': account['key_id']}
            )
            
            response = requests.post(
                'https://iam.api.cloud.yandex.net/iam/v1/tokens',
                json={'jwt': encoded_token}
            )
            response.raise_for_status()
            data = response.json()
            
            account['iam_token'] = data['iamToken']
            # Устанавливаем время истечения с запасом в 1 минуту
            account['token_expires_at'] = datetime.now() + timedelta(hours=1, minutes=-1)
            logger.info(f"✅ Новый IAM-токен успешно получен для аккаунта {account['service_account_id'][:10]}...")
            
            return account['iam_token']
            
        except ValueError as e:
            logger.error(f"Ошибка формирования JWT. Скорее всего, неверный формат приватного ключа. Ошибка: {e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка получения IAM-токена: {e}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка при получении IAM-токена: {e}")
            return None

    def recognize_text(self, image_url: str) -> str:
        """
        Распознает текст на изображении по URL.
        Использует round-robin распределение между доступными аккаунтами.
        """
        logger.info(f"Начинаю распознавание текста для URL: {image_url}")
        
        # Получаем следующий аккаунт для распределения нагрузки
        account = self._get_next_account()
        if not account:
            return "Ошибка: не настроены аккаунты Yandex Vision API."
        
        account_idx = self.accounts.index(account)
        logger.info(f"🔄 Используется аккаунт #{account_idx + 1} из {len(self.accounts)} для распределения нагрузки")
        
        iam_token = self._get_iam_token(account)
        if not iam_token:
            return "Ошибка: не удалось авторизоваться в Yandex Vision. Проверьте, что YANDEX_API_SECRET_KEY в файле config.env содержит корректный PEM-ключ."

        try:
            # Скачиваем изображение
            image_response = requests.get(image_url, timeout=20)
            image_response.raise_for_status()
            image_content = image_response.content
            
            # Определяем MIME тип по заголовкам или расширению
            content_type = image_response.headers.get('Content-Type', '')
            if 'png' in content_type.lower() or image_url.lower().endswith('.png'):
                mime_type = "PNG"
            elif 'jpeg' in content_type.lower() or 'jpg' in content_type.lower() or image_url.lower().endswith(('.jpg', '.jpeg')):
                mime_type = "JPEG"
            else:
                mime_type = "JPEG"  # По умолчанию
            
            # Кодируем в Base64
            encoded_content = base64.b64encode(image_content).decode('utf-8')
            
            headers = {
                'Authorization': f'Bearer {iam_token}',
                'x-folder-id': self.folder_id,
                'Content-Type': 'application/json'
            }
            
            body = {
                "mimeType": mime_type,
                "languageCodes": ["*"],  # Все языки
                # Убираем model - используем дефолтную модель для лучшего качества
                "content": encoded_content
            }
            
            # Логируем информацию об изображении
            import struct
            if len(image_content) > 2:
                # Пытаемся определить размер изображения из заголовка
                if image_content[:2] == b'\xff\xd8':  # JPEG
                    logger.info(f"📸 JPEG изображение, размер файла: {len(image_content)} байт")
                elif image_content[:8] == b'\x89PNG\r\n\x1a\n':  # PNG
                    logger.info(f"📸 PNG изображение, размер файла: {len(image_content)} байт")
                else:
                    logger.info(f"📸 Изображение, размер файла: {len(image_content)} байт")
            else:
                logger.warning(f"⚠️ Изображение слишком маленькое: {len(image_content)} байт")
            
            # Отправляем запрос на распознавание
            ocr_response = requests.post(
                'https://ocr.api.cloud.yandex.net/ocr/v1/recognizeText',
                headers=headers,
                json=body,
                timeout=30
            )
            
            if ocr_response.status_code == 200:
                result = ocr_response.json().get('result', {})
                text_annotation = result.get('textAnnotation', {})
                full_text = text_annotation.get('fullText', '')
                
                # Логируем распознанный текст для отладки
                logger.info(f"✅ Текст успешно распознан (аккаунт #{account_idx + 1}). Длина: {len(full_text)} символов.")
                if full_text:
                    logger.debug(f"📝 Распознанный текст: {full_text[:200]}...")  # Первые 200 символов
                
                # Если текст пустой, пробуем получить из blocks
                if not full_text and 'blocks' in text_annotation:
                    blocks_text = []
                    for block in text_annotation.get('blocks', []):
                        for line in block.get('lines', []):
                            for word in line.get('words', []):
                                word_text = word.get('text', '')
                                if word_text:
                                    blocks_text.append(word_text)
                    if blocks_text:
                        full_text = ' '.join(blocks_text)
                        logger.info(f"📝 Текст восстановлен из blocks: {len(full_text)} символов")
                
                return full_text if full_text else "Не удалось распознать текст на изображении."
            else:
                # Детальное логирование ошибки
                error_text = ocr_response.text
                logger.error(f"❌ Ошибка Yandex Vision API: {ocr_response.status_code}")
                logger.error(f"📄 Ответ API: {error_text[:1000]}")  # Первые 1000 символов
                
                # Пытаемся распарсить JSON ошибки
                error_message = "Неизвестная ошибка"
                try:
                    error_json = ocr_response.json()
                    error_message = error_json.get('message', error_json.get('error', 'Неизвестная ошибка'))
                    error_code = error_json.get('code', error_json.get('error_code', ''))
                    logger.error(f"🔍 Код ошибки: {error_code}, Сообщение: {error_message}")
                except Exception as parse_error:
                    # Если не JSON, пытаемся извлечь информацию из текста
                    logger.error(f"⚠️ Не удалось распарсить JSON ошибки: {parse_error}")
                    if error_text:
                        # Пытаемся найти сообщение об ошибке в тексте
                        if 'message' in error_text.lower() or 'error' in error_text.lower():
                            error_message = error_text[:200]  # Первые 200 символов
                        else:
                            error_message = f"HTTP {ocr_response.status_code}: {error_text[:200]}"
                
                return f"Ошибка распознавания: {error_message}"

        except requests.exceptions.Timeout:
            logger.error("Тайм-аут при скачивании изображения или запросе к OCR.")
            return "Ошибка: слишком долгое ожидание ответа при обработке изображения."
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка сети при обработке изображения: {e}")
            return "Ошибка: не удалось загрузить или обработать изображение."
        except Exception as e:
            logger.error(f"Неожиданная ошибка в recognize_text: {e}")
            return "Произошла непредвиденная ошибка при распознавании текста."
