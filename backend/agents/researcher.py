import asyncio
from utils.scraper import get_links, scrape_url
from utils.llm import ask_llm


async def researcher_agent(company: str, location: str) -> dict:
    print(f"\n{'='*50}")
    print(f"🔬 RESEARCHER AGENT: Starting research on '{company}' in '{location}'")
    print(f"{'='*50}")

    query = f"{company} {location} company".strip()

    search_results = await asyncio.to_thread(get_links, query)

    links = search_results.get("links", [])
    snippets = search_results.get("snippets", "")

    if not links and not snippets:
        print(f"   ⚠️  No results found for '{company}'")
        return {
            "profile": "Not Available - could not find information online.",
            "combined_text": "",
            "links": []
        }

    scraped_texts = []
    for link in links:
        text = await asyncio.to_thread(scrape_url, link)
        if text:
            scraped_texts.append(text)

    scraped_combined = "\n\n---\n\n".join(scraped_texts)

    combined_text = ""

    if scraped_combined:
        combined_text = scraped_combined[:4000]

    if snippets:
        combined_text += f"\n\n--- SEARCH SNIPPETS ---\n{snippets[:1500]}"

    if not combined_text.strip():
        print(f"   ⚠️  No text available for '{company}'")
        return {
            "profile": "Not Available - could not extract any text.",
            "combined_text": "",
            "links": links
        }

    print(f"   📝 Total text for LLM: {len(combined_text)} chars")

    prompt = f"""You are analyzing a company called "{company}" located in "{location}".

Below is text scraped from their website and search results. Based on this text, provide a SHORT summary (3-5 sentences max) covering:

1. What the company does (main products/services)
2. Their industry
3. Company size or scale (if mentioned)
4. Their digital presence

Keep it concise and factual. If something is not clear from the text, say "Not mentioned".

--- SCRAPED TEXT ---
{combined_text}
--- END ---

Write the summary as plain text paragraphs, NOT as JSON."""

    profile = await ask_llm(prompt)

    print(f"   ✅ Research complete for '{company}'")

    return {
        "profile": profile,
        "combined_text": combined_text,
        "links": links
    }
