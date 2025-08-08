import base64
import httpx
import json

# Load image and encode in base64
with open("72dbc5f7-51f4-423e-b188-0ddfbffd2c50.png", "rb") as f:
    base64_image = base64.b64encode(f.read()).decode("utf-8")

# Create data URL
data_url = f"data:image/png;base64,{base64_image}"

# Request payload
payload = {
    "model": "qwen/qwen2.5-vl-72b-instruct:free",
    "messages": [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Extract the text from this image."},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": data_url
                    }
                }
            ]
        }
    ]
}

# Custom headers (OpenRouter API)
headers = {
    "Authorization": "Bearer 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",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://your-site.com",   # Optional but recommended
    "X-Title": "Your App Name"                 # Optional but recommended
}

# Send request using httpx
response = httpx.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)

# Output the result
if response.status_code == 200:
    result = response.json()
    print(result["choices"][0]["message"]["content"])
else:
    print("Error:", response.status_code, response.text)
