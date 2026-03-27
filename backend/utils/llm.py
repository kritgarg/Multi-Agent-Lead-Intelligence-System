import os
from groq import AsyncGroq
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

client = None
if GROQ_API_KEY:
    client = AsyncGroq(api_key=GROQ_API_KEY)
    print("✅ Groq client initialized successfully")
else:
    print("⚠️  No GROQ_API_KEY found in .env file!")


async def ask_llm(prompt: str) -> str:
    if not client:
        print("❌ LLM Error: No API key configured")
        return "Not Available - LLM API Key missing"

    try:
        print(f"🤖 Sending prompt to LLM ({len(prompt)} chars)...")

        chat_completion = await client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful business research assistant. Always respond with accurate, structured information."
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            max_tokens=1024,
        )

        response = chat_completion.choices[0].message.content
        print(f"✅ LLM responded ({len(response)} chars)")
        return response

    except Exception as e:
        print(f"❌ LLM Error: {e}")
        return "Not Available"
