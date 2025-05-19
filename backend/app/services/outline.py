import httpx
import logging
from typing import Optional, Tuple
from fastapi import HTTPException, status
from app.core.logging import logger

async def create_outline_key(api_url: str, cert_sha256: str) -> Tuple[str, str]:
    """
    Create a new access key using Outline Management API.
    
    Args:
        api_url: Outline API URL (e.g., https://195.133.64.129:53470/IT1hLCPJJRgkP9C8aNe3gA)
        cert_sha256: Certificate SHA256 fingerprint
    
    Returns:
        Tuple of (access_key, key_id)
        
    Raises:
        HTTPException: If the API request fails
    """
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(verify=False) as client:  # Игнорируем SSL-проверку
        try:
            response = await client.post(
                f"{api_url}/access-keys",
                headers=headers,
                json={}
            )
            response.raise_for_status()
            
            data = response.json()
            access_key = data.get("accessUrl")
            key_id = data.get("id")
            
            if not access_key or not key_id:
                logger.error(f"Invalid response from Outline API: {data}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to generate VPN key: invalid response"
                )
            
            logger.info(f"Generated Outline key: id={key_id}, access_key={access_key}")
            return access_key, key_id
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Outline API error: {e.response.status_code} - {e.response.text}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to generate VPN key: {e.response.text}"
            )
        except httpx.RequestError as e:
            logger.error(f"Outline API connection error: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to connect to Outline API"
            )

async def delete_outline_key(api_url: str, cert_sha256: str, outline_key_id: str) -> None:
    """
    Delete an access key using Outline Management API.
    
    Args:
        api_url: Outline API URL (e.g., https://195.133.64.129:53470/IT1hLCPJJRgkP9C8aNe3gA)
        cert_sha256: Certificate SHA256 fingerprint
        outline_key_id: ID of the key to delete (e.g., "1")
    
    Raises:
        HTTPException: If the API request fails
    """
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(verify=False) as client:
        try:
            response = await client.delete(
                f"{api_url}/access-keys/{outline_key_id}",
                headers=headers
            )
            response.raise_for_status()
            
            logger.info(f"Deleted Outline key: id={outline_key_id}")
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Outline API error: {e.response.status_code} - {e.response.text}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to delete VPN key: {e.response.text}"
            )
        except httpx.RequestError as e:
            logger.error(f"Outline API connection error: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to connect to Outline API"
            )
