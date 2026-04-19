import requests

HF_API = "https://api-inference.huggingface.co/feature-extraction/sentence-transformers/all-MiniLM-L6-v2"
HF_KEY = "your_hf_api_key"

def get_embedding(text):
    response = requests.post(
        HF_API,
        headers={"Authorization": f"Bearer {HF_KEY}"},
        json={"inputs": text[:1000]}
    )

    return response.json()[0]