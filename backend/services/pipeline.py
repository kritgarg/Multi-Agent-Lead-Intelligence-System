import asyncio
from agents.researcher import researcher_agent
from agents.contact_finder import contact_agent
from agents.outreach_writer import outreach_agent


async def process_company(company: str, location: str) -> dict:
    print(f"\n{'🚀'*20}")
    print(f"PIPELINE START: {company} ({location})")
    print(f"{'🚀'*20}\n")

    try:
        research = await researcher_agent(company, location)

        profile = research.get("profile", "Not Available")
        combined_text = research.get("combined_text", "")
        links = research.get("links", [])

        contact = await contact_agent(combined_text, links, company)

        message = await outreach_agent(profile, contact, company)

        print(f"\n✅ PIPELINE COMPLETE for '{company}'")

        return {
            "company": company,
            "profile": profile,
            "contact": contact,
            "message": message,
            "sources": links
        }

    except Exception as e:
        print(f"\n❌ PIPELINE ERROR for '{company}': {e}")
        return {
            "company": company,
            "profile": f"Error during processing: {str(e)}",
            "contact": {
                "phone": "Not Available",
                "email": "Not Available",
                "whatsapp": "Not Available",
                "source": "Not Available"
            },
            "message": f"Hi {company}! We at Brokai Labs help businesses automate tasks. Let's connect!",
            "sources": []
        }


async def process_multiple(companies: list) -> list:
    print(f"\n⚡ Processing {len(companies)} companies in parallel...")

    tasks = [
        process_company(c.get("name", ""), c.get("location", ""))
        for c in companies
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    final_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            company_name = companies[i].get("name", "Unknown")
            final_results.append({
                "company": company_name,
                "profile": f"Error: {str(result)}",
                "contact": {
                    "phone": "Not Available",
                    "email": "Not Available",
                    "whatsapp": "Not Available",
                    "source": "Not Available"
                },
                "message": f"Hi! We at Brokai Labs help businesses automate tasks. Let's connect!",
                "sources": []
            })
        else:
            final_results.append(result)

    return final_results
