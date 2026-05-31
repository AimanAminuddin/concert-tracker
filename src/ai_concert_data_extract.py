"""
Concert Tracker - Week 2
Feed concert data into Gemini to extract, enrich and summarise each event
"""
import time
import json
import os
import google.genai as genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# Setup config matching .env setup
client = genai.Client(api_key=os.getenv("GEMINI_KEY"))

# modern SDK handles models directly via the client initialization, no extra setup needed!
RAW_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
MODEL_NAME = RAW_MODEL.replace("models/", "")

# ----------------------------
# LOAD CONCERTS FROM WEEK 1
# ----------------------------

def load_concerts(filename="data/concerts.json") -> list[dict]:
    '''
    Loads the json file generated in fetch_concert_info.py
    '''
    if not os.path.exists(filename):
        # Fallback support if script is exected from different root paths
        filename = "data/concerts.json"

    with open(filename, "r") as f:
        return json.load(f)


# ----------------------------
# ASK GEMINI TO ENRICH EACH CONCERT
# ----------------------------

def enrich_concert(concert: dict) -> dict:
    '''
    Passes a single concert payload to Gemini to calculate regional definitions,
    travel complexity metrics, and custom context-aware recommendations.
    '''
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
    # Define a strict structural JSON schema matching your dictionary keys 
    response_schema = types.Schema(
        type=types.Type.OBJECT,
        properties={
            "is_local": types.Schema(type=types.Type.BOOLEAN),
            "region": types.Schema(
                type=types.Type.STRING, 
                enum=["Local", "Southeast Asia", "Asia", "International"]
            ),
            "travel_effort": types.Schema(
                type=types.Type.STRING, 
                enum=["None", "Easy", "Moderate", "High"]
            ),
            "summary": types.Schema(type=types.Type.STRING),
            "recommendation": types.Schema(
                type=types.Type.STRING, 
                enum=["Highly Recommended", "Worth Considering", "Skip"]
            ),
            "reason": types.Schema(type=types.Type.STRING),
        },
        required=["is_local", "region", "travel_effort", "summary", "recommendation", "reason"],
    )
    # Forces the model to putput pure, valid JSON matching schema architecture
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=response_schema,
            temperature=0.2,
        ),
    )

    # Because of schema config defined above, response.txt is guranteed 
    # to be parseable JSON file
    enriched = json.loads(response.text)

    # Merge with original concert deftails
    return {**concert, **enriched}


def enrich_all_concerts(concerts: list[dict]) -> list[dict]:
    """
    Loops through the aggregated list of concerts and passes each one 
    to Gemini AI with automatic retry logic to handle rate limits cleanly.
    """
    enriched_list = []

    for idx, concert in enumerate(concerts, 1):
        print(f"[{idx}/{len(concerts)}] Enriching: {concert['artist']} in {concert['city']}...")

        # Retry parameters
        max_retries = 3
        base_delay = 15  # Seconds to wait if rate limited
        success = False
        enriched = None

        for attempt in range(max_retries):
            try:
                enriched = enrich_concert(concert)
                enriched_list.append(enriched)
                success = True
                break  # Break out of retry loop on success
            except Exception as e:
                # Check if it's a Rate Limit / Quota error
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    wait_time = base_delay * (attempt + 1)
                    print(f"Rate limit hit. Retrying item in {wait_time}s... (Attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    # General error handler
                    print(f"Error processing event: {e}")
                    break
        
        # If all retries failed, keep the original details to prevent empty drops
        if not success:
            print(f"Skipping enrichment for {concert['artist']} due to persistent API limits.")
            enriched_list.append(concert)

        # Safe pace delay between distinct valid items
        if idx < len(concerts):
            time.sleep(13)

    return enriched_list

# ----------------------------
# DISPLAY RESULTS
# ----------------------------

def print_enriched_concerts(concerts: list[dict]):
    """
    Saves the finalized, enriched dataset into a local JSON cache file.
    Creates the directory automatically if it doesn't exist yet.
    
    Args:
        concerts (list[dict]): The completed list of enriched concert records.
        filename (str): The destination file path. Defaults to 'src/data/concerts_enriched.json'.
    """
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
    """
    Saves the finalized, enriched dataset into a local JSON cache file.
    Creates the directory automatically if it doesn't exist yet.
    
    Args:
        concerts (list[dict]): The completed list of enriched concert records.
        filename (str): The destination file path. Defaults to 'src/data/concerts_enriched.json'.
    """
    # Force a clean purge of the old file to prevent stale artifacts
    if os.path.exists(filename):
        print(f"Purging old cache file: {filename}")
        os.remove(filename)

    # Ensure parent folders exist dynamically without choking on empty root path contexts
    if os.path.dirname(filename):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
    else:
        os.makedirs("data", exist_ok=True)
    
    with open(filename, "w") as f:
        json.dump(concerts, f, indent=2)
    print(f"Data Cache Refreshed! Saved new records to -> {filename}")


# ----------------------------
# MAIN
# ----------------------------

if __name__ == "__main__":
    print("Loading concerts from Week 1...")

    try:
        concerts = load_concerts()
        print(f"Found {len(concerts)} concerts\n")

        print("Enriching with Gemini AI...")
        enriched = enrich_all_concerts(concerts)

        print_enriched_concerts(enriched)
        save_enriched(enriched)

        print("\nWeek 2 done! Next week we add flight prices.")
    except FileNotFoundError:
        print("Error: Could not find raw concert data. Run fetch_concert_info.py first!")
