from __future__ import annotations
from datetime import datetime, timezone, timedelta
from sources.codmunity import fetch_weapon as codmunity
from sources.warzoneloadout import fetch_weapon as wlg
from sources.wzhub import fetch_weapon as wzhub
from sources.activision import fetch_weapon as activision
from sources.common import similarity


class LiveResolver:
    """Consulta fontes atuais com cache curto."""

    def __init__(self, cache_minutes=10):
        self.cache = {}
        self.cache_minutes = cache_minutes

    def resolve(self, weapon):
        key = f"{weapon.get('game')}:{weapon.get('name')}"
        now = datetime.now(timezone.utc)
        cached = self.cache.get(key)

        if cached:
            expires_at = cached.get("expires_at")
            if expires_at and now < expires_at:
                return cached["data"]
            self.cache.pop(key, None)

        name = weapon.get("name")
        game = weapon.get("game", "Black Ops 7")

        sources = [
            codmunity(name, game),
            wlg(name, game),
            wzhub(name),
            activision(name),
        ]

        cm, wz, zh, act = sources
        chosen = None

        # Fonte principal para classe/meta
        if cm.get("attachments"):
            chosen = dict(cm)
            chosen["confirmation"] = "CODMunity"
            chosen["confidence"] = "boa"

        # Confirmação pelo WarzoneLoadout
        if (
            chosen
            and wz.get("attachments")
            and similarity(
                chosen["attachments"],
                wz["attachments"]
            ) >= 0.55
        ):
            chosen["confirmation"] = (
                "CODMunity + WarzoneLoadout.games"
            )
            chosen["confidence"] = "alta"

        # Confirmação pelo WZHUB
        if (
            chosen
            and zh.get("attachments")
            and similarity(
                chosen["attachments"],
                zh["attachments"]
            ) >= 0.55
        ):
            chosen["confirmation"] = (
                chosen.get("confirmation", "CODMunity")
                + " + WZHUB"
            )
            chosen["confidence"] = "alta"

        # Fallback somente se a fonte principal não encontrou classe
        if not chosen:
            chosen = (
                wz
                if wz.get("attachments")
                else (zh if zh.get("attachments") else {})
            )

        data = {
            "patch": act,
            "loadout": chosen or {},
            "codmunity": cm,
            "warzoneloadout": wz,
            "wzhub": zh,
            "refreshed": now.isoformat(),
        }

        self.cache[key] = {
            "expires_at": now + timedelta(minutes=self.cache_minutes),
            "data": data,
        }

        return data
