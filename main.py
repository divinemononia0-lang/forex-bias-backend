from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
from datetime import datetime
import random

app = FastAPI()

# Enable CORS so frontend can talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

NEWSAPI_KEY = "77d8903fe89f45779932b3ddecae6478"

# --- Bias Logic ---
def generate_bias():
    """Generate a fake forex bias dynamically."""
    biases = ["Bullish", "Bearish"]
    reasons_map = {
        "Bullish": ["Strong economic data", "Positive sentiment", "Risk appetite rising"],
        "Bearish": ["Weak economic outlook", "Safe haven demand", "Risk-off sentiment"],
    }

    chosen = random.choice(biases)
    score = round(random.uniform(-1, 1), 2)  # Score between -1 and +1
    return {
        "bias": chosen,
        "score": score,
        "reasons": reasons_map[chosen],
    }

@app.get("/all-bias")
def get_bias():
    """Return bias for key forex pairs."""
    return {
        "EUR/USD": generate_bias(),
        "GBP/USD": generate_bias(),
        "USD/JPY": generate_bias(),
        "XAU/USD": generate_bias(),
    }


# --- News Filtering ---
CURRENCY_TAGS = {
    "EUR/USD": ["EURUSD", "EUR", "euro", "ECB", "eurozone", "Lagarde"],
    "GBP/USD": ["GBPUSD", "GBP", "pound", "sterling", "BoE", "UK", "Britain"],
    "USD/JPY": ["USDJPY", "JPY", "yen", "BOJ", "Bank of Japan", "Tokyo", "Ueda"],
    "XAU/USD": ["XAUUSD", "gold", "XAU", "bullion", "precious metal"],
}

@app.get("/news")
def get_news():
    """Fetch and filter forex-related news articles strictly."""
    url = (
        f"https://newsapi.org/v2/everything?"
        f"q=EURUSD OR GBPUSD OR USDJPY OR XAUUSD&"
        f"language=en&sortBy=publishedAt&apiKey={NEWSAPI_KEY}"
    )
    resp = requests.get(url)

    if resp.status_code != 200:
        return {"error": "Failed to fetch news", "details": resp.text}

    data = resp.json()
    articles = []

    for item in data.get("articles", []):
        title = item.get("title", "")
        desc = item.get("description", "")
        text = f"{title} {desc}".lower()

        # Detect related currency pairs
        related_pairs = []
        for pair, tags in CURRENCY_TAGS.items():
            if any(tag.lower() in text for tag in tags):
                related_pairs.append(pair)

        if not related_pairs:
            continue  # Skip anything not forex-related

        # Format datetime
        published = item.get("publishedAt")
        dt = None
        if published:
            try:
                dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
            except:
                dt = None

        articles.append({
            "headline": title,
            "summary": desc,
            "source": item.get("source", {}).get("name", "Unknown"),
            "url": item.get("url", "#"),
            "datetime": dt.strftime("%Y-%m-%d %H:%M:%S") if dt else "N/A",
            "currencies": related_pairs  # Attach detected pairs
        })

    return articles[:10]  # Return top 10 relevant forex articles

