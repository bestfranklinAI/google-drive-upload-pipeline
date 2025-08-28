import os
from dataclasses import dataclass
from dotenv import load_dotenv
load_dotenv()


@dataclass
class Config:
    credentials_path: str
    folder_id: str
    poll_interval: int
    upload_enabled: bool = True


def load_config() -> Config:
    creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    folder = os.getenv("FOLDER_ID")
    interval = os.getenv("POLL_INTERVAL")
    upload_env = os.getenv("UPLOAD_ENABLED", "true").lower()
    upload = upload_env in ("1", "true", "yes", "on")

    if not creds or not os.path.exists(creds):
        raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS missing or file does not exist")
    if not folder:
        raise RuntimeError("FOLDER_ID missing")
    if not interval:
        raise RuntimeError("POLL_INTERVAL missing")

    return Config(credentials_path=creds, folder_id=folder, poll_interval=int(interval), upload_enabled=upload)
