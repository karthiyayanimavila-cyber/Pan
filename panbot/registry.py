from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModuleInfo:
    name: str
    help_text: str
    category: str


_modules: dict[str, ModuleInfo] = {}


def register_module(name: str, help_text: str, category: str = "plugins") -> None:
    _modules[name.lower()] = ModuleInfo(name, help_text, category)


def modules() -> list[ModuleInfo]:
    return sorted(_modules.values(), key=lambda item: (item.category, item.name.lower()))
