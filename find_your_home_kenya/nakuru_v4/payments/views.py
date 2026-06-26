"""
Payments Views
Manual M-Pesa code submission — admin must confirm before account activates
"""
import json
import logging
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone

from payments.models import Payment, SiteSettings
from payments.mpesa import stk_push, check_payment_status

logger = logging.getLogger(__name__)


def get_till_number():
    return SiteSettings.get_settings().mpesa_till_number


@require_POST
def initiate_payment(request):
    """Start an STK push payment (only if Safaricom credentials are configured)."""
    phone = request.POST.get('phone', '').strip()
    payment_type = request.POST.get('payment_type', '')
    email = request.POST.get('email', '').strip()

    if not phone or payment_type not in ('landlord', 'tenant'):
        return JsonResponse({'success': False, 'error': 'Invalid request'})

    site = SiteSettings.get_settings()
    amount = site.landlord_fee if payment_type == 'landlord' else site.tenant_fee

    payment = Payment.objects.create(
        payment_type=payment_type,
        user_phone=phone,
        user_email=email,
        amount=amount,
        status='pending',
    )

    result = stk_push(
        phone_number=phone,
        amount=amount,
        account_reference=f'FYH-{payment.id}',
        description=f'Find Your Home Kenya {"Landlord" if payment_type == "landlord" else "Tenant"} subscription'
    )

    if result.get('success'):
        payment.notes = result.get('checkout_request_id', '')
        payment.save()
        return JsonResponse({
            'success': True,
            'payment_id': payment.id,
            'checkout_request_id': result.get('checkout_request_id'),
            'message': result.get('message'),
        })
    else:
        return JsonResponse({
            'success': False,
            'payment_id': payment.id,
            'show_manual': True,
            'till_number': site.mpesa_till_number,
            'amount': amount,
            'error': result.get('error'),
        })


@require_POST
def check_payment(request):
    """Poll payment status — used by STK push flow only."""
    payment_id = request.POST.get('payment_id')
    checkout_request_id = request.POST.get('checkout_request_id', '')

    try:
        payment = Payment.objects.get(id=payment_id)
    except Payment.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Payment not found'})

    if payment.status == 'confirmed':
        return JsonResponse({'success': True, 'confirmed': True})

    if checkout_request_id:
        result = check_payment_status(checkout_request_id)
        if result.get('success'):
            payment.confirm()
            _activate_user_after_payment(payment)
            return JsonResponse({'success': True, 'confirmed': True})

    return JsonResponse({'success': True, 'confirmed': False})


@require_POST
def manual_verify(request):
    """
    User submits their M-Pesa transaction code.
    Payment is saved as PENDING — admin must confirm it from the admin panel.
    Account does NOT activate until admin clicks Confirm.
    """
    payment_id = request.POST.get('payment_id')
    mpesa_code = request.POST.get('mpesa_code', '').strip().upper()

    if not mpesa_code or len(mpesa_code) < 6:
        return JsonResponse({'success': False, 'error': 'Enter a valid M-Pesa transaction code'})

    try:
        payment = Payment.objects.get(id=payment_id)
    except Payment.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Payment record not found'})

    # Save code and mark as awaiting admin confirmation — DO NOT activate yet
    payment.mpesa_code = mpesa_code
    payment.status = 'pending'
    payment.notes = f'M-Pesa code submitted by user: {mpesa_code}. Awaiting admin confirmation.'
    payment.save()

    # Return success = True but confirmed = False
    # Frontend will show "Awaiting admin confirmation" message
    return JsonResponse({
        'success': True,
        'confirmed': False,
        'pending_admin': True,
        'message': 'Payment code received. Your account will be activated once our team confirms your payment. This usually takes a few minutes.'
    })


def admin_confirm_payment(request, payment_id):
    """
    Admin-only view — confirms a payment and activates the user account.
    Called from the admin payments panel.
    """
    from admin_panel.decorators import admin_required
    # Check admin session
    if not request.session.get('admin_logged_in'):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden('Admin access required')

    try:
        payment = Payment.objects.get(id=payment_id)
    except Payment.DoesNotExist:
        from django.contrib import messages
        messages.error(request, 'Payment not found.')
        return redirect('admin_panel:payments')

    if payment.status != 'confirmed':
        payment.confirm()
        _activate_user_after_payment(payment)

    from django.contrib import messages
    messages.success(request, f'Payment confirmed. Account for {payment.user_email} has been activated.')
    return redirect('admin_panel:payments')


def admin_reject_payment(request, payment_id):
    """Admin rejects a payment — marks as failed, account stays locked."""
    if not request.session.get('admin_logged_in'):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden('Admin access required')

    try:
        payment = Payment.objects.get(id=payment_id)
        payment.status = 'failed'
        payment.notes = payment.notes + '\nRejected by admin.'
        payment.save()
    except Payment.DoesNotExist:
        pass

    from django.contrib import messages
    messages.warning(request, f'Payment rejected.')
    return redirect('admin_panel:payments')


def _activate_user_after_payment(payment):
    """Activate landlord or tenant account after admin confirms payment."""
    if payment.payment_type == 'landlord':
        from landlords.models import Landlord
        try:
            landlord = Landlord.objects.get(email=payment.user_email)
            landlord.is_active = True
            landlord.save()
        except Landlord.DoesNotExist:
            pass
    elif payment.payment_type == 'tenant':
        from tenants.models import Tenant
        try:
            tenant = Tenant.objects.get(email=payment.user_email)
            tenant.is_active = True
            tenant.save()
        except Tenant.DoesNotExist:
            pass


@csrf_exempt
def mpesa_callback(request):
    """Receives callback from Safaricom after STK push payment."""
    if request.method != 'POST':
        return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Failed'})

    try:
        data = json.loads(request.body)
        callback = data.get('Body', {}).get('stkCallback', {})
        result_code = callback.get('ResultCode')
        checkout_request_id = callback.get('CheckoutRequestID', '')

        try:
            payment = Payment.objects.get(notes__contains=checkout_request_id)
            if result_code == 0:
                items = callback.get('CallbackMetadata', {}).get('Item', [])
                for item in items:
                    if item.get('Name') == 'MpesaReceiptNumber':
                        payment.mpesa_code = item.get('Value', '')
                        break
                payment.confirm()
                _activate_user_after_payment(payment)
            else:
                payment.status = 'failed'
                payment.save()
        except Payment.DoesNotExist:
            logger.warning(f'Payment not found for checkout: {checkout_request_id}')

    except Exception as e:
        logger.error(f'Callback error: {e}')

    return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Success'})
