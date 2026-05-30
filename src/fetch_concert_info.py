"""
Concert Tracker - Week 1
Pulls upcoming events for your favourite artists using Ticketmaster API
"""

import requests
import json
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv

load_dotenv()

# ------------------------------------------
# CONFIG: Name of Artist can be edited here
# ------------------------------------------
TICKETMASTER_API_KEY = os.getenv("TICKETMASTER_API_KEY")

ARTISTS = [
    "Taylor Swift",
    "Coldplay",
    "The Weeknd",
]

# Array containing words that usually means the actual artist not performing
BANNED_KEYWORDS = [
    "tribute", 
    "party", 
    "dance", 
    "for kids", 
    "night with", 
    "inspired", 
    "playhouse",
    "singalong",
    'sing',
    'ultimate'
]

# ----------------------------
# DYNAMIC SPOTIFY FETCH
# ----------------------------

def get_spotify_top_artists(limit: int = 5) -> list[str]:
    """
    Authenticates with Spotify using OAuth and fetches the user's top favorite artists.
    
    Args:
        limit (int): Number of top artists to fetch. Defaults to 5.
        
    Returns:
        list[str]: A dynamic list of artist names from Spotify listening history.
    """
    print("🔊 Authenticating with Spotify...")
    try:
        # SpotifyOAuth automatically reads SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, 
        # and SPOTIPY_REDIRECT_URI from your .env file
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            scope="user-top-read"
        ))
        
        # Fetch top artists (medium_term handles the last few months of history)
        results = sp.current_user_top_artists(limit=limit, time_range="medium_term")
        
        artist_names = [artist['name'] for artist in results['items']]
        print(f"🎵 Loaded your top {len(artist_names)} Spotify artists: {', '.join(artist_names)}\n")
        return artist_names
        
    except Exception as e:
        print(f"🚨 Failed to pull artists from Spotify: {e}")
        print("Fallback: Using default fallback artist array.")
        return ["Taylor Swift", "Coldplay", "The Weeknd"]

# ----------------------------
# FETCH EVENTS
# ----------------------------

def get_events_for_artist(artist_name: str) -> list[dict]:
    """
    Fetches raw event data from Ticketmaster Discovery API for a specific 
    artist name

    Args:
        artist_name (str): The name of the artist to search for 
    
    Returns:
        list[dict]: A list of raw event dictionaries returned by the API. Returns an empty list on failure.
    """
    url = "https://app.ticketmaster.com/discovery/v2/events.json"
    params = {
        "apikey": TICKETMASTER_API_KEY,
        "keyword": artist_name,
        "classificationName": "music",
        "sort": "date,asc",
        # Use a large size to pull more records since we will filter
        # out some using BANNED_KEYWORDS
        "size": 20,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    return data.get("_embedded", {}).get("events", [])


def extract_event_info(event: dict, artist_name: str) -> dict:
    """
    Parses a messy, nested raw API event dictionary and extracts essential details into a clean format.

    Args:
        event (dict): The raw event dictionary from Ticketmaster.
        artist_name (str): The name of the tracked artist.
        
    Returns:
        dict: A flattened dictionary containing structured event details (venue, city, price, etc.).
    """
    # Ensures venues is a list and has at least one item
    venues = event.get("_embedded", {}).get("venues", [])
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
    """
    Loops through a list of artists, fetches their events, filters out tribute acts,
    and returns a master list of all verified real concerts.
    
    Args:
        artists (list[str]): Names of the artists to look up.
        
    Returns:
        list[dict]: A list of aggregated, parsed, and filtered concert dictionaries.
    """
    all_events = []
    for artist in artists:
        print(f"Searching: {artist}...")
        try:
            raw_events = get_events_for_artist(artist)
            filtered_count = 0

            for event in raw_events:
                event_info = extract_event_info(event,artist_name=artist)

                # Check if any banned keyword is in the event name (case-insensitive)
                event_name_lower = event_info['event_name'].lower()
                is_banned = any(keyword in event_name_lower for keyword in BANNED_KEYWORDS)

                if is_banned:
                    # skip this tribute act event
                    print(f"SKIPPED TRIBUTE:{event_info['event_name']}")
                    continue

                all_events.append(event_info)
                filtered_count += 1

            print(f"Success: Found {filtered_count} real events (filtered out {len(raw_events) - filtered_count} tribute acts)")
        except Exception as e:
            print(f"Error processing {artist}: {e}")
    return all_events

def print_events(events: list[dict]):
    """
    Prints a beautiful, human-readable layout of all collected concerts directly to the console.
    
    Args:
        events (list[dict]): List of parsed concert dictionaries.
    """
    print("\n" + "=" * 60)
    print("                    UPCOMING REAL CONCERTS                     ")
    print("=" * 60)
    for e in events:
        print(f"\n🎵 {e['artist']} — {e['event_name']}")
        print(f"   📅 {e['date']}")
        print(f"   📍 {e['venue']}, {e['city']}, {e['country']}")
        print(f"   💰 {e['price_range']}")
        print(f"   🔗 {e['ticket_url']}")
    print("\n" + "=" * 60)
    print(f"📋 Total Aggregated Events: {len(events)}")

def save_to_json(events, filename="data/concerts.json"):
    """
    Saves the aggregated concert list to a local JSON database file. 
    Wipes and overwrites any existing data to ensure a fresh state.
    
    Args:
        events (list[dict]): List of concert dictionaries to store.
        filename (str): The file path where data should be saved. Defaults to 'data/concerts.json'.
    """
    os.makedirs("data", exist_ok=True)
    # Open file with "w" which automatically clears out old data and refreshes it fresh
    with open(filename, "w") as f:
        json.dump(events, f, indent=2)
    print(f"🔄 Data Cache Refreshed! Saved current records to -> {filename}")


if __name__ == "__main__":
    # Get dynamic list of 5 favourite artists right out Spotify profile
    dynamic_artists = get_spotify_top_artists(limit=5)
    # events = fetch_all_events(ARTISTS)

    # Run ticketmaster pipeline with spotify artists 
    events = fetch_all_events(dynamic_artists)
    print_events(events)
    save_to_json(events)
