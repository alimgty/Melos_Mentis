import requests

# Mistral AI API Key
MISTRAL_API_KEY = "mRu9GUqTjWOZa7eyuramuqkU20nDuk7U"  # Replace with your actual key
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"

# Function to get response from Mistral AI
def get_bot_response(prompt):
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json",
    }
    
    data = {
        "model": "mistral-medium",
        "messages": [{"role": "system", "content": "You are a helpful therapist."},
                     {"role": "user", "content": prompt}],
        "temperature": 0.7,
    }

    response = requests.post(MISTRAL_API_URL, json=data, headers=headers)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return "I'm here to help, but I'm having trouble responding right now."