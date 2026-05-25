"""
Concert Tracker - Week 2
Feed concert data into Gemini to extract, enrich and summarise each event
"""

import json
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

# ----------------------------
# LOAD CONCERTS FROM WEEK 1
# ----------------------------

def load_concerts(filename="data/concerts.json") -> list[dict]:
    with open(filename, "r") as f:
        return json.load(f)


# ----------------------------
# ASK GEMINI TO ENRICH EACH CONCERT
# ----------------------------

def enrich_concert(concert: dict) -> dict:
    prompt = f"""
    You are a helpful travel and concert assistant based in Singapore.
    
    Here is a concert event:
    - Artist: {concert['artist']}
    - Event: {concert['event_name']}
    - Date: {concert['date']}
    - Venue: {concert['venue']}
    - City: {concert['city']}
    - Country: {concert['country']}
    - Ticket Price Range: {concert['price_range']}

    Please respond in JSON format with these fields:
    - is_local: true if the concert is in Singapore, false otherwise
    - region: one of "Local", "Southeast Asia", "Asia", "International"
    - travel_effort: one of "None", "Easy", "Moderate", "High"
    - summary: one sentence describing this concert opportunity
    - recommendation: one of "Highly Recommended", "Worth Considering", "Skip"
    - reason: one sentence explaining your recommendation

    Only respond with the JSON object, no extra text.
    """

    response = model.generate_content(prompt)
    
    # Clean up response and parse JSON
    text = response.text.strip()
    text = text.replace("```json", "").replace("```", "").strip()
    
    enriched = json.loads(text)
    
    # Merge with original concert data
    return {**concert, **enriched}


def enrich_all_concerts(concerts: list[dict]) -> list[dict]:
    enriched_list = []
    for concert in concerts:
        print(f"Enriching: {concert['artist']} in {concert['city']}...")
        try:
            enriched = enrich_concert(concert)
            enriched_list.append(enriched)
        except Exception as e:
            print(f"  Error: {e}")
            enriched_list.append(concert)  # keep original if AI fails
    return enriched_list


# ----------------------------
# DISPLAY RESULTS
# ----------------------------

def print_enriched_concerts(concerts: list[dict]):
    print("\n" + "=" * 60)
    print(f"{'ENRICHED CONCERT LIST':^60}")
    print("=" * 60)

    for c in concerts:
        print(f"\n🎵 {c['artist']} — {c['city']}, {c['country']}")
        print(f"   📅 {c['date']}")
        print(f"   💰 {c['price_range']}")
        print(f"   🌍 Region: {c.get('region', 'N/A')} | Travel: {c.get('travel_effort', 'N/A')}")
        print(f"   💬 {c.get('summary', '')}")
        print(f"   ✅ {c.get('recommendation', 'N/A')} — {c.get('reason', '')}")


def save_enriched(concerts, filename="data/concerts_enriched.json"):
    os.makedirs("data", exist_ok=True)
    with open(filename, "w") as f:
        json.dump(concerts, f, indent=2)
    print(f"\nSaved to {filename}")


# ----------------------------
# MAIN
# ----------------------------

if __name__ == "__main__":
    print("Loading concerts from Week 1...")
    concerts = load_concerts()
    print(f"Found {len(concerts)} concerts\n")

    print("Enriching with Gemini AI...")
    enriched = enrich_all_concerts(concerts)

    print_enriched_concerts(enriched)
    save_enriched(enriched)

    print("\nWeek 2 done! Next week we add flight prices.")
