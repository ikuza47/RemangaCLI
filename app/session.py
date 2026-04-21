import json
from pathlib import Path

from remanga import Remanga

CONFIG_DIR = Path.home() / ".remangacli"
CONFIG_FILE = CONFIG_DIR / "session.json"


def load_session() -> dict | None:
    if not CONFIG_FILE.exists():
        return None
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "access_token" not in data:
            return None
        return data
    except (json.JSONDecodeError, OSError):
        return None


def save_session(client: Remanga) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    cookies = {key: value for key, value in client.session.cookies.items()}
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "access_token": client.access_token,
            "user_id": client.user_id,
            "cookies": cookies,
        }, f)


def remove_session() -> None:
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()


def restore_client(data: dict) -> Remanga:
    client = Remanga()
    client.access_token = data["access_token"]
    client.user_id = data.get("user_id")
    client.session.headers["Authorization"] = f"Bearer {client.access_token}"
    for name, value in data.get("cookies", {}).items():
        client.session.cookies.set(name, value, domain=".remanga.org")
    return client
