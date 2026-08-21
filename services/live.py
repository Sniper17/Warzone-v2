
from __future__ import annotations
from datetime import date, timedelta
from sources.codmunity import fetch_weapon as codmunity
from sources.warzoneloadout import fetch_weapon as wlg
from sources.wzhub import fetch_weapon as wzhub
from sources.activision import fetch_weapon as activision
from sources.common import similarity

class LiveResolver:
    def __init__(self, cache_minutes=30):
        self.cache = {}
        self.cache_minutes = cache_minutes

    def resolve(self, weapon):
        key = f"{weapon.get('game')}:{weapon.get('name')}"
        now = date.today().isoformat()
        cached = self.cache.get(key)
        if cached and cached.get("_date") == now:
            return cached["data"]

        name, game = weapon.get("name"), weapon.get("game", "Black Ops 7")
        sources = [codmunity(name, game), wlg(name, game), wzhub(name), activision(name)]
        cm, wz, zh, act = sources
        chosen = None
        if cm.get("attachments"):
            chosen = dict(cm)
            chosen["confirmation"] = "CODMunity"
            chosen["confidence"] = "boa"
        if chosen and wz.get("attachments") and similarity(chosen["attachments"], wz["attachments"]) >= 0.55:
            chosen["confirmation"] = "CODMunity + WarzoneLoadout.games"
            chosen["confidence"] = "alta"
        if chosen and zh.get("attachments") and similarity(chosen["attachments"], zh["attachments"]) >= 0.55:
            chosen["confirmation"] = (chosen.get("confirmation","CODMunity") + " + WZHUB")
            chosen["confidence"] = "alta"
        if not chosen:
            chosen = wz if wz.get("attachments") else (zh if zh.get("attachments") else {})

        data = {
            "patch": act,
            "loadout": chosen or {},
            "codmunity": cm,
            "warzoneloadout": wz, "wzhub": zh,
            "refreshed": now,
        }
        self.cache[key] = {"_date": now, "data": data}
        return data
