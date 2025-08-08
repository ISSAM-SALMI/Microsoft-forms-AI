from openai import OpenAI

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key="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",
)

completion = client.chat.completions.create(
  extra_headers={
    "HTTP-Referer": "<YOUR_SITE_URL>", # Optional. Site URL for rankings on openrouter.ai.
    "X-Title": "<YOUR_SITE_NAME>", # Optional. Site title for rankings on openrouter.ai.
  },
  model="deepseek/deepseek-r1:free",
  messages=[
    {
      "role": "user",
      "content": "Hola?"
    }
  ]
)

print(completion.choices[0].message.content)
