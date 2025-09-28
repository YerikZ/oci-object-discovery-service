from nicegui import ui
import httpx
from typing import List, Dict, Any
from oci_object_discovery_service.utils.logger import logger

API_BASE = "http://controller-api:8080/api/ui"


# ---- API HELPERS ----
async def api_get(path: str, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(f"{API_BASE}{path}", params=params)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            return {"error": str(e)}


async def fetch_buckets() -> List[str]:
    data = await api_get("/buckets")
    if "error" in data:
        return []
    return data.get("results", [])


async def fetch_objects(q: str | None = None, bucket: str | None = None, skip: int = 0, limit: int = 1000) -> Dict[str, Any]:
    params: Dict[str, Any] = {"skip": skip, "limit": limit}
    if q and q.strip():
        params["q"] = q.strip()
    if bucket and bucket.strip() and bucket != "All":
        params["bucket"] = bucket.strip()
    data = await api_get("/objects", params=params)
    if "error" in data:
        return {"results": [], "total": 0, "skip": skip, "limit": limit, "error": data["error"]}
    return data


async def search_objects(keyword: str) -> List[Dict[str, Any]]:
    data = await api_get("/search", params={"q": keyword})
    if "error" in data:
        return []
    return data.get("results", [])


# ---- SHARED UI ----
def top_nav(active: str = "home") -> None:
    with ui.header().classes("items-center justify-between"):
        ui.label("OCI Object Discovery Service").classes("text-xl font-semibold")
        with ui.row().classes("items-center gap-4"):
            def link(label: str, path: str, key: str):
                style = "text-white font-bold" if key == active else "text-white/70 hover:text-white"
                ui.link(label, path).classes(style)

            link("Home", "/", "home")
            link("Buckets", "/buckets", "buckets")
            link("Objects", "/objects", "objects")


# ---- PAGES ----
@ui.page("/")
def home_page():
    ui.page_title("OCI Object Discovery Service")
    top_nav("home")
    with ui.column().classes("p-6 gap-2 max-w-3xl"):
        ui.label("Home").classes("text-lg font-medium")
        ui.separator()
        ui.label(
            "This is the home page. Add informational content here later."
        )


@ui.page("/buckets")
def buckets_page():
    ui.page_title("Buckets · OCI ODS")
    top_nav("buckets")

    # pagination state
    rows_all: List[Dict[str, Any]] = []
    filtered_rows: List[Dict[str, Any]] = []
    page_index = 0
    page_size = 10

    def update_table():
        nonlocal page_index
        total = len(filtered_rows)
        if total == 0:
            table.rows = []
            info.set_text("No buckets")
            b_prev.disable(); b_next.disable()
            return
        start = page_index * page_size
        end = start + page_size
        table.rows = filtered_rows[start:end]
        total_pages = (total + page_size - 1) // page_size
        info.set_text(f"Page {page_index + 1} of {total_pages} · {total} bucket(s)")
        b_prev.enable() if page_index > 0 else b_prev.disable()
        b_next.enable() if page_index < total_pages - 1 else b_next.disable()

    with ui.column().classes("p-6 gap-3"):
        ui.label("Buckets").classes("text-lg font-medium")
        ui.separator()

        # top controls: right-aligned search (client-side)
        with ui.row().classes("w-full items-end justify-end gap-3"):
            with ui.column().classes("items-end gap-1"):
                ui.label("Search")
                with ui.row().classes("items-center gap-2"):
                    search_input = ui.input("Enter keyword")
                    search_btn = ui.button("Search")

        columns = [
            {"name": "name", "label": "Bucket Name", "field": "name", "align": "left"},
            {"name": "namespace", "label": "Namespace", "field": "namespace", "align": "left"},
            {"name": "size", "label": "Size (MB)", "field": "sizeInMB", "align": "right"},
            {"name": "created", "label": "Created", "field": "timeCreated", "align": "left"},
        ]
        table = ui.table(columns=columns, rows=[]).classes("w-full")
        table.props("flat bordered")

        with ui.row().classes("items-center justify-between w-full"):
            status = ui.label("Loading buckets…")
            with ui.row().classes("items-center gap-2"):
                b_prev = ui.button("Prev")
                info = ui.label("")
                b_next = ui.button("Next")

        def apply_search():
            nonlocal filtered_rows, page_index
            q = (search_input.value or "").strip().lower()
            if not q:
                filtered_rows = rows_all
                status.set_text(f"Showing all ({len(filtered_rows)})")
            else:
                filtered_rows = [
                    r for r in rows_all
                    if q in (r.get("name", "").lower()) or q in (r.get("namespace", "").lower())
                ]
                status.set_text(f"Filtered: {len(filtered_rows)} match(es)")
            page_index = 0
            update_table()

        async def load():
            nonlocal rows_all, filtered_rows, page_index
            buckets = await fetch_buckets()
            rows_all = [{"name": b["name"], "namespace": b["namespace"], "sizeInMB": b["metadata"]["sizeInMB"], "timeCreated": b["metadata"]["timeCreated"]} for b in sorted(buckets, key=lambda x: x["name"])]
            filtered_rows = rows_all
            page_index = 0
            update_table()
            status.set_text("Loaded")

        def go_prev():
            nonlocal page_index
            if page_index > 0:
                page_index -= 1
                update_table()

        def go_next():
            nonlocal page_index
            total_pages = (len(filtered_rows) + page_size - 1) // page_size
            if page_index < total_pages - 1:
                page_index += 1
                update_table()

        b_prev.on("click", lambda e: go_prev())
        b_next.on("click", lambda e: go_next())
        # search handlers
        search_input.on('keydown.enter', apply_search)
        search_btn.on('click', apply_search)

        ui.timer(0.1, load, once=True)


@ui.page("/objects")
def objects_page():
    ui.page_title("Objects · OCI ODS")
    top_nav("objects")

    # state (client-side pagination over fetched set)
    all_rows: List[Dict[str, Any]] = []
    filtered_rows: List[Dict[str, Any]] = []
    page_index = 0
    page_size = 10

    # helpers
    def to_row(obj: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "name": obj.get("name") or obj.get("path") or obj.get("key") or "",
            "bucket": obj.get("bucket", ""),            
            "_raw": obj.get("metadata", {}).__repr__(),
        }

    def apply_filters():
        nonlocal filtered_rows, page_index
        b = bucket_select.value
        rows = [to_row(o) for o in all_rows]
        if b and b != "All":
            rows = [r for r in rows if r.get("bucket") == b]
        filtered_rows = rows
        page_index = 0
        update_table()

    def update_table():
        nonlocal page_index
        total = len(filtered_rows)
        if total == 0:
            objects_table.rows = []
            page_info.set_text("No results")
            prev_btn.disable()
            next_btn.disable()
            return
        start = page_index * page_size
        end = start + page_size
        objects_table.rows = filtered_rows[start:end]
        total_pages = (total + page_size - 1) // page_size
        page_info.set_text(f"Page {page_index + 1} of {total_pages} · {total} result(s)")
        prev_btn.enable() if page_index > 0 else prev_btn.disable()
        next_btn.enable() if page_index < total_pages - 1 else next_btn.disable()

    async def do_search():
        nonlocal all_rows
        q = search_input.value.strip()
        if q:
            status.set_text("Searching…")
            results = await search_objects(q)
            all_rows = results
            status.set_text(f"Found {len(all_rows)} object(s)")
        else:
            status.set_text("Loading…")
            data = await fetch_objects(q=None, bucket=None, skip=0, limit=1000)
            if data.get("error"):
                status.set_text("Objects endpoint unavailable; enter a keyword to search")
                all_rows = []
            else:
                all_rows = data.get("results", [])
                status.set_text(f"Found {len(all_rows)} object(s)")
        apply_filters()

    # layout
    with ui.column().classes("p-6 gap-3"):
        ui.label("Objects").classes("text-lg font-medium")
        ui.separator()

        # top controls: bucket filter (left) and search (right)
        with ui.row().classes("w-full items-end justify-between gap-3"):
            with ui.column().classes("gap-1"):
                ui.label("Bucket filter")
                bucket_select = ui.select(options=["All"], value="All").classes("min-w-[240px]")
                bucket_select.on_value_change(lambda e: apply_filters())

            with ui.column().classes("items-end gap-1"):
                ui.label("Search")
                with ui.row().classes("items-center gap-2"):
                    search_input = ui.input("Enter keyword")
                    search_input.on('keydown.enter', do_search)
                    ui.button('Search', on_click=do_search)

        # table
        columns = [
            {"name": "name", "label": "Name", "field": "name", "align": "left"},
            {"name": "bucket", "label": "Bucket", "field": "bucket", "align": "left"},
            {"name": "details", "label": "Metadata", "field": "_raw", "align": "left"},
        ]
        objects_table = ui.table(columns=columns, rows=[]).classes("w-full")
        objects_table.props("flat bordered")

        # pagination controls
        with ui.row().classes("items-center justify-between w-full"):
            status = ui.label("")
            with ui.row().classes("items-center gap-2"):
                prev_btn = ui.button("Prev")
                page_info = ui.label("")
                next_btn = ui.button("Next")

        # wire real handlers for prev/next
        def go_prev():
            nonlocal page_index
            if page_index > 0:
                page_index -= 1
                update_table()

        def go_next():
            nonlocal page_index
            total = len(filtered_rows)
            total_pages = (total + page_size - 1) // page_size
            if page_index < total_pages - 1:
                page_index += 1
                update_table()

        prev_btn.on("click", lambda e: go_prev())
        next_btn.on("click", lambda e: go_next())

        # initial loads
        async def init():
            # load bucket options and default object list
            buckets = await fetch_buckets()
            # logger.debug(f"Fetched buckets: {buckets}")
            bucket_names = [b["name"] for b in buckets]
            options = ["All"] + sorted(bucket_names)
            bucket_select.set_options(options)
            bucket_select.set_value("All")
            # default: show all objects
            search_input.set_value("")
            await do_search()

        ui.timer(0.05, init, once=True)


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(host="0.0.0.0", port=3000)
