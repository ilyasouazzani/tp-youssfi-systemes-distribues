import os
import time
from urllib.error import HTTPError

from bank import ask_bank, post_json


def main():
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    allowed_chat = int(os.environ["TELEGRAM_ALLOWED_CHAT_ID"])
    base = f"https://api.telegram.org/bot{token}/"
    offset = 0
    while True:
        try:
            updates = post_json(base + "getUpdates", {
                "offset": offset, "timeout": 25, "allowed_updates": ["message"],
            }, timeout=35)
            for update in updates["result"]:
                message = update.get("message", {})
                text = message.get("text", "")
                chat = message.get("chat", {})
                if chat.get("id") == allowed_chat and text.startswith("/bank "):
                    answer = ask_bank(text.removeprefix("/bank "))
                    post_json(base + "sendMessage", {
                        "chat_id": allowed_chat, "text": answer[:4000],
                    }, timeout=15)
                offset = update["update_id"] + 1
        except HTTPError as error:
            if error.code in {401, 404, 409}:
                raise SystemExit(f"Telegram a refusé le poll (HTTP {error.code}). Vérifie le jeton et l'absence d'un autre poller/webhook.") from None
            time.sleep(5)
        except (OSError, ValueError, KeyError):
            time.sleep(5)


if __name__ == "__main__":
    main()
