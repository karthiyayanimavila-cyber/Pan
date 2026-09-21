from __future__ import annotations

import importlib
import logging
from pathlib import Path

log = logging.getLogger("panbot.loader")


def load_modules() -> tuple[int, int]:
    root = Path(__file__).parent / "modules"
    discovered = 0
    loaded = 0
    for path in sorted(root.rglob("*.py")):
        if path.name == "__init__.py" or path.name.startswith("_"):
            continue
        discovered += 1
        relative = path.relative_to(Path(__file__).parent).with_suffix("")
        module_name = "panbot." + ".".join(relative.parts)
        try:
            importlib.import_module(module_name)
            loaded += 1
            log.debug("Loaded module %s", module_name)
        except Exception:
            log.exception("Failed to load module %s", module_name)
    return loaded, discovered
