import base64
import os

from firebase_admin import initialize_app

from app.app import create_app
from app.week_plans import provide_anthropic_client


def decode_kubernetes_secret_file():
    base_64_secret_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if base_64_secret_file:
        with open(base_64_secret_file, "rb") as f:
            encoded_data = f.read()
            if encoded_data.decode("utf-8").startswith("{"):
                return
            decoded_data = base64.b64decode(encoded_data).decode("utf-8")

        decoded_secret_file = "gym-tracking-firebase-key.json"
        with open(decoded_secret_file, "w") as f:
            f.write(decoded_data)

        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = decoded_secret_file


def export_anthropic_api_key():
    try:
        with open("/mnt/anthropic-api-key/key", "r") as f:
            os.environ["ANTHROPIC_API_KEY"] = f.read()
    except Exception as e:
        print(e)
        print("Anthropic API key secret not found")


# Initialize the app
decode_kubernetes_secret_file()
initialize_app()
export_anthropic_api_key()
app = create_app(dependencies={"anthropic_client": provide_anthropic_client})
