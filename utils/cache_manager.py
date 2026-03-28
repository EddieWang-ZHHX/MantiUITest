import json
from pathlib import Path
from typing import Optional, Dict, Any
from utils.parsers.base_parser import PageSnapshot


class CacheManager:
    def __init__(self, cache_dir: str = "reports/page_analysis"):
        self.cache_dir = Path(cache_dir)

    def _get_path(self, module: str, page_name: str, ext: str) -> Path:
        return self.cache_dir / module / f"{page_name}.{ext}"

    def save_snapshot(
        self, module: str, page_name: str, snapshot: PageSnapshot
    ) -> Path:
        path = self._get_path(module, page_name, "json")
        path.parent.mkdir(parents=True, exist_ok=True)

        data = snapshot.to_dict()
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        return path

    def load_snapshot(self, module: str, page_name: str) -> Optional[PageSnapshot]:
        path = self._get_path(module, page_name, "json")
        if not path.exists():
            return None

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return PageSnapshot.from_dict(data)
        except Exception:
            return None

    def save_raw(self, module: str, page_name: str, data: dict) -> Path:
        path = self._get_path(module, page_name, "json")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return path

    def load_raw(self, module: str, page_name: str) -> Optional[dict]:
        path = self._get_path(module, page_name, "json")
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def exists(self, module: str, page_name: str) -> bool:
        return self._get_path(module, page_name, "json").exists()

    def delete(self, module: str, page_name: str) -> bool:
        json_path = self._get_path(module, page_name, "json")
        md_path = self._get_path(module, page_name, "md")

        deleted = False
        if json_path.exists():
            json_path.unlink()
            deleted = True
        if md_path.exists():
            md_path.unlink()
            deleted = True

        return deleted

    def list_pages(self, module: str) -> list:
        module_dir = self.cache_dir / module
        if not module_dir.exists():
            return []

        pages = []
        for f in module_dir.glob("*.json"):
            pages.append(f.stem)
        return pages

    def list_modules(self) -> list:
        modules = []
        if not self.cache_dir.exists():
            return modules
        for d in self.cache_dir.iterdir():
            if d.is_dir() and d.name != "sessions":
                modules.append(d.name)
        return modules
