import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def get_links(query: str) -> dict:
    print(f"🔍 Searching for: '{query}'")

    links = []
    snippets = []

    try:
        from ddgs import DDGS
        results = DDGS().text(query, max_results=3)
        for r in results:
            url = r.get("href", "")
            title = r.get("title", "")
            body = r.get("body", "")
            if url:
                links.append(url)
            if body:
                snippets.append(f"{title}: {body}")
    except Exception as e:
        print(f"   ⚠️  ddgs search failed: {e}")

    if not links:
        try:
            from googlesearch import search as gsearch
            print("   Trying googlesearch-python as fallback...")
            links = list(gsearch(query, num_results=3))
        except Exception as e:
            print(f"   ⚠️  googlesearch also failed: {e}")

    if not links:
        words = query.lower().split()
        company_slug = words[0] if words else "unknown"
        fallback = f"https://www.{company_slug}.com"
        print(f"   Using fallback URL: {fallback}")
        links = [fallback]

    snippet_text = "\n".join(snippets)
    print(f"   📎 Found {len(links)} links")
    print(f"   📝 Got {len(snippet_text)} chars of search snippets")

    return {
        "links": links,
        "snippets": snippet_text,
    }


def scrape_url(url: str) -> str:
    try:
        print(f"   📄 Scraping: {url}")

        response = requests.get(url, headers=HEADERS, timeout=8, allow_redirects=True)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup(["script", "style", "nav", "footer", "iframe", "noscript", "svg"]):
            tag.extract()

        main_content = soup.find("main") or soup.find("article") or soup.find("body")

        if main_content:
            text = main_content.get_text(separator=" ")
        else:
            text = soup.get_text(separator=" ")

        lines = text.splitlines()
        clean_lines = []
        for line in lines:
            line = line.strip()
            if line and len(line) > 3:
                clean_lines.append(line)

        text = " ".join(clean_lines)

        while "  " in text:
            text = text.replace("  ", " ")

        result = text[:3000]
        print(f"      ✅ Scraped {len(result)} chars")
        return result

    except requests.exceptions.Timeout:
        print(f"      ⏱️  Timeout scraping {url}")
        return ""
    except requests.exceptions.HTTPError as e:
        print(f"      🚫 HTTP error ({e})")
        return ""
    except Exception as e:
        print(f"      ❌ Error scraping {url}: {e}")
        return ""
