from nicegui import ui

# Import pages to register routes with NiceGUI
# These imports must happen before ui.run so that @ui.page decorators execute.
from oci_object_discovery_service.frontend.pages import home, buckets, objects  # noqa: F401


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(host="0.0.0.0", port=3000)
