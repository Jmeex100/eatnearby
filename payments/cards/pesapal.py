from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from requests_oauthlib import OAuth1Session
import uuid
import xml.etree.ElementTree as ET
import logging
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import requests.exceptions

logger = logging.getLogger(__name__)

def initiate_pesapal_payment(request, cart, delivery_info, total_usd):
    required_settings = ['PESAPAL_CONSUMER_KEY', 'PESAPAL_CONSUMER_SECRET', 'PESAPAL_API_URL']
    for setting in required_settings:
        if not hasattr(settings, setting):
            raise ImproperlyConfigured(f"{setting} must be set in settings.py")

    api_url = settings.PESAPAL_API_URL
    payment_url = f"{api_url}/API/PostPesapalDirectOrderV4"
    order_id = str(uuid.uuid4())

    # Check if Pesapal is reachable first
    try:
        test_response = requests.get(api_url, timeout=5)
        if test_response.status_code != 200:
            logger.warning("Pesapal API is down (initial check failed). Returning placeholder.")
            return {
                'iframe_url': None,
                'order_id': order_id,
                'status': 'down',
                'message': 'Pesapal is currently unavailable. Coming soon!'
            }
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        logger.warning(f"Pesapal API unreachable: {str(e)}. Returning placeholder.")
        return {
            'iframe_url': None,
            'order_id': order_id,
            'status': 'down',
            'message': 'Pesapal is currently unavailable. Coming soon!'
        }

    # Proceed with normal payment initiation if API is up
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
    ET.SubElement(root, "PhoneNumber").text = delivery_info.phone_number
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
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        logger.error(f"Pesapal request failed: {str(e)}. Returning placeholder.")
        return {
            'iframe_url': None,
            'order_id': order_id,
            'status': 'down',
            'message': 'Pesapal is currently unavailable. Coming soon!'
        }

    if response.status_code != 200:
        logger.error(f"Pesapal API error: {response.text}. Returning placeholder.")
        return {
            'iframe_url': None,
            'order_id': order_id,
            'status': 'down',
            'message': 'Pesapal is currently unavailable. Coming soon!'
        }

    try:
        if "pesapal_response_data=" not in response.text:
            logger.error(f"Unexpected Pesapal response format: {response.text}")
            raise Exception(f"Unexpected Pesapal response format: {response.text}")
        tracking_id = response.text.split('pesapal_response_data=')[1].strip()
        logger.debug(f"Pesapal tracking ID: {tracking_id}")
    except IndexError:
        logger.error(f"Failed to parse Pesapal response: {response.text}")
        raise Exception(f"Invalid Pesapal response format: {response.text}")

    iframe_url = f"{api_url}/API/Transactions/RenderIframe?orderTrackingId={tracking_id}"
    logger.debug(f"Pesapal iframe URL: {iframe_url}")

    return {'iframe_url': iframe_url, 'order_id': order_id, 'status': 'up'}

def verify_pesapal_payment(request):
    pass