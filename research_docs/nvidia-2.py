import os
from openai import OpenAI

from dotenv import load_dotenv

load_dotenv()

nvapi_key = os.getenv("NVIDIA_API_KEY")

client = OpenAI(
  base_url = "https://integrate.api.nvidia.com/v1",
  api_key = nvapi_key
)

completion = client.chat.completions.create(
  model="writer/palmyra-med-70b-32k",
  messages=[{"role":"user","content":"what is clinical trial?"}],
  temperature=0.2,
  top_p=0.7,
  max_tokens=1024,
  stream=True
)

for chunk in completion:
  if chunk.choices[0].delta.content is not None:
    print(chunk.choices[0].delta.content, end="")

