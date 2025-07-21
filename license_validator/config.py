import os

class Settings:
    LICENSE_FILE_PATH: str = os.getenv("LICENSE_FILE_PATH", "/var/license/license.json")
    TRUSTED_PUBLIC_KEY: str = os.getenv("TRUSTED_PUBLIC_KEY")

settings = Settings()
