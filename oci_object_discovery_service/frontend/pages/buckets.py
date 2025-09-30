from typing import List, Dict, Any

from nicegui import ui

from oci_object_discovery_service.frontend.common import fetch_buckets, top_nav


@ui.page("/buckets")
def buckets_page():
    ui.page_title("Buckets · OCI ODS")
    top_nav("buckets")

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
            b_prev.disable()
            b_next.disable()
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

        with ui.row().classes("w-full items-end justify-end gap-3"):
            with ui.column().classes("items-end gap-1"):
                ui.label("Search")
                with ui.row().classes("items-center gap-2"):
                    search_input = ui.input("Enter keyword")
                    search_btn = ui.button("Search")

        columns = [
            {"name": "name", "label": "Bucket Name", "field": "name", "align": "left"},
            {
                "name": "namespace",
                "label": "Namespace",
                "field": "namespace",
                "align": "left",
            },
            {
                "name": "size",
                "label": "Size (GB)",
                "field": "sizeInGB",
                "align": "right",
            },
            {
                "name": "data",
                "label": "Details",
                "field": "data",
                "align": "left",
            },
            {
                "name": "created",
                "label": "Created",
                "field": "timeCreated",
                "align": "left",
            },
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
                    r
                    for r in rows_all
                    if q in (r.get("name", "").lower())
                    or q in (r.get("namespace", "").lower())
                ]
                status.set_text(f"Filtered: {len(filtered_rows)} match(es)")
            page_index = 0
            update_table()

        async def load():
            nonlocal rows_all, filtered_rows, page_index
            buckets = await fetch_buckets()
            def to_row(b: Dict[str, Any]) -> Dict[str, Any]:
                data = b.get("data", {}) if isinstance(b, dict) else {}
                size_gb = None
                try:
                    size_bytes = data.get("approximate_size")
                    if size_bytes is not None:
                        size_gb = round(float(size_bytes) / (1024 * 1024), 2)
                except Exception:
                    size_gb = None
                return {
                    "name": b.get("name"),
                    "namespace": b.get("namespace"),
                    "sizeInGB": size_gb,
                    "data": str(data),
                    "timeCreated": data.get("time_created"),
                }

            rows_all = [to_row(b) for b in sorted(buckets, key=lambda x: x.get("name"))]
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
        search_input.on("keydown.enter", apply_search)
        search_btn.on("click", apply_search)

        ui.timer(0.1, load, once=True)
