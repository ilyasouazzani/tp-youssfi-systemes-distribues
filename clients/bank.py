from http.client import HTTPConnection
import json
from urllib.request import Request, urlopen


UNAVAILABLE = "L’assistant est temporairement indisponible."


def post_json(url, payload, timeout):
    request = Request(url, data=json.dumps(payload).encode("utf-8"),
                      headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=timeout) as response:
        return json.load(response)


def ask_bank(question):
    if not 1 <= len(question.strip()) <= 1000:
        return "Pose une question de 1 à 1000 caractères."
    try:
        connection = HTTPConnection("127.0.0.1", 8085, timeout=60)
        try:
            connection.request("POST", "/api/chat", body=json.dumps({"question": question}),
                               headers={"Content-Type": "application/json"})
            with connection.getresponse() as response:
                if response.status != 200:
                    return UNAVAILABLE
                return json.load(response)["answer"]
        finally:
            connection.close()
    except (OSError, ValueError, KeyError):
        return UNAVAILABLE
