import os

class Settings:
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    OTEL_EXPORTER_OTLP_ENDPOINT: str = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")
    OTEL_SERVICE_NAME: str = os.getenv("OTEL_SERVICE_NAME", "license-server")
    MASTER_KEY: str = os.getenv("MASTER_KEY")  # Private key for signing licenses
    MASTER_PUBLIC_KEY: str = os.getenv("MASTER_PUBLIC_KEY")  # Public key for verification

settings = Settings()
