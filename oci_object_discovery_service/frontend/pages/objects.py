from typing import List, Dict, Any

from nicegui import ui

from oci_object_discovery_service.frontend.common import (
    fetch_buckets,
    fetch_objects,
    search_objects,
    top_nav,
)


@ui.page("/objects")
def objects_page():
    ui.page_title("Objects · OCI ODS")
    top_nav("objects")

    all_rows: List[Dict[str, Any]] = []
    filtered_rows: List[Dict[str, Any]] = []
    page_index = 0
    page_size = 10

    def to_row(obj: Dict[str, Any]) -> Dict[str, Any]:
        try:
            obj_size = obj.get("data", {}).get("size", 0)
            size_mb = round(obj_size / (1024 * 1024), 4)
        except Exception:
            size_mb = 0
        return {
            "name": obj.get("name") or obj.get("path") or obj.get("key") or "",
            "bucket": obj.get("bucket", ""),
            "data": obj.get("data", {}).__repr__(),
            "sizeInMB": size_mb,
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
        page_info.set_text(
            f"Page {page_index + 1} of {total_pages} · {total} result(s)"
        )
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
                status.set_text(
                    "Objects endpoint unavailable; enter a keyword to search"
                )
                all_rows = []
            else:
                all_rows = data.get("results", [])
                status.set_text(f"Found {len(all_rows)} object(s)")
        apply_filters()

    with ui.column().classes("p-6 gap-3"):
        ui.label("Objects").classes("text-lg font-medium")
        ui.separator()

        with ui.row().classes("w-full items-end justify-between gap-3"):
            with ui.column().classes("gap-1"):
                ui.label("Bucket filter")
                bucket_select = ui.select(options=["All"], value="All").classes(
                    "min-w-[240px]"
                )
                bucket_select.on_value_change(lambda e: apply_filters())

            with ui.column().classes("items-end gap-1"):
                ui.label("Search")
                with ui.row().classes("items-center gap-2"):
                    search_input = ui.input("Enter keyword")
                    search_input.on("keydown.enter", do_search)
                    ui.button("Search", on_click=do_search)

        columns = [
            {"name": "name", "label": "Name", "field": "name", "align": "left"},
            {"name": "bucket", "label": "Bucket", "field": "bucket", "align": "left"},
            {"name": "size", "label": "Size (MB)", "field": "sizeInMB", "align": "left"},
            {"name": "details", "label": "Details", "field": "data", "align": "left"},
        ]
        objects_table = ui.table(columns=columns, rows=[]).classes("w-full")
        objects_table.props("flat bordered")

        with ui.row().classes("items-center justify-between w-full"):
            status = ui.label("")
            with ui.row().classes("items-center gap-2"):
                prev_btn = ui.button("Prev")
                page_info = ui.label("")
                next_btn = ui.button("Next")

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

        async def init():
            buckets = await fetch_buckets()
            bucket_names = [b["name"] for b in buckets]
            options = ["All"] + sorted(bucket_names)
            bucket_select.set_options(options)
            bucket_select.set_value("All")
            search_input.set_value("")
            await do_search()

        ui.timer(0.05, init, once=True)
