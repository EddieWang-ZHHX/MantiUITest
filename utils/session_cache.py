import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from utils.evolution.decorator import evolution_monitor


SESSION_EXPIRE_HOURS = 24


@dataclass
class SessionData:
    session_name: str
    cookies: List[Dict[str, Any]]
    local_storage: Dict[str, Any]
    session_storage: Dict[str, Any]
    created_at: str
    expires_at: str
    login_url: str
    username: str = ""
    identity: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "SessionData":
        return cls(**data)

    def is_expired(self) -> bool:
        expires = datetime.fromisoformat(self.expires_at)
        return datetime.now() > expires


class SessionCache:
    def __init__(self, cache_dir: str = "reports/page_analysis/sessions"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_session_name = "default"

    def _get_path(self, session_name: str) -> Path:
        safe_name = session_name.replace("/", "_").replace("\\", "_")
        return self.cache_dir / f"{safe_name}.json"

    @evolution_monitor("session_cache.save")
    def save(
        self,
        session_name: str,
        cookies: List[Dict],
        local_storage: Dict = None,
        session_storage: Dict = None,
        login_url: str = "",
        username: str = "",
        identity: str = "",
    ) -> Path:
        now = datetime.now()
        expires = now + timedelta(hours=SESSION_EXPIRE_HOURS)

        session = SessionData(
            session_name=session_name,
            cookies=cookies,
            local_storage=local_storage or {},
            session_storage=session_storage or {},
            created_at=now.isoformat(),
            expires_at=expires.isoformat(),
            login_url=login_url,
            username=username,
            identity=identity,
        )

        path = self._get_path(session_name)
        path.write_text(
            json.dumps(session.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        return path

    @evolution_monitor("session_cache.load")
    def load(self, session_name: str) -> Optional[SessionData]:
        path = self._get_path(session_name)
        if not path.exists():
            return None

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            session = SessionData.from_dict(data)

            if session.is_expired():
                path.unlink()
                return None

            return session
        except Exception:
            return None

    def exists(self, session_name: str) -> bool:
        return (
            self._get_path(session_name).exists()
            and self.load(session_name) is not None
        )

    def delete(self, session_name: str) -> bool:
        path = self._get_path(session_name)
        if path.exists():
            path.unlink()
            return True
        return False

    def list_sessions(self) -> List[str]:
        sessions = []
        for f in self.cache_dir.glob("*.json"):
            name = f.stem
            sessions.append(name)
        return sessions

    def clear_all(self):
        for f in self.cache_dir.glob("*.json"):
            f.unlink()
