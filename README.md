# FitFindr

A multi-tool AI agent that helps users find secondhand clothing and figure out how to wear it.

---

## How to Run

1. Clone the repo and activate your virtual environment
2. Install dependencies: `pip install -r requirements.txt`
3. Add your Groq API key to a `.env` file: `GROQ_API_KEY=your_key_here`
4. Run the app: `python app.py`
5. Open `http://127.0.0.1:7860` in your browser

---

## Tool Inventory

### search_listings(description: str, size: str | None, max_price: float | None) → list[dict]
Searches the mock listings dataset for items matching the description, filtered by size and price. Returns a list of matching listing dicts sorted by relevance score. Returns an empty list if nothing matches — does not raise an exception.

### suggest_outfit(new_item: dict, wardrobe: dict) → str
Takes the selected listing and the user's wardrobe and calls the Groq LLM to suggest 1-2 outfit combinations. If the wardrobe is empty, returns general styling advice instead of specific combinations. Returns a non-empty string in all cases.

### create_fit_card(outfit: str, new_item: dict) → str
Takes the outfit suggestion and the listing item and calls the Groq LLM to generate a casual 2-4 sentence Instagram-style caption. Uses higher temperature (1.2) so outputs vary across runs. Guards against empty outfit input.

---

## How the Planning Loop Works

When a query is submitted, `run_agent()` does the following:

1. Parses the query with regex to extract a description, size, and max_price
2. Calls `search_listings()` with those parameters
3. Checks if results is empty — if yes, sets an error message and returns immediately without calling the other tools
4. If results exist, selects the top result and stores it in the session
5. Calls `suggest_outfit()` with the selected item and wardrobe
6. Calls `create_fit_card()` with the outfit suggestion and selected item
7. Returns the completed session dict to `app.py`

The key conditional logic is at step 3 — the agent does not call `suggest_outfit` or `create_fit_card` if search returns nothing.

---

## State Management

All state is stored in a session dict that gets passed through the planning loop:

- `session["selected_item"]` — set after search, passed into suggest_outfit
- `session["outfit_suggestion"]` — set after suggest_outfit, passed into create_fit_card
- `session["fit_card"]` — set after create_fit_card, displayed in the final panel
- `session["error"]` — set if a tool fails, displayed to the user instead of the other panels

No values are hardcoded between steps — each tool receives its input directly from the session.

---

## Error Handling

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | Returns empty list | "No listings found for your search. Try different keywords, a higher budget, or no size filter." |
| suggest_outfit | Empty wardrobe | Returns general styling advice instead of crashing |
| suggest_outfit | LLM call fails | "Could not generate outfit suggestions. Please try again." |
| create_fit_card | Empty outfit string | "Could not generate a fit card — outfit description was empty." |

**Concrete example from testing:** Running `create_fit_card('', results[0])` returned `"Could not generate a fit card — outfit description was empty."` instead of raising an exception. Running `search_listings('designer ballgown', size='XXS', max_price=5)` returned `[]` and the agent displayed the error message without calling the next tools.

---

## Spec Reflection

**One way the spec helped:** Writing the planning loop section of `planning.md` before coding made the conditional logic in `run_agent()` straightforward — the numbered steps mapped directly to code.

**One way implementation diverged:** The spec didn't specify how to parse the user query. I used regex to extract size and price rather than using the LLM, because it was faster and more predictable for structured patterns like "under $30" and "size M".

---

## AI Usage

**Instance 1 — implementing tools.py:** I gave Claude the Tool 1, 2, and 3 sections from `planning.md` and asked it to implement each function. I reviewed the generated code to confirm it filtered by all three parameters, handled empty results, and called the Groq API correctly before running it.

**Instance 2 — implementing agent.py:** I gave Claude the Architecture diagram and Planning Loop section from `planning.md` and asked it to implement `run_agent()`. I checked that the generated code branched on empty search results before calling `suggest_outfit`, and that state was stored in the session dict between steps.