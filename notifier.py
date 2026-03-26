import logging
import requests

logger = logging.getLogger(__name__)


class Notifier:
    def __init__(self, webhook_url: str = ""):
        self.webhook_url = webhook_url.strip()
        self.enabled = bool(self.webhook_url)

        if self.enabled:
            logger.info("Discord notifier enabled")
        else:
            logger.info("Notifier disabled (no webhook URL)")

    def send(self, message: str) -> None:
        logger.info(f"[NOTIFY] {message}")

        if not self.enabled:
            return

        try:
            payload = {"content": message}
            resp = requests.post(self.webhook_url, json=payload, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            logger.warning(f"Failed to send notification: {e}")
