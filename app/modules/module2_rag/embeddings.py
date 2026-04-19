import os
import requests
from dotenv import load_dotenv

load_dotenv()

HF_API = "https://api-inference.huggingface.co/models/sentence-transformers/all-MiniLM-L6-v2"
HF_KEY = os.getenv("HF_API_KEY")


def get_embedding(text):

    try:
        response = requests.post(
            HF_API,
            headers={
                "Authorization": f"Bearer {HF_KEY}",
                "Content-Type": "application/json"
            },
            json={"inputs": text[:1000]},
            timeout=10
        )

        if response.status_code != 200:
            print("❌ HF ERROR:", response.text)
            return [0.0] * 384

        data = response.json()

        return data[0] if isinstance(data, list) else [0.0] * 384

    except Exception as e:
        print("⚠️ Embedding Error:", str(e))
        return [0.0] * 384