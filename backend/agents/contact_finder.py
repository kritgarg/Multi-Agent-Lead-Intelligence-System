import re
import json
import asyncio
from utils.scraper import scrape_url
from utils.llm import ask_llm

EMAIL_PATTERN = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

PHONE_PATTERNS = [
    r'\+?\d{1,3}[-.\s]?\(?\d{2,5}\)?[-.\s]?\d{3,5}[-.\s]?\d{3,5}',
    r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
    r'\+\d{10,13}',
]

BAD_EMAIL_ENDINGS = ['.png', '.jpg', '.jpeg', '.svg', '.gif', '.webp', '.css', '.js']
BAD_EMAIL_DOMAINS = ['example.com', 'sentry.io', 'wixpress.com', 'w3.org', 'schema.org', 'googleapis.com']


def _extract_emails(text: str) -> list:
    emails = re.findall(EMAIL_PATTERN, text)
    valid = []
    for email in emails:
        email_lower = email.lower()
        if any(email_lower.endswith(ext) for ext in BAD_EMAIL_ENDINGS):
            continue
        if any(domain in email_lower for domain in BAD_EMAIL_DOMAINS):
            continue
        if len(email) < 6:
            continue
        valid.append(email)
    return valid


def _extract_phones(text: str) -> list:
    phones = []
    for pattern in PHONE_PATTERNS:
        matches = re.findall(pattern, text)
        phones.extend(matches)
    valid = []
    for phone in phones:
        digits_only = re.sub(r'\D', '', phone)
        if len(digits_only) >= 10:
            valid.append(phone)
    return valid


def _get_company_domain(links: list) -> str:
    skip_domains = [
        'wikipedia.org', 'linkedin.com', 'facebook.com', 'twitter.com',
        'youtube.com', 'instagram.com', 'ambitionbox.com', 'glassdoor.com',
        'justdial.com', 'indiamart.com', 'crunchbase.com', 'github.com',
        'cleartax.in', 'zaubacorp.com', 'tofler.in'
    ]
    for link in links:
        link_lower = link.lower()
        if any(domain in link_lower for domain in skip_domains):
            continue
        try:
            from urllib.parse import urlparse
            parsed = urlparse(link)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            return base_url
        except:
            pass
    return ""


async def contact_agent(scraped_text: str, links: list, company: str) -> dict:
    print(f"\n{'='*50}")
    print(f"📞 CONTACT FINDER AGENT: Finding contacts for '{company}'")
    print(f"{'='*50}")

    found_email = None
    found_phone = None
    contact_source = links[0] if links else "Not Available"
    all_text_collected = scraped_text or ""

    print("   📋 Step 1: Checking researcher's scraped text with regex...")

    if scraped_text:
        emails = _extract_emails(scraped_text)
        phones = _extract_phones(scraped_text)
        if emails:
            found_email = emails[0]
            print(f"      ✅ Found email: {found_email}")
        if phones:
            found_phone = phones[0]
            print(f"      ✅ Found phone: {found_phone}")

    if not found_email or not found_phone:
        print("      ❌ Incomplete — moving to Step 2")

    if not found_email or not found_phone:
        print("   🔍 Step 2: Searching DDG specifically for contact info...")
        try:
            from ddgs import DDGS
            contact_query = f'"{company}" contact email phone number'
            results = await asyncio.to_thread(
                lambda: DDGS().text(contact_query, max_results=5)
            )

            contact_snippets = []
            for r in results:
                snippet = f"{r.get('title', '')} {r.get('body', '')}"
                contact_snippets.append(snippet)

                url = r.get("href", "")
                if any(d in url.lower() for d in ["justdial", "indiamart", "sulekha", "yellowpages", "mouthshut"]):
                    print(f"      📂 Found directory listing: {url}")
                    directory_text = await asyncio.to_thread(scrape_url, url)
                    if directory_text:
                        contact_snippets.append(directory_text)
                        contact_source = url

            snippet_text = " ".join(contact_snippets)
            all_text_collected += "\n" + snippet_text

            if not found_email:
                emails = _extract_emails(snippet_text)
                if emails:
                    found_email = emails[0]
                    print(f"      ✅ Found email from search: {found_email}")

            if not found_phone:
                phones = _extract_phones(snippet_text)
                if phones:
                    found_phone = phones[0]
                    print(f"      ✅ Found phone from search: {found_phone}")

        except Exception as e:
            print(f"      ⚠️  Contact search failed: {e}")

    if not found_email or not found_phone:
        print("      ❌ Still incomplete — moving to Step 3")

    if not found_email or not found_phone:
        print("   🌐 Step 3: Trying to scrape company's contact page...")
        company_domain = _get_company_domain(links)

        if company_domain:
            contact_paths = ["/contact", "/contact-us", "/contactus", "/about/contact", "/reach-us"]

            for path in contact_paths:
                contact_url = company_domain + path
                print(f"      Trying: {contact_url}")

                contact_page_text = await asyncio.to_thread(scrape_url, contact_url)

                if contact_page_text:
                    all_text_collected += "\n" + contact_page_text
                    contact_source = contact_url

                    if not found_email:
                        emails = _extract_emails(contact_page_text)
                        if emails:
                            found_email = emails[0]
                            print(f"      ✅ Found email on contact page: {found_email}")

                    if not found_phone:
                        phones = _extract_phones(contact_page_text)
                        if phones:
                            found_phone = phones[0]
                            print(f"      ✅ Found phone on contact page: {found_phone}")

                    if found_email and found_phone:
                        break
        else:
            print("      ⚠️  Could not determine company domain")

    if not found_email or not found_phone:
        print("      ❌ Still incomplete — moving to Step 4 (LLM)")

    if not found_email or not found_phone:
        print("   🤖 Step 4: Asking LLM to extract contacts from all text...")

        llm_text = all_text_collected[-3000:] if len(all_text_collected) > 3000 else all_text_collected

        if llm_text.strip():
            prompt = f"""You are extracting contact information for the company "{company}".

Below is text from their website, search results, and directory listings.
Find the BEST contact email and phone number for this company.

Rules:
- Return ONLY a valid JSON object, nothing else
- Format: {{"email": "...", "phone": "...", "whatsapp": "..."}}
- For phone, include country code if available (e.g. +91...)
- If a field is truly not found anywhere, use "Not Available"
- Prefer business/sales/info emails over personal ones
- Do NOT make up contacts, only extract what's actually in the text

--- TEXT ---
{llm_text}
--- END ---"""

            llm_response = await ask_llm(prompt)

            try:
                json_str = llm_response.strip()
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0].strip()
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].split("```")[0].strip()

                start = json_str.find("{")
                end = json_str.rfind("}") + 1
                if start != -1 and end > start:
                    json_str = json_str[start:end]

                data = json.loads(json_str)

                if not found_email and data.get("email") and data["email"] != "Not Available":
                    found_email = data["email"]
                    print(f"      ✅ LLM found email: {found_email}")

                if not found_phone and data.get("phone") and data["phone"] != "Not Available":
                    found_phone = data["phone"]
                    print(f"      ✅ LLM found phone: {found_phone}")

            except (json.JSONDecodeError, Exception) as e:
                print(f"      ⚠️  Could not parse LLM response: {e}")

    contact_info = {
        "email": found_email if found_email else "Not Available",
        "phone": found_phone if found_phone else "Not Available",
        "whatsapp": "Not Available",
        "source": contact_source
    }

    if found_phone:
        contact_info["whatsapp"] = found_phone

    print(f"\n   📋 FINAL CONTACT INFO:")
    print(f"      Email:    {contact_info['email']}")
    print(f"      Phone:    {contact_info['phone']}")
    print(f"      WhatsApp: {contact_info['whatsapp']}")
    print(f"      Source:   {contact_info['source']}")

    return contact_info
