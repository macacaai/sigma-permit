import asyncio, logging, datetime, json, requests, os
from dateutil.parser import isoparse
from license_controller.config import settings
from common.models import SignedLicense  # For new license format

logging.basicConfig(level="INFO")
logger = logging.getLogger("license-controller")

def days_until(expiry_iso):
    return (isoparse(expiry_iso) - datetime.datetime.utcnow()).days

async def loop():
    while True:
        try:
            # Read license file from configured path
            if not os.path.exists(settings.LICENSE_FILE_PATH):
                remaining = -1
                logger.info("License file not found")
            else:
                with open(settings.LICENSE_FILE_PATH, "r") as f:
                    license_data = json.load(f)
                license_json = SignedLicense(**license_data).payload.dict()
                remaining = days_until(license_json["expires_at"])
                logger.info("License remaining %d days", remaining)
        except Exception:
            remaining = -1
            logger.info("License invalid or missing")

        if remaining < 0 or remaining <= settings.RENEW_THRESHOLD_DAYS:
            logger.info("Fetching new license from server")
            try:
                resp = requests.post(settings.FETCH_URL, 
                                    json={"public_key": settings.PUBLIC_KEY}, 
                                    timeout=15)
                if resp.status_code == 200:
                    # Write new license to file
                    new_lic = resp.json()
                    with open(settings.LICENSE_FILE_PATH, "w") as f:
                        json.dump(new_lic, f)
                    logger.info("License updated at %s", settings.LICENSE_FILE_PATH)
                else:
                    logger.error("Fetch failed %s %s", resp.status_code, resp.text)
            except Exception as ex:
                logger.error("Error calling license server: %s", ex)
        await asyncio.sleep(settings.CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    asyncio.run(loop())
