from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class MemeCache:
    path: Path
    titles: list[str] = field(default_factory=list)
    source: str = "fallback"

    def load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return

        if isinstance(data, dict):
            self.titles = [str(item) for item in data.get("titles", []) if item is not None]
            self.source = str(data.get("source", self.source))

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"source": self.source, "titles": self.titles[:200]}
        self.path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    def update(self, titles: list[str], source: str) -> None:
        merged: list[str] = []
        for title in titles:
            cleaned = str(title).strip()
            if cleaned and cleaned not in merged:
                merged.append(cleaned)
        self.titles = merged[:200]
        self.source = source
        self.save()

    def add(self, title: str) -> None:
        cleaned = title.strip()
        if not cleaned or cleaned in self.titles:
            return
        self.titles.append(cleaned)
        self.titles = self.titles[-200:]
        self.save()
