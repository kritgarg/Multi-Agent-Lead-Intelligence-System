import re
import json
import asyncio
from urllib.parse import urlparse
from utils.scraper import scrape_url
from utils.llm import ask_llm

# ─── In-memory cache to avoid reprocessing same company ───────────────────────
_cache: dict = {}

# ─── Regex Patterns ───────────────────────────────────────────────────────────
PHONE_REGEX = r'(\+91[\-\s]?)?[6-9]\d{9}'
EMAIL_REGEX = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.(com|in|org|net|co\.in)'

# Emails/domains to discard as garbage
_BAD_EMAIL_KEYWORDS = ['example', 'test', 'sentry', 'noreply', 'no-reply', 'donotreply']
_BAD_EMAIL_EXTS     = ['.png', '.jpg', '.jpeg', '.svg', '.gif', '.webp', '.css', '.js']
_BAD_EMAIL_DOMAINS  = ['sentry.io', 'wixpress.com', 'w3.org', 'schema.org', 'googleapis.com']

# ─── Link ranking weights ─────────────────────────────────────────────────────
_DIRECTORY_DOMAINS = ['justdial', 'indiamart', 'sulekha', 'yellowpages', 'mouthshut', 'tradeindia']
_SKIP_DOMAINS      = ['linkedin.com', 'wikipedia.org', 'facebook.com', 'twitter.com',
                      'instagram.com', 'youtube.com', 'glassdoor.com', 'ambitionbox.com']


# ─── STEP 1: Multi-query search ───────────────────────────────────────────────
def get_search_links(company: str) -> tuple:
    """Run targeted queries. Returns (links, snippet_text)."""
    from ddgs import DDGS

    queries = [
        f"{company} contact email phone",
        f"{company} justdial indiamart contact",
    ]

    seen = set()
    links = []
    snippets = []

    for query in queries:
        try:
            # Limit to 4 results per query to keep it fast
            results = list(DDGS().text(query, max_results=4))
            for r in results:
                url = r.get("href", "").strip()
                body = r.get("body", "")
                if url and url not in seen:
                    seen.add(url)
                    links.append(url)
                if body:
                    snippets.append(body)
        except Exception as e:
            print(f"   ⚠️  DDG query failed [{query[:40]}]: {e}")

    snippet_text = " ".join(snippets)
    print(f"   📎 Collected {len(links)} unique links, {len(snippet_text)} chars of snippets")
    return links, snippet_text


# ─── STEP 2: Link ranking ─────────────────────────────────────────────────────
def rank_links(links: list, company_domain: str = "") -> list:
    """Score and sort links using netloc (domain) not full URL to avoid false matches."""

    def get_netloc(url: str) -> str:
        try:
            return urlparse(url).netloc.lower()
        except Exception:
            return url.lower()

    def score(url: str) -> int:
        netloc = get_netloc(url)
        s = 0
        # Score by actual domain, not full URL path (fixes quora.com/...justdial... bug)
        if any(netloc == d or netloc.endswith("." + d) for d in _DIRECTORY_DOMAINS): s += 5
        if company_domain and company_domain in netloc:                               s += 5
        if url.startswith("https://"):                                                s += 1
        if ".com" in netloc or ".in" in netloc:                                       s += 2
        if "linkedin.com" in netloc:                                                  s -= 3
        if "wikipedia.org" in netloc:                                                 s -= 5
        if any(d in netloc for d in ['quora.com','facebook.','twitter.','instagram.','youtube.']): s -= 4
        return s

    ranked = sorted(links, key=score, reverse=True)
    print(f"   🏆 Top link after ranking: {ranked[0] if ranked else 'none'}")
    return ranked


# ─── STEP 3: Strong regex extraction ──────────────────────────────────────────
def extract_contacts(text: str) -> dict:
    """Extract best phone + email from text using strict patterns."""
    # Phones
    phones = re.findall(PHONE_REGEX, text)
    clean_phones = []
    for match in phones:
        # re.findall returns tuples when groups exist — flatten
        full = match if isinstance(match, str) else "".join(match)
        digits = re.sub(r'\D', '', full)
        if len(digits) >= 10 and full not in clean_phones:
            clean_phones.append(full.strip())

    # Rebuild phone from raw text to get full match (group issue workaround)
    raw_phones = re.findall(r'(\+91[\-\s]?[6-9]\d{9}|[6-9]\d{9})', text)
    raw_phones = list(dict.fromkeys(raw_phones))  # deduplicate preserving order

    # Emails
    raw_emails = re.findall(EMAIL_REGEX, text, re.IGNORECASE)
    # re returns tuples for groups — rebuild from full pattern
    all_emails = re.findall(
        r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.(com|in|org|net|co\.in)',
        text, re.IGNORECASE
    )
    # Reconstruct full email strings
    clean_emails = []
    for match in re.finditer(
        r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.(com|in|org|net|co\.in)',
        text, re.IGNORECASE
    ):
        email = match.group(0).lower()
        if any(email.endswith(ext) for ext in _BAD_EMAIL_EXTS):       continue
        if any(kw in email for kw in _BAD_EMAIL_KEYWORDS):            continue
        if any(domain in email for domain in _BAD_EMAIL_DOMAINS):     continue
        if len(email) < 6:                                            continue
        if email not in clean_emails:
            clean_emails.append(email)

    return {
        "phone": raw_phones[0] if raw_phones else None,
        "email": clean_emails[0] if clean_emails else None,
    }


# ─── STEP 4: Confidence scoring ───────────────────────────────────────────────
def score_contact(contact: dict, source: str) -> int:
    """Score a contact result for ranking."""
    s = 0
    if contact.get("phone"): s += 5
    if contact.get("email"): s += 5
    src = source.lower()
    if any(d in src for d in _DIRECTORY_DOMAINS): s += 3
    # Penalise low-quality sources
    if "wikipedia" in src or "linkedin" in src:   s -= 4
    return s


# ─── STEP 5: /contact page scraper ───────────────────────────────────────────
async def try_contact_pages(domain: str) -> list:
    """Scrape common contact-page paths and return a list of contact dicts."""
    paths = ["/contact", "/contact-us", "/contactus", "/about", "/reach-us"]
    results = []

    for path in paths:
        url = domain + path
        print(f"      🌐 Trying contact page: {url}")
        text = await asyncio.to_thread(scrape_url, url)
        if not text:
            continue
        contacts = extract_contacts(text)
        if contacts["phone"] or contacts["email"]:
            results.append({**contacts, "source": url})
            if contacts["phone"] and contacts["email"]:
                break  # Both found — no need to continue

    return results


# ─── STEP 6: LLM fallback ─────────────────────────────────────────────────────
async def llm_extract(text: str, company: str) -> dict:
    """Ask the LLM to extract contacts from concatenated scraped text."""
    snippet = text[-3000:] if len(text) > 3000 else text
    if not snippet.strip():
        return {"phone": None, "email": None}

    prompt = f"""You are extracting contact information for the company "{company}".

Text from their website and directories is below.
Extract ONE valid business phone number and ONE valid business email.

Rules:
- Return ONLY valid JSON: {{"email": "...", "phone": "..."}}
- Phone must be a real Indian mobile or landline (10 digits).
- Ignore fake/system emails (noreply, sentry, example, test).
- If a field is not found, use null (not a string).
- Do NOT make up any contact info.

--- TEXT ---
{snippet}
--- END ---"""

    raw = await ask_llm(prompt)

    try:
        s = raw.strip()
        if "```json" in s: s = s.split("```json")[1].split("```")[0].strip()
        elif "```" in s:   s = s.split("```")[1].split("```")[0].strip()
        start, end = s.find("{"), s.rfind("}") + 1
        if start != -1 and end > start:
            data = json.loads(s[start:end])
            return {
                "phone": data.get("phone") or None,
                "email": (data.get("email") or "").lower() or None,
            }
    except Exception as e:
        print(f"      ⚠️  LLM JSON parse failed: {e}")

    return {"phone": None, "email": None}


# ─── HELPER: detect official domain ──────────────────────────────────────────
def _detect_official_domain(links: list) -> str:
    for url in links:
        low = url.lower()
        if any(d in low for d in _SKIP_DOMAINS + _DIRECTORY_DOMAINS):
            continue
        try:
            parsed = urlparse(url)
            if parsed.scheme and parsed.netloc:
                return f"{parsed.scheme}://{parsed.netloc}"
        except Exception:
            pass
    return ""


# ─── MAIN AGENT ───────────────────────────────────────────────────────────────
async def contact_agent(scraped_text: str, links: list, company: str) -> dict:
    print(f"\n{'='*50}")
    print(f"📞 CONTACT FINDER AGENT: Finding contacts for '{company}'")
    print(f"{'='*50}")

    # Cache check
    cache_key = company.lower().strip()
    if cache_key in _cache:
        print(f"   ✅ Cache hit for '{company}'")
        return _cache[cache_key]

    all_results: list[dict] = []
    collected_text = scraped_text or ""

    # ── Step 1 & 2: Multi-query search + rank ─────────────────────────────────
    print("   🔎 Step 1-2: Running multi-query search and ranking links...")
    official_domain = _detect_official_domain(links)
    search_links, search_snippets = await asyncio.to_thread(get_search_links, company)

    # Immediately try regex on search snippets — free, fast, no extra scraping
    if search_snippets:
        collected_text += "\n" + search_snippets
        snippet_contacts = extract_contacts(search_snippets)
        if snippet_contacts["phone"] or snippet_contacts["email"]:
            score = score_contact(snippet_contacts, "search_snippet")
            all_results.append({**snippet_contacts, "source": "search_snippet", "score": score})
            print(f"      ✅ Found contacts in search snippets (no scraping needed!)")

    all_links = list(dict.fromkeys(links + search_links))  # merge, deduplicate
    ranked    = rank_links(all_links, official_domain)

    # ── Step 3 & 4: Scrape top sources + regex ────────────────────────────────
    print("   🌐 Step 3-4: Scraping top ranked sources...")
    for url in ranked[:4]:
        text = await asyncio.to_thread(scrape_url, url)
        if not text:
            continue
        collected_text += "\n" + text
        contacts = extract_contacts(text)
        if contacts["phone"] or contacts["email"]:
            score = score_contact(contacts, url)
            all_results.append({**contacts, "source": url, "score": score})
            print(f"      ✅ Extracted from {url} (score: {score})")

    # Also try regex on the original researcher text
    if scraped_text:
        contacts = extract_contacts(scraped_text)
        if contacts["phone"] or contacts["email"]:
            score = score_contact(contacts, ranked[0] if ranked else "")
            all_results.append({**contacts, "source": "researcher_text", "score": score})

    # ── Step 5: Score and pick best so far ───────────────────────────────────
    all_results.sort(key=lambda x: x["score"], reverse=True)
    best = all_results[0] if all_results else {"phone": None, "email": None, "source": ""}

    # ── Step 6: /contact page fallback ───────────────────────────────────────
    if not best.get("phone") or not best.get("email"):
        if official_domain:
            print("   🏠 Step 6: Trying /contact pages on official domain...")
            contact_page_results = await try_contact_pages(official_domain)
            for r in contact_page_results:
                r["score"] = score_contact(r, r["source"]) + 2  # bonus for contact page
                all_results.append(r)
                collected_text += "\n" + r.get("source", "")

            all_results.sort(key=lambda x: x["score"], reverse=True)
            best = all_results[0] if all_results else best

    # ── Step 7: LLM fallback (ONCE, only if still missing data) ──────────────
    if not best.get("phone") or not best.get("email"):
        print("   🤖 Step 7: LLM fallback — extracting from collected text...")
        llm_data = await llm_extract(collected_text, company)

        if not best.get("phone") and llm_data.get("phone"):
            best["phone"] = llm_data["phone"]
            print(f"      ✅ LLM found phone: {llm_data['phone']}")

        if not best.get("email") and llm_data.get("email"):
            best["email"] = llm_data["email"]
            print(f"      ✅ LLM found email: {llm_data['email']}")

    # ── Build final output ────────────────────────────────────────────────────
    phone  = best.get("phone") or "Not Available"
    email  = best.get("email") or "Not Available"
    source = best.get("source") or (ranked[0] if ranked else "Not Available")

    result = {
        "phone":    phone,
        "email":    email,
        "whatsapp": phone if phone != "Not Available" else "Not Available",
        "source":   source,
    }

    print(f"\n   📋 FINAL CONTACT INFO:")
    print(f"      Email:    {result['email']}")
    print(f"      Phone:    {result['phone']}")
    print(f"      WhatsApp: {result['whatsapp']}")
    print(f"      Source:   {result['source']}")

    # Cache result
    _cache[cache_key] = result
    return result
