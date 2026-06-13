"""
agent.py
"""

import re
from tools import search_listings, suggest_outfit, create_fit_card


def _new_session(query: str, wardrobe: dict) -> dict:
    return {
        "query": query,
        "parsed": {},
        "search_results": [],
        "selected_item": None,
        "wardrobe": wardrobe,
        "outfit_suggestion": None,
        "fit_card": None,
        "error": None,
    }


def _parse_query(query: str) -> dict:
    """Extract description, size, and max_price from the user's query."""
    
    # Extract max price (looks for numbers after $ or "under")
    price_match = re.search(r'under\s*\$?(\d+(?:\.\d+)?)', query, re.IGNORECASE)
    if not price_match:
        price_match = re.search(r'\$(\d+(?:\.\d+)?)', query, re.IGNORECASE)
    max_price = float(price_match.group(1)) if price_match else None

    # Extract size (looks for common size patterns)
    size_match = re.search(r'\bsize\s*([SMLX]+\d*|XS|XL|XXL|one size)\b', query, re.IGNORECASE)
    if not size_match:
        size_match = re.search(r'\b(XS|S|M|L|XL|XXL)\b', query)
    size = size_match.group(1) if size_match else None

    # Remove price and size mentions to get clean description
    description = query
    description = re.sub(r'under\s*\$?\d+(?:\.\d+)?', '', description, flags=re.IGNORECASE)
    description = re.sub(r'\$\d+(?:\.\d+)?', '', description)
    description = re.sub(r'\bsize\s*[SMLX]+\d*\b', '', description, flags=re.IGNORECASE)
    description = re.sub(r'\b(XS|S|M|L|XL|XXL)\b', '', description)
    description = re.sub(r'\b(looking for|i want|find me|i need)\b', '', description, flags=re.IGNORECASE)
    description = ' '.join(description.split())

    return {"description": description, "size": size, "max_price": max_price}


def run_agent(query: str, wardrobe: dict) -> dict:
    # Step 1: Initialize session
    session = _new_session(query, wardrobe)

    # Step 2: Parse the query
    parsed = _parse_query(query)
    session["parsed"] = parsed

    # Step 3: Search listings
    results = search_listings(
        description=parsed["description"],
        size=parsed["size"],
        max_price=parsed["max_price"],
    )
    session["search_results"] = results

    # If no results, stop early
    if not results:
        session["error"] = "No listings found for your search. Try different keywords, a higher budget, or no size filter."
        return session

    # Step 4: Select top result
    session["selected_item"] = results[0]

    # Step 5: Suggest outfit
    session["outfit_suggestion"] = suggest_outfit(
        session["selected_item"],
        wardrobe,
    )

    # Step 6: Create fit card
    session["fit_card"] = create_fit_card(
        session["outfit_suggestion"],
        session["selected_item"],
    )

    # Step 7: Return session
    return session


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")