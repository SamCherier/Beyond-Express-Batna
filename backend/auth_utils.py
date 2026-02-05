from argon2 import PasswordHasher, Type
from argon2.exceptions import VerifyMismatchError, InvalidHashError
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv
from pathlib import Path
import uuid
import logging

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Argon2id Configuration (Military-grade security)
ph = PasswordHasher(
    time_cost=3,           # Number of iterations
    memory_cost=65536,     # 64 MB memory usage
    parallelism=4,         # Number of parallel threads
    hash_len=32,           # 32 bytes output
    salt_len=16,           # 16 bytes salt
    encoding='utf-8',
    type=Type.ID           # Argon2id (hybrid mode: resistant to side-channel + GPU attacks)
)

JWT_SECRET = os.environ.get('JWT_SECRET', 'default_secret_key')
JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM', 'HS256')
JWT_EXPIRATION_DAYS = int(os.environ.get('JWT_EXPIRATION_DAYS', 7))

def hash_password(password: str) -> str:
    """Hash password using Argon2id (military-grade)"""
    try:
        return ph.hash(password)
    except Exception as e:
        logger.error(f"Password hashing error: {e}")
        raise

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against Argon2id hash"""
    try:
        ph.verify(hashed_password, plain_password)
        
        # Auto-rehash if parameters changed (future-proof)
        if ph.check_needs_rehash(hashed_password):
            logger.info("Password hash needs rehashing with new parameters")
        
        return True
    except VerifyMismatchError:
        return False
    except InvalidHashError:
        logger.warning("Invalid hash format detected")
        return False
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRATION_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None

def generate_session_token() -> str:
    return str(uuid.uuid4())