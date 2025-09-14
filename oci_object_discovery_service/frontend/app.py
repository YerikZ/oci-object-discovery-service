from nicegui import ui
import httpx


async def search(query: str):
    async with httpx.AsyncClient() as client:
        try:
            results = await client.get(
                "http://controller-api:8080/api/ui/search", params={"q": query}
            )
            results.raise_for_status()
            return results.json()
        except Exception as e:
            return {"error": str(e)}


def on_search(query: str):
    results.clear()  # <-- clear previous results immediately

    if not query.strip():
        with results:
            ui.label("Please enter a search term")
        return

    # optional: show a quick loading line
    with results:
        ui.label("Searching…")

    async def load():
        data = await search(query)
        results.clear()

        if "error" in data:
            with results:
                ui.label(f"Error: {data['error']}")
            return

        items = data.get("results")
        if items is None:
            with results:
                ui.label(f"Unexpected response: {data}")
            return

        if not items:
            with results:
                ui.label("No results found")
            return

        with results:
            for obj in items:
                # render however you like:
                ui.label(str(obj))

    ui.timer(0.1, load, once=True)


# ---- LAYOUT ----
ui.page_title('OCI Object Discovery Service') 
with ui.column().classes("w-full p-4 gap-2"):
    # Input comes first
    ui.input("Search object name").on(
        "keydown.enter",
        lambda e: on_search(e.sender.value),
    )

    # Then the results container
    results = ui.column()
    with results:
        ui.label("Results will appear here")

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(host="0.0.0.0", port=3000)
