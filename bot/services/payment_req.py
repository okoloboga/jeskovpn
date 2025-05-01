import aiohttp
import asyncio
import json
import logging
from typing import Dict, Optional, Any, List, Tuple
from config import get_config, Backend, CryptoBot

backend = get_config(Backend, "backend")
cryptobot = get_config(CryptoBot, "cryptobot")
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
                logger.info(f"Process Balance Payment: Status {status}")
                logger.info(json.dumps(response_json, indent=2))
                if status in (200, 201):
                    return response_json
                else:
                    logger.error(f"Process Balance Payment: Failed with status {status}")
                    return None
        except aiohttp.ClientError as e:
            logger.error(f"Process Balance Payment: Error - {e}")
            return None

async def payment_ukassa_process(
    event: str, payment_id: str, status: str, amount_value: str, currency: str,
    user_id: str, period: str, device_type: str, payment_type: str,
    payload: Optional[Dict] = None
) -> Optional[Dict[str, Any]]:
    """POST /api/payments/ukassa"""
    url = f"{BASE_URL}/api/payments/ukassa"
    default_payload = {
        "event": event,
        "object": {
            "id": payment_id,
            "status": status,
            "amount": {
                "value": amount_value,
                "currency": currency
            },
            "metadata": {
                "user_id": user_id,
                "period": period,
                "device_type": device_type,
                "payment_type": payment_type
            }
        }
    }
    request_payload = payload if payload is not None else default_payload

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=HEADERS, json=request_payload) as response:
                status = response.status
                response_json = await response.json()
                logger.info(f"Ukassa Webhook: Status {status}")
                logger.info(json.dumps(response_json, indent=2))
                if status in (200, 201):
                    return response_json
                else:
                    logger.error(f"Ukassa Webhook: Failed with status {status}")
                    return None
        except aiohttp.ClientError as e:
            logger.error(f"Ukassa Webhook: Error - {e}")
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
                logger.info(f"Create CryptoBot Invoice: Status {status}")
                logger.info(json.dumps(response_json, indent=2))
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
                logger.info(f"Check Invoice Status: Status {status}")
                logger.info(json.dumps(response_json, indent=2))
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
                logger.info(f"Save Invoice: Status {status}")
                logger.info(json.dumps(response_json, indent=2))
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
    logger.info(f"Sending request to backend: GET {url}")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=HEADERS) as response:
                status = response.status
                response_json = await response.json()
                logger.info(f"Get Active Invoices: Status {status}")
                logger.info(json.dumps(response_json, indent=2))
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
                logger.info(f"Update Invoice Status: Status {status}")
                logger.info(json.dumps(response_json, indent=2))
                if status in (200, 201):
                    return response_json
                else:
                    logger.error(f"Update Invoice Status: Failed with status {status}")
                    return None
        except aiohttp.ClientError as e:
            logger.error(f"Update Invoice Status: Error - {e}")
            return None

