"""
Concert Tracker - Week 1
Pulls upcoming events for your favourite artists using Ticketmaster API
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

# ----------------------------
# CONFIG - edit these!
# ----------------------------
TICKETMASTER_API_KEY = os.getenv("TICKETMASTER_API_KEY")

ARTISTS = [
    "Taylor Swift",
    "Coldplay",
    "The Weeknd",
]

# ----------------------------
# FETCH EVENTS
# ----------------------------

def get_events_for_artist(artist_name: str) -> list[dict]:
    url = "https://app.ticketmaster.com/discovery/v2/events.json"
    params = {
        "apikey": TICKETMASTER_API_KEY,
        "keyword": artist_name,
        "classificationName": "music",
        "sort": "date,asc",
        "size": 10,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    return data.get("_embedded", {}).get("events", [])


def extract_event_info(event: dict, artist_name: str) -> dict:
    venues = event.get("_embedded", {}).get("venues", [{}])
    venue = venues[0] if venues else {}

    dates = event.get("dates", {}).get("start", {})

    price_ranges = event.get("priceRanges", [])
    if price_ranges:
        min_p = price_ranges[0].get("min", "N/A")
        max_p = price_ranges[0].get("max", "N/A")
        currency = price_ranges[0].get("currency", "")
        price_str = f"{min_p} - {max_p} {currency}"
    else:
        price_str = "Not listed"

    return {
        "artist": artist_name,
        "event_name": event.get("name", "Unknown"),
        "date": dates.get("localDate", "Unknown"),
        "venue": venue.get("name", "Unknown"),
        "city": venue.get("city", {}).get("name", "Unknown"),
        "country": venue.get("country", {}).get("name", "Unknown"),
        "price_range": price_str,
        "ticket_url": event.get("url", "N/A"),
    }


def fetch_all_events(artists: list[str]) -> list[dict]:
    all_events = []
    for artist in artists:
        print(f"Searching: {artist}...")
        try:
            raw_events = get_events_for_artist(artist)
            for event in raw_events:
                all_events.append(extract_event_info(event, artist))
            print(f"  Found {len(raw_events)} events")
        except Exception as e:
            print(f"  Error: {e}")
    return all_events


def print_events(events: list[dict]):
    print("\n" + "=" * 60)
    for e in events:
        print(f"\n🎵 {e['artist']} — {e['event_name']}")
        print(f"   📅 {e['date']}")
        print(f"   📍 {e['venue']}, {e['city']}, {e['country']}")
        print(f"   💰 {e['price_range']}")
        print(f"   🔗 {e['ticket_url']}")
    print(f"\nTotal: {len(events)} events")


def save_to_json(events, filename="data/concerts.json"):
    os.makedirs("data", exist_ok=True)
    with open(filename, "w") as f:
        json.dump(events, f, indent=2)
    print(f"Saved to {filename}")


if __name__ == "__main__":
    events = fetch_all_events(ARTISTS)
    print_events(events)
    save_to_json(events)
