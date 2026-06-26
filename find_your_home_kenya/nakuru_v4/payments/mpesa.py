"""
M-Pesa Integration - Safaricom Daraja API
Handles STK Push and payment verification
"""
import base64
import json
import logging
import requests
from datetime import datetime
from django.conf import settings

logger = logging.getLogger(__name__)


def get_mpesa_env():
    """Return base URL based on environment."""
    if getattr(settings, 'MPESA_ENV', 'sandbox') == 'production':
        return 'https://api.safaricom.co.ke'
    return 'https://sandbox.safaricom.co.ke'


def get_access_token():
    """Get OAuth token from Safaricom."""
    consumer_key = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET
    base_url = get_mpesa_env()

    if not consumer_key or not consumer_secret:
        logger.warning('M-Pesa credentials not configured')
        return None

    url = f'{base_url}/oauth/v1/generate?grant_type=client_credentials'
    credentials = base64.b64encode(f'{consumer_key}:{consumer_secret}'.encode()).decode()

    try:
        response = requests.get(
            url,
            headers={'Authorization': f'Basic {credentials}'},
            timeout=30
        )
        response.raise_for_status()
        return response.json().get('access_token')
    except Exception as e:
        logger.error(f'Failed to get M-Pesa token: {e}')
        return None


def stk_push(phone_number, amount, account_reference, description):
    """
    Initiate M-Pesa STK Push (Lipa na M-Pesa).
    Returns dict with success status and response data.
    """
    from payments.models import SiteSettings
    site = SiteSettings.get_settings()

    access_token = get_access_token()
    if not access_token:
        return {'success': False, 'error': 'Payment service unavailable. Please try manual payment.'}

    base_url = get_mpesa_env()
    shortcode = settings.MPESA_SHORTCODE
    passkey = settings.MPESA_PASSKEY
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    password = base64.b64encode(f'{shortcode}{passkey}{timestamp}'.encode()).decode()

    # Format phone number
    phone = phone_number.strip().replace(' ', '').replace('-', '')
    if phone.startswith('0'):
        phone = '254' + phone[1:]
    elif phone.startswith('+'):
        phone = phone[1:]

    payload = {
        'BusinessShortCode': shortcode,
        'Password': password,
        'Timestamp': timestamp,
        'TransactionType': 'CustomerBuyGoodsOnline',
        'Amount': amount,
        'PartyA': phone,
        'PartyB': shortcode,
        'PhoneNumber': phone,
        'CallBackURL': f'{getattr(settings, "SITE_URL", "https://yourdomain.com")}/payments/mpesa/callback/',
        'AccountReference': account_reference,
        'TransactionDesc': description,
    }

    try:
        response = requests.post(
            f'{base_url}/mpesa/stkpush/v1/processrequest',
            json=payload,
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
            },
            timeout=30
        )
        data = response.json()

        if data.get('ResponseCode') == '0':
            return {
                'success': True,
                'checkout_request_id': data.get('CheckoutRequestID'),
                'message': 'Payment request sent to your phone. Enter your M-Pesa PIN.'
            }
        else:
            return {'success': False, 'error': data.get('ResponseDescription', 'Payment failed')}

    except Exception as e:
        logger.error(f'STK Push failed: {e}')
        return {'success': False, 'error': 'Could not connect to M-Pesa. Try again or pay manually.'}


def check_payment_status(checkout_request_id):
    """Query the status of an STK push request."""
    access_token = get_access_token()
    if not access_token:
        return {'success': False}

    base_url = get_mpesa_env()
    shortcode = settings.MPESA_SHORTCODE
    passkey = settings.MPESA_PASSKEY
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    password = base64.b64encode(f'{shortcode}{passkey}{timestamp}'.encode()).decode()

    payload = {
        'BusinessShortCode': shortcode,
        'Password': password,
        'Timestamp': timestamp,
        'CheckoutRequestID': checkout_request_id,
    }

    try:
        response = requests.post(
            f'{base_url}/mpesa/stkpushquery/v1/query',
            json=payload,
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
            },
            timeout=30
        )
        data = response.json()
        result_code = data.get('ResultCode')
        return {
            'success': result_code == '0',
            'result_code': result_code,
            'result_desc': data.get('ResultDesc', ''),
        }
    except Exception as e:
        logger.error(f'Payment status check failed: {e}')
        return {'success': False}
