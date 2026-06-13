"""
tools.py
"""

import os
from dotenv import load_dotenv
from groq import Groq
from utils.data_loader import load_listings

load_dotenv()

def _get_groq_client():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set. Add it to a .env file in the project root.")
    return Groq(api_key=api_key)


def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    listings = load_listings()

    # Filter by price
    if max_price is not None:
        listings = [l for l in listings if l["price"] <= max_price]

    # Filter by size
    if size is not None:
        listings = [l for l in listings if size.lower() in l["size"].lower()]

    # Score by keyword match
    keywords = description.lower().split()
    scored = []
    for item in listings:
        searchable = (
            item["title"].lower() + " " +
            item["description"].lower() + " " +
            " ".join(item["style_tags"]).lower()
        )
        score = sum(1 for kw in keywords if kw in searchable)
        if score > 0:
            scored.append((score, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored]


def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    client = _get_groq_client()

    if not wardrobe.get("items"):
        prompt = f"""A user is considering buying this thrifted item:
- {new_item['title']} (${new_item['price']}, {new_item['condition']} condition)
- Style: {', '.join(new_item['style_tags'])}
- Colors: {', '.join(new_item['colors'])}

They haven't shared their wardrobe yet. Give them 1-2 general outfit ideas for this piece — what kinds of items pair well with it, what vibe it suits, how to wear it."""
    else:
        wardrobe_text = "\n".join(
            f"- {item['name']} ({', '.join(item['colors'])})"
            for item in wardrobe["items"]
        )
        prompt = f"""A user is considering buying this thrifted item:
- {new_item['title']} (${new_item['price']}, {new_item['condition']} condition)
- Style: {', '.join(new_item['style_tags'])}
- Colors: {', '.join(new_item['colors'])}

Their current wardrobe includes:
{wardrobe_text}

Suggest 1-2 specific outfit combinations using the new item and pieces from their wardrobe. Name the exact wardrobe pieces."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
        )
        result = response.choices[0].message.content.strip()
        return result if result else "Could not generate outfit suggestions. Please try again."
    except Exception:
        return "Could not generate outfit suggestions. Please try again."


def create_fit_card(outfit: str, new_item: dict) -> str:
    if not outfit or not outfit.strip():
        return "Could not generate a fit card — outfit description was empty."

    client = _get_groq_client()

    prompt = f"""Write a 2-4 sentence Instagram caption for this thrifted outfit.

Item: {new_item['title']}
Price: ${new_item['price']}
Platform: {new_item['platform']}
Outfit: {outfit}

Rules:
- Sound casual and authentic like a real OOTD post, not a product description
- Mention the item name, price, and platform once each, naturally
- Capture the specific vibe of the outfit
- Do NOT use hashtags"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=1.2,
        )
        result = response.choices[0].message.content.strip()
        return result if result else "Could not generate a fit card. Please try again."
    except Exception:
        return "Could not generate a fit card. Please try again."