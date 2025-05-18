import aiohttp
import asyncio
import json
import uuid
import logging

from yookassa import Configuration, Payment
from yookassa.domain.response import PaymentResponse
from fluentogram import TranslatorRunner
from typing import Dict, Optional, Any, List, Tuple
from config import get_config, Backend, CryptoBot, Yookassa

backend = get_config(Backend, "backend")
cryptobot = get_config(CryptoBot, "cryptobot")
yookassa = get_config(Yookassa, "yookassa")
if not yookassa.id or not yookassa.key:
    raise ValueError("ЮKassa configuration is missing shop_id or secret_key")
Configuration.account_id = yookassa.id 
Configuration.secret_key = yookassa.key 
api_key = backend.key
url = backend.url
cryptobot_api = cryptobot.key
cryptobot_url = cryptobot.url

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Base URL for the API
BASE_URL = url
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

CRYPTOBOT_HEADERS = {
        "Crypto-Pay-API-Token": cryptobot_api,
        "Content-Type": "application/json"
    }

async def get_subscriptions(user_id: int) -> Optional[Dict[str, Any]]:
    """GET /payments/subscriptions/{user_id}"""
    url = f"{BASE_URL}/payments/subscriptions/{user_id}"
    
    logger.info(f"Sending request to backend: GET {url}")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=HEADERS) as response:
                status = response.status
                response_json = await response.json()
                # logger.info(f"Get Subscriptions: Status {status}")
                # logger.info(json.dumps(response_json, indent=2))
                if status in (200, 201):
                    return response_json
                else:
                    logger.error(f"Get Subscriptions: Failed with status {status}")
                    return None
        except aiohttp.ClientError as e:
            logger.error(f"Get Subscriptions: Error - {e}")
            return None

async def payment_balance_process(
        user_id: int, amount: float, period: int, device_type: str, 
        device: str, payment_type: str, method: str
) -> Optional[Dict[str, Any]]:
    """POST /payments/balance"""
    url = f"{BASE_URL}/payments/balance"
    payload = {
        "user_id": int(user_id),
        "amount": float(amount),
        "period": int(period),
        "device_type": str(device_type),
        "device": str(device),
        "payment_type": str(payment_type),
        "method": str(method)
    }
    logger.info(f"Sending request to backend: {json.dumps(payload, ensure_ascii=False)}")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=HEADERS, json=payload) as response:
                status = response.status
                response_json = await response.json()
                # logger.info(f"Process Balance Payment: Status {status}")
                # logger.info(json.dumps(response_json, indent=2))
                if status in (200, 201):
                    return response_json
                else:
                    logger.error(f"Process Balance Payment: Failed with status {status}")
                    return None
        except aiohttp.ClientError as e:
            logger.error(f"Process Balance Payment: Error - {e}")
            return None

def generate_receipt_description(
        payload: str, amount: float, i18n: TranslatorRunner
        ) -> str:
    parts = payload.split(":")
    if len(parts) != 7:
        return f"Оплата на сумму {amount:.2f} рублей"
    
    _, _, period, device_type, device, payment_type, _ = parts

    if payment_type == "add_balance":
        return i18n.ukassa.receipt.add_balance(amount=amount)
    
    period = period if period != "0" else "1"
    
    if device_type == "combo": 
        device_type_str = i18n.ukassa.device_type.combo(device=device) 
    elif device_type == "device":
        device_type_str = i18n.ukassa.device_type.device
    else:
        device_type_str = i18n.ukassa.device_type.router

    return i18n.ukassa.receipt.subscription(device_type=device_type_str, period=period)

async def create_ukassa_invoice(
    amount: float,
    currency: str,
    payload: str,
    i18n: TranslatorRunner,
    customer: Dict[str, str],
    description: Optional[str] = None
) -> Optional[Tuple[str, str]]:
    """Create a payment invoice via ЮKassa API."""
    if currency != "RUB":
        logger.error(f"Invalid currency: {currency}. Only RUB is supported.")
        return None

    if not customer.get("email") and not customer.get("phone"):
        logger.error(f"Invalid customer data: {customer}")
        return None

    idempotence_key = str(uuid.uuid4())
    receipt_description = str(generate_receipt_description(payload, amount, i18n))
    
    payment_data = {
        "amount": {
            "value": f"{amount:.2f}",
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/lovelyNochka_bot"  # Реальный username бота
        },
        "capture": True,
        "description": description or "Subscription payment",
        "metadata": {"payload": payload},
        "receipt": {
            "customer": customer,
            "items": [
                {
                    "description": receipt_description[:128],
                    "quantity": "1",
                    "amount": {
                        "value": f"{amount:.2f}",
                        "currency": "RUB"
                    },
                    "vat_code": 1
                }
            ]
        }
    }

    logger.info(f"Sending request to ЮKassa: {json.dumps(payment_data, ensure_ascii=False)}")
    try:
        payment: PaymentResponse = Payment.create(payment_data, idempotence_key)
        if payment.status == "pending" and payment.confirmation:
            invoice_url = payment.confirmation.confirmation_url
            invoice_id = payment.id
            # logger.info(f"ЮKassa Invoice created: ID={invoice_id}, URL={invoice_url}")
            return invoice_url, invoice_id
        else:
            logger.error(f"ЮKassa Invoice creation failed: Status={payment.status}")
            return None
    except Exception as e:
        logger.error(f"ЮKassa Invoice creation error: {e}, payment_data={json.dumps(payment_data, ensure_ascii=False)}")
        return None


async def check_ukassa_invoice_status(invoice_id: str) -> Optional[Dict[str, Any]]:
    """Check the status of a ЮKassa payment."""
    logger.info(f"Checking ЮKassa invoice status: ID={invoice_id}")
    try:
        payment: PaymentResponse = Payment.find_one(invoice_id)
        result = {
            "invoice_id": payment.id,
            "status": payment.status,
            "amount": float(payment.amount.value),
            "currency": payment.amount.currency,
            "payload": payment.metadata.get("payload", ""),
            "paid": payment.paid
        }
        # logger.info(f"ЮKassa Invoice status: {json.dumps(result, ensure_ascii=False)}")
        return result
    except Exception as e:
        logger.error(f"ЮKassa Invoice status check error: {e}")
        return None

async def exchange_rate(currency: str) -> Optional[float]:
    url = f"{cryptobot_url}/getExchangeRates"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=CRYPTOBOT_HEADERS) as resp:
                data = await resp.json()
                if not data.get("ok"):
                    logger.error(f"CryptoBot error: {data}")
                    raise Exception(f"CryptoBot error: {data}")
                rates = data["result"]
                for rate in rates:
                    if rate["source"] == currency and rate["target"] == "RUB":
                        return float(rate["rate"])
                logger.error("USDT to RUB rate not found")
                raise Exception("USDT to RUB rate not found")
        except aiohttp.ClientError as e:
            logger.error(f"Get Exchange Rate: Error - {e}")
            return None

async def create_cryptobot_invoice(
    amount: float, asset: str, payload: str, description: Optional[str] = None
) -> Optional[Tuple[str, str]]:
    """POST /createInvoice to CryptoBot"""
    url = f"{cryptobot_url}/createInvoice"
    payload_data = {
        "asset": str(asset),
        "amount": str(float(amount)),
        "payload": str(payload)
    }
    if description:
        payload_data["description"] = str(description)

    logger.info(f"Sending request to CryptoBot: {json.dumps(payload_data, ensure_ascii=False)}")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=CRYPTOBOT_HEADERS, json=payload_data) as response:
                status = response.status
                response_json = await response.json()
                # logger.info(f"Create CryptoBot Invoice: Status {status}")
                # logger.info(json.dumps(response_json, indent=2))
                if status in (200, 201) and response_json.get("ok"):
                    invoice_url = response_json["result"]["pay_url"]
                    invoice_id = response_json["result"]["invoice_id"]
                    return invoice_url, invoice_id
                else:
                    logger.error(f"Create CryptoBot Invoice: Failed with status {status}")
                    return None
        except aiohttp.ClientError as e:
            logger.error(f"Create CryptoBot Invoice: Error - {e}")
            return None

async def check_invoice_status(invoice_id: str) -> Optional[Dict[str, Any]]:
    """GET /getInvoices from CryptoBot"""
    url = f"{cryptobot_url}/getInvoices"
    params = {"invoice_ids": str(invoice_id)}

    logger.info(f"Sending request to CryptoBot: GET {url} with params {params}")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=CRYPTOBOT_HEADERS, params=params) as response:
                status = response.status
                response_json = await response.json()
                # logger.info(f"Check Invoice Status: Status {status}")
                # logger.info(json.dumps(response_json, indent=2))
                if status in (200, 201) and response_json.get("ok"):
                    invoices = response_json["result"]["items"]
                    if invoices:
                        return invoices[0]
                    logger.error(f"Invoice {invoice_id} not found")
                    return None
                else:
                    logger.error(f"Check Invoice Status: Failed with status {status}")
                    return None
        except aiohttp.ClientError as e:
            logger.error(f"Check Invoice Status: Error - {e}")
            return None

async def save_invoice(
    user_id: int, invoice_id: str, amount: float, currency: str, payload: str
) -> Optional[Dict[str, Any]]:
    """POST /payments/invoices"""
    url = f"{BASE_URL}/payments/invoices"
    payload_data = {
        "user_id": int(user_id),
        "invoice_id": str(invoice_id),
        "amount": float(amount),
        "currency": str(currency),
        "status": "active",
        "payload": str(payload)
    }
    logger.info(f"Sending request to backend: {json.dumps(payload_data, ensure_ascii=False)}")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=HEADERS, json=payload_data) as response:
                status = response.status
                response_json = await response.json()
                # logger.info(f"Save Invoice: Status {status}")
                # logger.info(json.dumps(response_json, indent=2))
                if status in (200, 201):
                    return response_json
                else:
                    logger.error(f"Save Invoice: Failed with status {status}")
                    return None
        except aiohttp.ClientError as e:
            logger.error(f"Save Invoice: Error - {e}")
            return None

async def get_active_invoices() -> List[Dict[str, Any]]:
    """GET /payments/invoices?status=active"""
    url = f"{BASE_URL}/payments/invoices?status=active"
    # logger.info(f"Sending request to backend: GET {url}")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=HEADERS) as response:
                status = response.status
                response_json = await response.json()
                # logger.info(f"Get Active Invoices: Status {status}")
                # logger.info(json.dumps(response_json, indent=2))
                if status in (200, 201):
                    return response_json
                else:
                    logger.error(f"Get Active Invoices: Failed with status {status}")
                    return []
        except aiohttp.ClientError as e:
            logger.error(f"Get Active Invoices: Error - {e}")
            return []

async def update_invoice_status(invoice_id: str, status: str) -> Optional[Dict[str, Any]]:
    """PUT /payments/invoices/{invoice_id}"""
    url = f"{BASE_URL}/payments/invoices/{invoice_id}"
    payload = {"status": str(status)}
    logger.info(f"Sending request to backend: {json.dumps(payload, ensure_ascii=False)}")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.put(url, headers=HEADERS, json=payload) as response:
                status = response.status
                response_json = await response.json()
                # logger.info(f"Update Invoice Status: Status {status}")
                # logger.info(json.dumps(response_json, indent=2))
                if status in (200, 201):
                    return response_json
                else:
                    logger.error(f"Update Invoice Status: Failed with status {status}")
                    return None
        except aiohttp.ClientError as e:
            logger.error(f"Update Invoice Status: Error - {e}")
            return None

