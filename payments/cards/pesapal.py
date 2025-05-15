import logging
import uuid
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from requests_oauthlib import OAuth1Session
import xml.etree.ElementTree as ET
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

def initiate_pesapal_payment(request, cart, delivery_info, total_usd):
    """
    Initiate a Pesapal payment for the given cart.

    Args:
        request: The HTTP request object.
        cart: The user's cart object (Cart model instance).
        delivery_info: The DeliveryInfo instance tied to the order (None if not created).
        total_usd: The total amount in USD (float).

    Returns:
        dict: Contains 'iframe_url', 'order_id', 'status', and 'message'.

    Raises:
        ImproperlyConfigured: If required Pesapal settings are missing.
    """
    required_settings = ['PESAPAL_CONSUMER_KEY', 'PESAPAL_CONSUMER_SECRET', 'PESAPAL_API_URL']
    for setting in required_settings:
        if not hasattr(settings, setting):
            raise ImproperlyConfigured(f"{setting} must be set in settings.py")

    api_url = settings.PESAPAL_API_URL
    payment_url = f"{api_url}/API/PostPesapalDirectOrderV4"
    order_id = str(uuid.uuid4())

    # Check if Pesapal is reachable
    try:
        test_response = requests.get(api_url, timeout=5)
        if test_response.status_code != 200:
            logger.warning("Pesapal API is down (initial check failed).")
            return {
                'iframe_url': None,
                'order_id': order_id,
                'status': 'down',
                'message': 'Pesapal is currently unavailable. Please try another payment method.'
            }
    except (requests.Timeout, requests.ConnectionError) as e:
        logger.warning(f"Pesapal API unreachable: {str(e)}")
        return {
            'iframe_url': None,
            'order_id': order_id,
            'status': 'down',
            'message': 'Pesapal is currently unavailable. Please try another payment method.'
        }

    # Prepare XML payload
    root = ET.Element("PesapalDirectOrderInfo")
    root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    root.set("xmlns:xsd", "http://www.w3.org/2001/XMLSchema")
    root.set("xmlns", "http://www.pesapal.com")
    ET.SubElement(root, "Amount").text = f"{total_usd:.2f}"
    ET.SubElement(root, "Currency").text = "USD"
    ET.SubElement(root, "Description").text = f"Order for {request.user.username}"
    ET.SubElement(root, "Type").text = "MERCHANT"
    ET.SubElement(root, "Reference").text = order_id
    ET.SubElement(root, "FirstName").text = request.user.first_name or "Customer"
    ET.SubElement(root, "LastName").text = request.user.last_name or ""
    ET.SubElement(root, "Email").text = request.user.email or "customer@example.com"
    ET.SubElement(root, "PhoneNumber").text = request.session.get('pending_order', {}).get('phone_number', '')
    xml_payload = ET.tostring(root, encoding='utf-8', method='xml').decode('utf-8')

    oauth = OAuth1Session(
        client_key=settings.PESAPAL_CONSUMER_KEY,
        client_secret=settings.PESAPAL_CONSUMER_SECRET,
    )
    callback_url = request.build_absolute_uri('/payments/payment-done/')

    session = oauth
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount('https://', adapter)

    params = {
        "oauth_callback": callback_url,
        "pesapal_request_data": xml_payload,
    }

    try:
        response = session.post(payment_url, data=params, timeout=30)
        logger.debug(f"Pesapal response status: {response.status_code}, text: {response.text}")
    except (requests.Timeout, requests.ConnectionError) as e:
        logger.error(f"Pesapal request failed: {str(e)}")
        return {
            'iframe_url': None,
            'order_id': order_id,
            'status': 'down',
            'message': 'Pesapal is currently unavailable. Please try another payment method.'
        }

    if response.status_code != 200:
        logger.error(f"Pesapal API error: {response.text}")
        return {
            'iframe_url': None,
            'order_id': order_id,
            'status': 'down',
            'message': 'Pesapal is currently unavailable. Please try another payment method.'
        }

    try:
        if "pesapal_response_data=" not in response.text:
            logger.error(f"Unexpected Pesapal response format: {response.text}")
            raise Exception(f"Unexpected Pesapal response format: {response.text}")
        tracking_id = response.text.split('pesapal_response_data=')[1].strip()
        logger.debug(f"Pesapal tracking ID: {tracking_id}")
    except (IndexError, Exception) as e:
        logger.error(f"Failed to parse Pesapal response: {str(e)}")
        return {
            'iframe_url': None,
            'order_id': order_id,
            'status': 'down',
            'message': 'Pesapal is currently unavailable. Please try another payment method.'
        }

    iframe_url = f"{api_url}/API/Transactions/RenderIframe?orderTrackingId={tracking_id}"
    logger.debug(f"Pesapal iframe URL: {iframe_url}")
    return {'iframe_url': iframe_url, 'order_id': order_id, 'status': 'up'}

def verify_pesapal_payment(order_id):
    """
    Placeholder to verify Pesapal payment status.

    Args:
        order_id: The Pesapal order ID.

    Returns:
        str: Payment status ('paid' or 'unpaid').

    Note: Implementation pending Pesapal API details.
    """
    logger.warning(f"Pesapal verification not implemented for order {order_id}")
    return 'unpaid'  # Placeholder