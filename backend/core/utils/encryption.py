"""
Simple encryption utilities for credential profiles.
"""

import os
import base64
import hashlib
from cryptography.fernet import Fernet
from core.utils.logger import logger


def get_encryption_key() -> bytes:
    """
    Get the credential encryption key.

    Prefer the explicit credential key env vars. If they are missing, derive a
    stable fallback from existing production secrets so the API can still boot.
    """
    key_env = os.getenv("MCP_CREDENTIAL_ENCRYPTION_KEY") or os.getenv("ENCRYPTION_KEY")

    if key_env:
        try:
            return key_env.encode("utf-8") if isinstance(key_env, str) else key_env
        except Exception as e:
            logger.error(f"Invalid encryption key: {e}")

    for seed_var in (
        "SUPABASE_SERVICE_ROLE_KEY",
        "DATABASE_URL",
        "DATABASE_POOLER_URL",
        "POSTGRES_PASSWORD",
        "SUPABASE_URL",
    ):
        seed = os.getenv(seed_var)
        if not seed:
            continue

        derived_key = base64.urlsafe_b64encode(hashlib.sha256(seed.encode("utf-8")).digest())
        logger.warning(
            "Credential encryption key env missing; using stable derived fallback from existing service secrets"
        )
        return derived_key

    logger.warning("No stable credential encryption seed found, generating a temporary session key")
    key = Fernet.generate_key()
    logger.debug("Generated temporary encryption key for this process only")
    return key


def encrypt_data(data: str) -> str:
    """
    Encrypt a string and return base64 encoded encrypted data.
    
    Args:
        data: String data to encrypt
        
    Returns:
        Base64 encoded encrypted string
    """
    encryption_key = get_encryption_key()
    cipher = Fernet(encryption_key)
    
    # Convert string to bytes
    data_bytes = data.encode('utf-8')
    
    # Encrypt the data
    encrypted_bytes = cipher.encrypt(data_bytes)
    
    # Return base64 encoded string
    return base64.b64encode(encrypted_bytes).decode('utf-8')


def decrypt_data(encrypted_data: str) -> str:
    """
    Decrypt base64 encoded encrypted data and return the original string.
    
    Args:
        encrypted_data: Base64 encoded encrypted string
        
    Returns:
        Decrypted string
    """
    encryption_key = get_encryption_key()
    cipher = Fernet(encryption_key)
    
    # Decode base64 to get encrypted bytes
    encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
    
    # Decrypt the data
    decrypted_bytes = cipher.decrypt(encrypted_bytes)
    
    # Return as string
    return decrypted_bytes.decode('utf-8') 
