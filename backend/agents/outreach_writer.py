from utils.llm import ask_llm


async def outreach_agent(profile: str, contact: dict, company: str) -> str:
    print(f"\n{'='*50}")
    print(f"✉️  OUTREACH WRITER AGENT: Writing message for '{company}'")
    print(f"{'='*50}")

    prompt = f"""Write a short WhatsApp outreach message to "{company}".

Context about the company:
{profile}

Rules:
- Keep it under 50 words
- Be friendly and conversational (WhatsApp style, not formal email)
- Mention what their company does briefly
- Mention a problem they might face (missed calls, lead management, automation)
- End with a call to action
- Sign off from "Team Brokai Labs"
- Do NOT use markdown formatting, emojis are fine
- Output ONLY the message, nothing else"""

    message = await ask_llm(prompt)

    if (
        not message
        or message == "Not Available"
        or "LLM API Key missing" in message
        or "error" in message.lower()[:20]
    ):
        print("   ⚠️  Using fallback message")
        return f"Hi {company}! We at Brokai Labs help businesses like yours automate lead management and never miss a customer call. Let's chat about how we can help! - Team Brokai Labs"

    print(f"   ✅ Message generated ({len(message)} chars)")
    return message
