import os
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from jose.backends import RSAKey
import requests

bearer_scheme = HTTPBearer()

_jwks_cache = None

def get_jwks():
    global _jwks_cache
    if _jwks_cache is None:
        supabase_url = os.environ["SUPABASE_URL"]
        resp = requests.get(f"{supabase_url}/auth/v1/.well-known/jwks.json")
        resp.raise_for_status()
        _jwks_cache = resp.json()
    return _jwks_cache

def verify_token(credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)) -> str:
    token = credentials.credentials
    
    try:
        # Get the key id from token header
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        
        # Find matching key in JWKS
        jwks = get_jwks()
        key = next((k for k in jwks["keys"] if k["kid"] == kid), None)
        if not key:
            raise HTTPException(status_code=401, detail="Signing key not found")
        
        payload = jwt.decode(
            token,
            key,
            algorithms=["ES256"],
            audience="authenticated",
            options={"verify_aud": True},
        )
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id

    except JWTError as e:
        raise HTTPException(status_code=401, detail="Could not validate token")