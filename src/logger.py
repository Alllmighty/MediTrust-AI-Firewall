import logging
from pathlib import Path

class SecurityLogger:
    """Handles operational logging for the Semantic Firewall."""

    def __init__(self) -> None:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        self.logger = logging.getLogger("MediTrust")
        if not self.logger.handlers:
            self.logger.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)a | %(levelname)s | %(message)s')

            file_handler = logging.FileHandler(log_dir / "security.log", encoding="utf-8")
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def log_threat(self, threat_type: str, details: str) -> None:
        self.logger.warning(f"THREAT BLOCKED: {threat_type} | {details}")

    def log_safe(self, details: str) -> None:
        self.logger.info(f"SAFE TRANSACTION: {details}")