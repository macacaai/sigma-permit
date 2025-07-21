
import logging
import datetime
from fastapi import FastAPI, HTTPException, status, Depends, Header
from pydantic import BaseModel
from prometheus_fastapi_instrumentator import Instrumentator
try:
    from opentelemetry.instrumentation.asgi import OpenTelemetryMiddleware
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    has_opentelemetry = True
except ImportError:
    has_opentelemetry = False

from license_server.config import settings
from common.crypto import generate_keypair, sign_payload, verify_signature

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger("license-server")

# Configure OpenTelemetry if enabled
if has_opentelemetry and settings.OTEL_EXPORTER_OTLP_ENDPOINT:
    resource = Resource(attributes={SERVICE_NAME: settings.OTEL_SERVICE_NAME})
    trace.set_tracer_provider(TracerProvider(resource=resource))
    otlp_exporter = OTLPSpanExporter(endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT)
    trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(otlp_exporter))
    logger.info(f"OpenTelemetry tracing enabled, exporting to {settings.OTEL_EXPORTER_OTLP_ENDPOINT}")
elif has_opentelemetry:
    logger.warning("OpenTelemetry is installed but OTEL_EXPORTER_OTLP_ENDPOINT is not set. Tracing will not be exported.")
else:
    logger.warning("OpenTelemetry not installed. Tracing disabled.")

app = FastAPI(
    title="License Server",
    version="2.0",
    description="API for generating and validating software licenses",
    openapi_tags=[
        {
            "name": "Licensing",
            "description": "Operations for license management"
        },
        {
            "name": "Health",
            "description": "Service health checks"
        }
    ]
)
if has_opentelemetry and settings.OTEL_EXPORTER_OTLP_ENDPOINT:
    app.add_middleware(OpenTelemetryMiddleware)
Instrumentator().instrument(app).expose(app, include_in_schema=True)


# Models
class GenerateResponse(BaseModel):
    private_key: str
    public_key: str
    details: str

class IssueRequest(BaseModel):
    validator_public_key: str  # For encrypting payload
    payload: dict
    expires_in_days: int

class SignedResponse(BaseModel):
    payload: dict
    signature: str

class VerifyRequest(BaseModel):
    public_key: str
    payload: dict
    signature: str

@app.get("/generate", tags=["Licensing"], summary="Generate key pair", description="Generates a new public/private key pair for license signing")
async def generate():
    private_key, public_key = generate_keypair()
    return GenerateResponse(private_key=private_key, public_key=public_key,details="DO NOT SHARE PRIVATE KEY. Use it only for signing licenses. Share the public key with clients to verify licenses.")

@app.post("/issue", tags=["Licensing"], summary="Issue license", description="Creates a signed license with expiration")
async def issue_license(req: IssueRequest):
    # Calculate expiration date
    expires_at = (datetime.datetime.utcnow() + datetime.timedelta(days=req.expires_in_days)).isoformat() + "Z"
    
    # Create payload with expiration
    license_payload = req.payload.copy()
    license_payload["expires_at"] = expires_at
    
    # Encrypt payload using validator's public key
    from common.crypto import encrypt_payload
    encrypted_payload = encrypt_payload(license_payload, req.validator_public_key)
    
    # Sign the encrypted payload with MASTER_KEY
    from license_server.config import settings
    signature = sign_payload({"encrypted_payload": encrypted_payload}, settings.MASTER_KEY)
    return SignedResponse(payload={"encrypted_payload": encrypted_payload}, signature=signature)

@app.get("/health/live", tags=["Health"], summary="Liveness check", description="Indicates whether the service is running")
async def health_live():
    return {"status": "ok"}

@app.get("/health/ready", tags=["Health"], summary="Readiness check", description="Indicates whether the service is ready to accept requests")
async def health_ready():
    return {"status": "ok"}

@app.post("/verify", tags=["Licensing"], summary="Verify license", description="Validates a license signature and expiration")
async def verify(req: VerifyRequest):
    # Verify signature first
    if not verify_signature(req.payload, req.signature, req.public_key):
        return {"valid": False}
    
    # Check if expiration exists in payload
    if "expires_at" not in req.payload:
        return {"valid": False}
    
    # Validate expiration
    expires_at = req.payload["expires_at"]
    try:
        # Parse expiration time (ISO format with 'Z' suffix)
        expiration_time = datetime.datetime.fromisoformat(expires_at.replace('Z', ''))
        current_time = datetime.datetime.utcnow()
        
        if current_time > expiration_time:
            return {"valid": False}
    except ValueError:
        return {"valid": False}
    
    return {"valid": True}
