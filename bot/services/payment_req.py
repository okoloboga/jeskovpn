import aiohttp
import asyncio
import json
import logging
from typing import Dict, Optional, Tuple, Union
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

# async def payment_balance_process(
# user_id: int, amount: float, period: int, device_type: str, payment_type: str) -> None:
#     """Mock balance payment."""
#     print(f"Balance payment of {amount} for user {user_id}, type: {payment_type}")

async def payment_balance_process(
    user_id: int, amount: float, period: int, device_type: str, payment_type: str,
) -> Tuple[int, Union[Dict, str]]:
    """Test POST /payments/balance
    Note: Using 'device_subscription' instead of 'device' as per handler validation."""
    url = f"{BASE_URL}/payments/balance"
    payload = {
        "user_id": int(user_id),
        "amount": float(amount),
        "period": int(period),
        "device_type": str(device_type),
        "payment_type": str(payment_type)
    }
    logger.info(f"Sending request to backend: {json.dumps(payload, ensure_ascii=False)}")
    request_payload = payload

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=HEADERS, json=request_payload) as response:
                status = response.status
                response_json = await response.json()
                logger.info(f"Process Balance Payment: Status {status}")
                logger.info(json.dumps(response_json, indent=2))
                return response_json
        except aiohttp.ClientError as e:
            logger.error(f"Process Balance Payment: Error - {e}")
            return 0, str(e)

async def payment_ukassa_process(
    event: str, payment_id: str, status: str, amount_value: str, currency: str,
    user_id: str, period: str, device_type: str, payment_type: str,
    payload: Optional[Dict] = None
) -> Tuple[int, Union[Dict, str]]:
    """Test POST /api/payments/ukassa"""
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
            async with session.post(url, headers=HEADERS, json=request_payload) as response:  # No Authorization
                status = response.status
                response_json = await response.json()
                logger.info(f"Ukassa Webhook: Status {status}")
                logger.info(json.dumps(response_json, indent=2))
                return response_json
        except aiohttp.ClientError as e:
            logger.error(f"Ukassa Webhook: Error - {e}")
            return 0, str(e)

async def exchange_rate(currency: str):
    headers = {
        "Crypto-Pay-API-Token": cryptobot_api,
        "Content-Type": "application/json"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{cryptobot_url}/getExchangeRates", headers=headers) as resp:
            data = await resp.json()
            if not data.get("ok"):
                raise Exception(f"CryptoBot error: {data}")
            rates = data["result"]
            for rate in rates:
                if rate["source"] == currency and rate["target"] == "RUB":
                    return float(rate["rate"])
            raise Exception("USDT to RUB rate not found")

async def create_cryptobot_invoice(amount, asset, payload, description=None):
    headers = {
        "Crypto-Pay-API-Token": cryptobot_api,
        "Content-Type": "application/json"
    }
    data = {
        "asset": asset,         
        "amount": str(amount),        
        "payload": payload,          
        }
    if description:
        data["description"] = description

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{cryptobot_url}/createInvoice", headers=headers, json=data) as resp:
            result = await resp.json()
            if not result.get("ok"):
                raise Exception(f"CryptoBot error: {result}")
            invoice_url = result["result"]["pay_url"]
            invoice_id = result["result"]["invoice_id"]
            logger.info(f'CryptoBot: {result}')
            return invoice_url, invoice_id

# async def payment_cryptobot_process(
#     update_id: int, update_type: str, invoice_id: str, amount: str, currency: str,
#     user_id: str, period: str, device_type: str, payment_type: str,
#     payload: Optional[Dict] = None
# ) -> Tuple[int, Union[Dict, str]]:
#     """Test POST /api/payments/crypto"""
#     url = f"{BASE_URL}/api/payments/crypto"
#     default_payload = {
#         "update_id": update_id,
#         "update_type": update_type,
#         "invoice_id": invoice_id,
#         "amount": amount,
#         "currency": currency,
#         "payload": f"user_id:{user_id},period:{period},device_type:{device_type},payment_type:{payment_type}"
#     }
#     request_payload = payload if payload is not None else default_payload
#     CRYPTOBOT_HEADERS = {
#         "Content-Type": "application/json",
#         "Crypto-Pay-API-Token": cryptobot_api,
#         "Authorization": f"Bearer {api_key}"
#     }

#     async with aiohttp.ClientSession() as session:
#         try:
#             async with session.post(url, headers=CRYPTOBOT_HEADERS, json=request_payload) as response:  # No Authorization
#                 status = response.status
#                 response_json = await response.json()
#                 logger.info(f"Cryptobot Webhook: Status {status}")
#                 logger.info(json.dumps(response_json, indent=2))
#                 return response_json
#         except aiohttp.ClientError as e:
#             logger.error(f"Cryptobot Webhook: Error - {e}")
#             return 0, str(e)

async def deposit(user_id: int, amount: float, payment_type: str) -> None:
    """Mock balance deposit."""
    print(f"Deposited {amount} for user {user_id} via {payment_type}")

# async def payment_ukassa_process(user_id: int, amount: float, period: int, device_type: str, payment_type: str) -> None:
#     """Mock ЮKassa payment."""
#     print(f"ЮKassa payment of {amount} for user {user_id}, type: {payment_type}")

# async def payment_crypto_process(user_id: int, amount: float, period: int, device_type: str, payment_type: str) -> None:
#     """Mock crypto payment."""
#     print(f"Crypto payment of {amount} for user {user_id}, type: {payment_type}")


