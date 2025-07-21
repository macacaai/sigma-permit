
from pydantic import BaseModel, Field, validator
from typing import List
from uuid import uuid4
from datetime import datetime, timezone
from dateutil.parser import isoparse

class LicensePayload(BaseModel):
    license_id: str = Field(default_factory=lambda: str(uuid4()))
    customer_id: str
    issued_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: str
    features: List[str]
    issuer_public_key: str  # Added to prevent public key substitution

    @validator('expires_at')
    def _future(cls, v):
        if isoparse(v) <= datetime.now(timezone.utc):
            raise ValueError('expires_at must be in the future')
        return v

class SignedLicense(BaseModel):
    encrypted_payload: str  # Encrypted LicensePayload
    signature: str
