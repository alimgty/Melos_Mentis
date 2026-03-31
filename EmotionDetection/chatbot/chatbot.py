# import requests

# # Mistral AI API Key
# MISTRAL_API_KEY = "3nv0X8H8O94lZI3yUmkDDcFLYZRMwoOE"  # Replace with your actual key
# MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"

# # Function to get response from Mistral AI
# def get_bot_response(prompt):
#     headers = {
#         "Authorization": f"Bearer {MISTRAL_API_KEY}",
#         "Content-Type": "application/json",
#     }
    
#     data = {
#         "model": "mistral-medium",
#         "messages": [{"role": "system", "content": "You are a helpful therapist."},
#                      {"role": "user", "content": prompt}],
#         "temperature": 0.7,
#     }

#     response = requests.post(MISTRAL_API_URL, json=data, headers=headers)

#     if response.status_code == 200:
#         return response.json()["choices"][0]["message"]["content"]
#     else:
#         return "I'm here to help, but I'm having trouble responding right now."

import requests

# Mistral AI API Key
MISTRAL_API_KEY = "3l3ryutp7qao9FPu6zRcHhSQirGrATtg"
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"

# Function to get response from Mistral AI
def get_bot_response(prompt):
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json",
    }
    
    data = {
        "model": "mistral-medium",
        "messages": [
            {"role": "system", "content": "You are a helpful therapist."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
    }

    response = requests.post(MISTRAL_API_URL, json=data, headers=headers)

    if response.status_code == 200:
        try:
            return response.json()["choices"][0]["message"]["content"]
        except:
            return "Unexpected response format."
    else:
        return "I'm here to help, but I'm having trouble responding right now."


# Chat loop
if __name__ == "__main__":
    print("TherapyBot is running! Type 'exit' to quit.\n")
    while True:
        user_text = input("You: ")
        if user_text.lower() in ["exit", "quit"]:
            print("Bot: Take care! Goodbye 👋")
            break
        
        bot_reply = get_bot_response(user_text)
        print("Bot:", bot_reply)
