import os

class Settings:
    LICENSE_FILE_PATH: str = os.getenv("LICENSE_FILE_PATH", "/var/license/license.json")  # Configurable path
    LICENSE_SECRET: str = os.getenv("LICENSE_SECRET", "license-data")
    NAMESPACE: str = os.getenv("LICENSE_NAMESPACE", os.getenv("POD_NAMESPACE", "default"))
    PUBLIC_KEY: str = os.getenv("PUBLIC_KEY", "")
    FETCH_URL: str = os.getenv("FETCH_URL", "http://license-server:8000/admin/licenses/fetch")
    RENEW_THRESHOLD_DAYS: int = int(os.getenv("RENEW_THRESHOLD_DAYS", "7"))
    CHECK_INTERVAL_SECONDS: int = int(os.getenv("CHECK_INTERVAL_SECONDS", str(24*60*60)))
settings = Settings()
