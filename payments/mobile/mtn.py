import logging
import requests
import uuid
from base64 import b64encode
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)

class MTNMoMoClient:
    def __init__(self):
        if not all(hasattr(settings, key) for key in ['MTN_SUBSCRIPTION_KEY', 'MTN_CALLBACK_HOST']):
            raise ImproperlyConfigured("MTN_SUBSCRIPTION_KEY and MTN_CALLBACK_HOST must be set in settings.py")
        self.base_url = "https://sandbox.momodeveloper.mtn.com"
        self.subscription_key = settings.MTN_SUBSCRIPTION_KEY
        self.callback_host = settings.MTN_CALLBACK_HOST
        self.api_user = None
        self.api_key = None
        self.access_token = None

    def provision_api_user(self):
        """Create an API User in the MTN sandbox."""
        api_user_id = str(uuid.uuid4())
        url = f"{self.base_url}/v1_0/apiuser"
        headers = {
            "X-Reference-Id": api_user_id,
            "Ocp-Apim-Subscription-Key": self.subscription_key,
            "Content-Type": "application/json",
        }
        payload = {"providerCallbackHost": self.callback_host}
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            logger.info(f"API User created: {api_user_id}")
            self.api_user = api_user_id
            return api_user_id
        except requests.RequestException as e:
            logger.error(f"Failed to create API User: {str(e)}")
            raise Exception(f"MTN API User creation failed: {str(e)}")

    def provision_api_key(self):
        """Generate an API Key for the API User."""
        if not self.api_user:
            raise ValueError("API User must be provisioned first.")
        url = f"{self.base_url}/v1_0/apiuser/{self.api_user}/apikey"
        headers = {
            "Ocp-Apim-Subscription-Key": self.subscription_key,
        }
        
        try:
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            self.api_key = response.json()["apiKey"]
            logger.info(f"API Key generated for {self.api_user}")
            return self.api_key
        except requests.RequestException as e:
            logger.error(f"Failed to create API Key: {str(e)}")
            raise Exception(f"MTN API Key creation failed: {str(e)}")

    def get_access_token(self):
        """Obtain an OAuth 2.0 access token."""
        if not self.api_user or not self.api_key:
            raise ValueError("API User and Key must be provisioned first.")
        url = f"{self.base_url}/collection/token/"
        auth_str = f"{self.api_user}:{self.api_key}"
        auth_header = b64encode(auth_str.encode()).decode("utf-8")
        headers = {
            "Authorization": f"Basic {auth_header}",
            "Ocp-Apim-Subscription-Key": self.subscription_key,
        }
        
        try:
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            self.access_token = response.json()["access_token"]
            logger.info("Access token obtained successfully")
            return self.access_token
        except requests.RequestException as e:
            logger.error(f"Failed to get access token: {str(e)}")
            raise Exception(f"MTN access token retrieval failed: {str(e)}")

    def initiate_mtn_payment(self, request, cart, delivery_info, total_zmw, phone_number):
        """Initiate an MTN MoMo payment request to the user's phone."""
        if not self.access_token:
            self.provision_api_user()
            self.provision_api_key()
            self.get_access_token()

        url = f"{self.base_url}/collection/v1_0/requesttopay"
        reference_id = str(uuid.uuid4())
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "X-Reference-Id": reference_id,
            "X-Target-Environment": "sandbox",
            "Ocp-Apim-Subscription-Key": self.subscription_key,
            "Content-Type": "application/json",
        }
        EXCHANGE_RATE_ZMW_TO_EUR = 0.035  # Approx 1 ZMW = 0.035 EUR (March 2025 estimate)
        total_eur = total_zmw * EXCHANGE_RATE_ZMW_TO_EUR
        logger.warning("MTN Sandbox only supports EUR. Converting ZMW to EUR for testing.")
        
        payload = {
            "amount": str(round(total_eur, 2)),
            "currency": "EUR",
            "externalId": f"ORDER-{cart.id}",
            "payer": {
                "partyIdType": "MSISDN",
                "partyId": phone_number.replace("+", ""),
            },
            "payerMessage": f"Payment for order {cart.id} (ZMW {total_zmw} converted to EUR {total_eur:.2f})",
            "payeeNote": f"Payment received for order {cart.id}",
            "X-Callback-Url": f"{self.callback_host}/mtn/callback/",
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 202:
                logger.info(f"MTN payment request sent: {reference_id} to {phone_number}")
                return {
                    'status': 'success',
                    'transaction_id': reference_id,
                    'message': f"Payment request sent to {phone_number}. Please check your phone to authorize (amount in EUR for sandbox testing)."
                }
            else:
                logger.error(f"MTN payment request failed: {response.text}")
                raise Exception(f"MTN payment request failed: {response.text}")
        except requests.RequestException as e:
            logger.error(f"MTN payment initiation failed: {str(e)}")
            raise Exception(f"MTN payment initiation failed: {str(e)}")

    def check_mtn_status(self, transaction_id):
        """Check the status of an MTN MoMo payment request."""
        if not self.access_token:
            self.get_access_token()

        url = f"{self.base_url}/collection/v1_0/requesttopay/{transaction_id}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "X-Target-Environment": "sandbox",
            "Ocp-Apim-Subscription-Key": self.subscription_key,
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            status = data.get("status")  # e.g., "PENDING", "SUCCESSFUL", "FAILED"
            logger.info(f"MTN transaction {transaction_id} status: {status}")
            return {
                'status': status,
                'details': data
            }
        except requests.RequestException as e:
            logger.error(f"Failed to check MTN status for {transaction_id}: {str(e)}")
            raise Exception(f"MTN status check failed: {str(e)}")

def initiate_mtn_payment(request, cart, delivery_info, total_zmw, phone_number):
    """Wrapper function for external use."""
    client = MTNMoMoClient()
    return client.initiate_mtn_payment(request, cart, delivery_info, total_zmw, phone_number)

def check_mtn_payment_status(transaction_id):
    """Wrapper function to check payment status."""
    client = MTNMoMoClient()
    return client.check_mtn_status(transaction_id)