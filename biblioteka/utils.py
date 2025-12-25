# biblioteka/utils.py
import base64
import requests
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


def get_yookassa_auth_headers():
    """Возвращает заголовки для авторизации в ЮKassa"""
    shop_id = settings.YOOKASSA_SHOP_ID
    secret_key = settings.YOOKASSA_SECRET_KEY
    auth = f"{shop_id}:{secret_key}"
    basic_auth = base64.b64encode(auth.encode('utf-8')).decode('utf-8')

    return {
        "Authorization": f"Basic {basic_auth}",
        "Content-Type": "application/json"
    }


def check_yookassa_payment_status(payment_id):
    """
    Проверяет статус платежа через API ЮKassa
    Возвращает: 'succeeded', 'canceled', 'pending' или None
    """
    if not payment_id:
        return None

    try:
        url = f"https://api.yookassa.ru/v3/payments/{payment_id}"
        headers = get_yookassa_auth_headers()

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            payment = response.json()
            return payment.get('status')
        elif response.status_code == 404:
            print(f"Платеж {payment_id} не найден в ЮKassa")
        else:
            print(f"Ошибка API ЮKassa: {response.status_code} - {response.text[:200]}")

    except requests.exceptions.RequestException as e:
        print(f"Ошибка соединения с ЮKassa: {e}")
    except Exception as e:
        print(f"Ошибка проверки статуса платежа: {e}")

    return None


def update_fine_status_from_yookassa(fine):
    """
    Обновляет статус штрафа на основе данных из ЮKassa
    Возвращает True если статус изменился
    """
    if not fine.yookassa_payment_id:
        return False

    payment_status = check_yookassa_payment_status(fine.yookassa_payment_id)

    if payment_status == 'succeeded' and fine.status != 'paid':
        fine.mark_as_paid()
        return True
    elif payment_status == 'canceled' and fine.status != 'cancelled':
        fine.status = 'cancelled'
        fine.save()
        return True

    return False