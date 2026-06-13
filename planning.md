# FitFindr Planning Doc

## A Complete Interaction

FitFindr takes a natural language request and searches secondhand listings for a matching item, then suggests an outfit using the user's existing wardrobe, and finally generates a shareable caption. Each tool only runs if the previous one succeeded — if search returns nothing, the agent stops and tells the user instead of continuing. If the wardrobe is empty, the outfit tool still runs but gives general styling advice instead of specific combinations.

**Example query:** "I'm looking for a vintage graphic tee under $30, size L. I mostly wear baggy jeans and chunky sneakers."

- Step 1: search_listings("vintage graphic tee", size="L", max_price=30) → returns matching items, picks the top result
- Step 2: suggest_outfit(selected_item, wardrobe) → suggests outfit combinations using the user's wardrobe
- Step 3: create_fit_card(outfit_suggestion, selected_item) → generates a casual Instagram-style caption
- Error path: if search returns nothing, agent sets an error message and stops — does not call suggest_outfit or create_fit_card

---

## Tool 1: search_listings

**What it does:** Searches listings.json for items matching the user's description, filtered by size and price.

**Inputs:**
- description (str): keywords from the user e.g. "vintage graphic tee"
- size (str or None): size to filter by e.g. "M", or None to skip
- max_price (float or None): maximum price e.g. 30.0, or None to skip

**Returns:** A list of listing dicts sorted by relevance score. Each dict has: id, title, description, category, style_tags, size, condition, price, colors, brand, platform. Returns an empty list if nothing matches.

**If it fails:** Returns an empty list. The agent checks for this, sets session["error"] to "No listings found for your search. Try different keywords, a higher budget, or no size filter.", and stops without calling the next tools.

---

## Tool 2: suggest_outfit

**What it does:** Takes the selected listing item and the user's wardrobe, calls the Groq LLM, and returns 1-2 outfit suggestions.

**Inputs:**
- new_item (dict): the listing dict selected from search_listings results
- wardrobe (dict): a wardrobe dict with an 'items' key containing a list of wardrobe items

**Returns:** A non-empty string with outfit suggestions. If wardrobe is empty, returns general styling advice for the item instead.

**If it fails:** If the LLM call fails or returns nothing, returns the string "Could not generate outfit suggestions. Please try again."

---

## Tool 3: create_fit_card

**What it does:** Takes the outfit suggestion and the new item, calls the Groq LLM, and returns a short casual caption like an Instagram OOTD post.

**Inputs:**
- outfit (str): the outfit suggestion string from suggest_outfit
- new_item (dict): the listing dict for the thrifted item

**Returns:** A 2-4 sentence casual caption mentioning the item name, price, and platform naturally.

**If it fails:** If outfit is empty or whitespace, returns the string "Could not generate a fit card — outfit description was empty." Does not raise an exception.

---

## Architecture

User query
│
▼
Planning Loop
│
├─► search_listings(description, size, max_price)
│       │
│       ├── results=[] → session["error"] = "No listings found..." → STOP
│       │
│       └── results=[item,...] → session["selected_item"] = results[0]
│               │
├─► suggest_outfit(selected_item, wardrobe)
│       │
│       └── session["outfit_suggestion"] = "..."
│               │
└─► create_fit_card(outfit_suggestion, selected_item)
│
└── session["fit_card"] = "..."
│
▼
Return session to app.py

---

## Planning Loop

After run_agent() receives the user query and wardrobe:

1. Call search_listings(description, size, max_price)
2. Check if results is empty
   - If yes: set session["error"] = "No listings found..." and return session immediately
   - If no: set session["selected_item"] = results[0] and continue
3. Call suggest_outfit(session["selected_item"], wardrobe)
4. Set session["outfit_suggestion"] = result
5. Call create_fit_card(session["outfit_suggestion"], session["selected_item"])
6. Set session["fit_card"] = result
7. Return session

---

## State Management

The session dict stores everything between tool calls:
- session["selected_item"] — set after search_listings, passed into suggest_outfit
- session["outfit_suggestion"] — set after suggest_outfit, passed into create_fit_card
- session["fit_card"] — set after create_fit_card, displayed in the final panel
- session["error"] — set if any tool fails, displayed to the user instead

---

## Error Handling

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | Returns empty list | "No listings found for your search. Try different keywords, a higher budget, or no size filter." |
| suggest_outfit | Empty wardrobe | Returns general styling advice instead of specific combinations |
| suggest_outfit | LLM call fails | "Could not generate outfit suggestions. Please try again." |
| create_fit_card | Empty outfit string | "Could not generate a fit card — outfit description was empty." |

---

## AI Tool Plan

- For search_listings: paste the Tool 1 section above into Claude, ask it to implement the function using load_listings() from data_loader. Check that it filters by all three parameters and handles empty results before running.
- For suggest_outfit: paste the Tool 2 section into Claude, ask it to implement using Groq llama-3.3-70b-versatile. Check that it handles empty wardrobe and returns a string.
- For create_fit_card: paste the Tool 3 section into Claude, ask it to implement with higher temperature. Run it 3 times on the same input to verify outputs vary.
- For the planning loop: paste the Architecture diagram and Planning Loop section into Claude, ask it to implement run_agent() in agent.py. Check that it branches on empty results before using.