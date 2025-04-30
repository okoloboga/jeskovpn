import aiohttp
import asyncio
import json
import logging
from typing import Dict, Optional, Any
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

async def payment_balance_process(
        user_id: int, amount: float, period: int, device_type: str, device: str, payment_type: str,
) -> Optional[Dict[str, Any]]:
    """POST /payments/balance"""
    url = f"{BASE_URL}/payments/balance"
    payload = {
        "user_id": int(user_id),
        "amount": float(amount),
        "period": int(period),
        "device_type": str(device_type),
        "device": str(device),
        "payment_type": str(payment_type)
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

async def exchange_rate(currency: str) -> float:
    headers = {
        "Crypto-Pay-API-Token": cryptobot_api,
        "Content-Type": "application/json"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{cryptobot_url}/getExchangeRates", headers=headers) as resp:
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

async def create_cryptobot_invoice(amount, asset, payload, description=None) -> Optional[tuple]:
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
                logger.error(f"CryptoBot error: {result}")
                return None
            invoice_url = result["result"]["pay_url"]
            invoice_id = result["result"]["invoice_id"]
            logger.info(f'CryptoBot: {result}')
            return invoice_url, invoice_id

async def deposit(user_id: int, amount: float, payment_type: str) -> None:
    """Mock balance deposit."""
    print(f"Deposited {amount} for user {user_id} via {payment_type}")

