from nicegui import ui

from oci_object_discovery_service.frontend.common import top_nav, fetch_metrics


@ui.page("/")
def home_page():
    ui.page_title("OCI Object Discovery Service")
    top_nav("home")
    with ui.column().classes("p-6 gap-4 w-full max-w-5xl"):
        ui.label("Dashboard").classes("text-lg font-medium")
        ui.separator()

        # Metric tiles
        with ui.row().classes("w-full gap-4 flex-wrap"):
            def metric_tile(title: str, value: str, subtitle: str = ""):
                with ui.card().classes(
                    "min-w-[220px] flex-1 select-none shadow-sm"
                ):
                    ui.label(title).classes("text-sm text-gray-500")
                    ui.label(value).classes("text-3xl font-semibold")
                    if subtitle:
                        ui.label(subtitle).classes("text-xs text-gray-500 mt-1")

            # placeholders updated by async loader
            bucket_value = ui.label("–").classes("hidden")
            object_value = ui.label("–").classes("hidden")
            size_value = ui.label("–").classes("hidden")

            # Build tiles with dynamic labels inside
            with ui.card().classes("min-w-[220px] flex-1 select-none shadow-sm"):
                ui.label("Buckets").classes("text-sm text-gray-500")
                bucket_value = ui.label("Loading…").classes("text-3xl font-semibold")
            with ui.card().classes("min-w-[220px] flex-1 select-none shadow-sm"):
                ui.label("Objects").classes("text-sm text-gray-500")
                object_value = ui.label("Loading…").classes("text-3xl font-semibold")
            with ui.card().classes("min-w-[220px] flex-1 select-none shadow-sm"):
                ui.label("Total Size").classes("text-sm text-gray-500")
                size_value = ui.label("Loading…").classes("text-3xl font-semibold")
                ui.label("across all buckets").classes("text-xs text-gray-500 mt-1")

        def fmt_size_mb(total_mb: float) -> str:
            try:
                mb = float(total_mb)
            except Exception:
                mb = 0.0
            if mb >= 1024 * 1024:
                return f"{mb/1024/1024:.2f} TB"
            if mb >= 1024:
                return f"{mb/1024:.2f} GB"
            return f"{mb:.0f} MB"

        async def load():
            m = await fetch_metrics()
            bucket_value.set_text(f"{m.get('bucket_count', 0):,}")
            object_value.set_text(f"{m.get('object_count', 0):,}")
            size_value.set_text(fmt_size_mb(m.get("total_size_mb", 0.0)))

        ui.timer(0.05, load, once=True)
