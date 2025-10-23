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
        self.service_account_id = Config.YANDEX_SERVICE_ACCOUNT_ID
        self.key_id = Config.YANDEX_API_KEY_ID
        # Заменяем \\n на \n для корректного чтения ключа из .env
        self.secret_key = Config.YANDEX_API_SECRET_KEY.replace('\\n', '\n')
        self.iam_token = None
        self.token_expires_at = None

    def _get_iam_token(self) -> str:
        """
        Получает IAM-токен для аутентификации в Yandex Cloud.
        Токен кешируется и обновляется по истечении срока действия.
        """
        if self.iam_token and self.token_expires_at and self.token_expires_at > datetime.now():
            return self.iam_token

        logger.info("IAM-токен устарел или отсутствует. Получение нового токена...")
        
        now = int(time.time())
        payload = {
            'aud': 'https://iam.api.cloud.yandex.net/iam/v1/tokens',
            'iss': self.service_account_id, # Должен быть ID сервисного аккаунта
            'iat': now,
            'exp': now + 3600  # Токен живет 1 час
        }

        try:
            # Формируем JWT
            encoded_token = jwt.encode(
                payload,
                self.secret_key,
                algorithm='PS256',
                headers={'kid': self.key_id} # А здесь ID ключа
            )
            
            response = requests.post(
                'https://iam.api.cloud.yandex.net/iam/v1/tokens',
                json={'jwt': encoded_token}
            )
            response.raise_for_status()
            data = response.json()
            
            self.iam_token = data['iamToken']
            # Устанавливаем время истечения с запасом в 1 минуту
            self.token_expires_at = datetime.now() + timedelta(hours=1, minutes=-1) 
            logger.info("Новый IAM-токен успешно получен.")
            
            return self.iam_token
            
        except ValueError as e:
            logger.error(f"Ошибка формирования JWT. Скорее всего, неверный формат приватного ключа в YANDEX_API_SECRET_KEY. Ошибка: {e}")
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
        """
        logger.info(f"Начинаю распознавание текста для URL: {image_url}")
        
        iam_token = self._get_iam_token()
        if not iam_token:
            return "Ошибка: не удалось авторизоваться в Yandex Vision. Проверьте, что YANDEX_API_SECRET_KEY в файле config.env содержит корректный PEM-ключ."

        try:
            # Скачиваем изображение
            image_response = requests.get(image_url, timeout=20)
            image_response.raise_for_status()
            image_content = image_response.content
            
            # Кодируем в Base64
            encoded_content = base64.b64encode(image_content).decode('utf-8')
            
            headers = {
                'Authorization': f'Bearer {iam_token}',
                'x-folder-id': self.folder_id,
                'Content-Type': 'application/json'
            }
            
            body = {
                "mimeType": "JPEG", # VK обычно отдает в JPG
                "languageCodes": ["*"],
                "model": "page",
                "content": encoded_content
            }
            
            # Отправляем запрос на распознавание
            ocr_response = requests.post(
                'https://ocr.api.cloud.yandex.net/ocr/v1/recognizeText',
                headers=headers,
                json=body,
                timeout=30
            )
            
            if ocr_response.status_code == 200:
                result = ocr_response.json().get('result', {})
                full_text = result.get('textAnnotation', {}).get('fullText', '')
                logger.info(f"Текст успешно распознан. Длина: {len(full_text)} символов.")
                return full_text
            else:
                logger.error(f"Ошибка Yandex Vision API: {ocr_response.status_code} - {ocr_response.text}")
                return f"Ошибка распознавания: {ocr_response.json().get('message', 'Неизвестная ошибка')}"

        except requests.exceptions.Timeout:
            logger.error("Тайм-аут при скачивании изображения или запросе к OCR.")
            return "Ошибка: слишком долгое ожидание ответа при обработке изображения."
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка сети при обработке изображения: {e}")
            return "Ошибка: не удалось загрузить или обработать изображение."
        except Exception as e:
            logger.error(f"Неожиданная ошибка в recognize_text: {e}")
            return "Произошла непредвиденная ошибка при распознавании текста."
