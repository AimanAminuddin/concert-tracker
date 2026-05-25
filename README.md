# Concert Tracker 🎵

A Python pipeline that pulls upcoming concert data for favourite artists, 
estimates flight costs from Singapore, and uses AI to rank shows by 
total value (ticket price + flights).

## Why I Built This
As someone based in Singapore, deciding whether to attend a concert locally 
or fly out to another city is always a trade-off. This tool automates that 
decision by combining concert data, flight costs, and AI-powered scoring.

## Tech Stack
- **Ticketmaster API** — concert & ticket data
- **Serpapi** — flight prices via Google Flights
- **Gemini API** — AI extraction and enrichment
- **Python** — pandas, requests

## Setup
1. Clone the repo
```bash
   git clone https://github.com/YOURUSERNAME/concert-tracker.git
   cd concert-tracker
```
2. Install dependencies
```bash
   pip install -r requirements.txt
```
3. Create a `.env` file in the root folder
```
   TICKETMASTER_API_KEY=your_key_here
   SERPAPI_KEY=your_key_here
   GEMINI_KEY=your_key_here
```
4. Run the pipeline
```bash
   python src/fetch_concert_info.py
   python src/ai_concert_data_extract.py
```

## Project Status
- [x] Week 1 — Fetch concert data from Ticketmaster
- [x] Week 2 — AI extraction and enrichment with Gemini
- [ ] Week 3 — Flight cost lookup via Serpapi
- [ ] Week 4 — Ranking and scoring system
- [ ] Week 5 — Database storage
- [ ] Week 6 — Streamlit UI

## Sample Output
Coming soon!
