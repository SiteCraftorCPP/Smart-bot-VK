"""
Webhook для приема уведомлений от ЮКассы
"""
from flask import Flask, request, jsonify
import logging
from user_manager import UserManager
from yookassa_client import YooKassaClient

logger = logging.getLogger(__name__)

app = Flask(__name__)
user_manager = UserManager()
yookassa = YooKassaClient()

@app.route('/yookassa/webhook', methods=['POST'])
def yookassa_webhook():
    """
    Обработчик webhook от ЮКассы
    Вызывается автоматически при изменении статуса платежа
    """
    try:
        data = request.json
        logger.info(f"Получен webhook от ЮКассы: {data}")
        
        # Проверяем тип события
        event_type = data.get('event')
        if event_type != 'payment.succeeded':
            logger.info(f"Игнорируем событие типа: {event_type}")
            return jsonify({'status': 'ok'}), 200
        
        # Получаем данные платежа
        payment = data.get('object')
        if not payment:
            logger.error("Нет объекта платежа в webhook")
            return jsonify({'status': 'error', 'message': 'No payment object'}), 400
        
        payment_id = payment.get('id')
        status = payment.get('status')
        metadata = payment.get('metadata', {})
        
        if status != 'succeeded':
            logger.info(f"Платеж {payment_id} не в статусе succeeded: {status}")
            return jsonify({'status': 'ok'}), 200
        
        # Извлекаем данные пользователя
        user_id = int(metadata.get('user_id'))
        payment_type = metadata.get('payment_type')
        
        if not user_id or not payment_type:
            logger.error(f"Нет user_id или payment_type в metadata платежа {payment_id}")
            return jsonify({'status': 'error', 'message': 'Missing metadata'}), 400
        
        # Обрабатываем платеж в зависимости от типа
        logger.info(f"Обрабатываем платеж {payment_id} для пользователя {user_id}, тип: {payment_type}")
        
        if payment_type == 'tokens':
            # Добавляем 150.000 токенов
            if user_manager.add_tokens(user_id, 150000):
                logger.info(f"✅ Пользователю {user_id} начислено 150.000 токенов")
            else:
                logger.error(f"❌ Ошибка начисления токенов пользователю {user_id}")
                
        elif payment_type == 'photo':
            # Добавляем 30 фото-запросов
            if user_manager.add_photo_requests(user_id, 30):
                logger.info(f"✅ Пользователю {user_id} начислено 30 фото-запросов")
            else:
                logger.error(f"❌ Ошибка начисления фото-запросов пользователю {user_id}")
                
        elif payment_type in ['lite', 'premium']:
            # Активируем подписку
            if user_manager.activate_subscription(user_id, payment_type, 30):
                logger.info(f"✅ Пользователю {user_id} активирована подписка {payment_type}")
            else:
                logger.error(f"❌ Ошибка активации подписки {payment_type} для пользователя {user_id}")
        else:
            logger.warning(f"Неизвестный тип платежа: {payment_type}")
        
        return jsonify({'status': 'ok'}), 200
        
    except Exception as e:
        logger.error(f"Ошибка обработки webhook: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    # Запуск в режиме отладки (в продакшне использовать gunicorn или аналог)
    app.run(host='0.0.0.0', port=5000, debug=False)

