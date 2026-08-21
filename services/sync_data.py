from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent.parent
DATA_PATH = BASE / "data" / "meta.json"

# Allow execution as `python services/sync_data.py`.
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from services.catalog import WeaponCatalog
from services.live import LiveResolver


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _weapon_key(w):
    return (
        str(w.get("game", "")).strip().lower(),
        str(w.get("name", "")).strip().lower(),
    )


def _stable_loadout(loadout):
    if not isinstance(loadout, dict):
        return {}
    keep = {
        "attachments", "code", "updated", "source", "confirmation",
        "consensus_sources", "consensus_details"
    }
    out = {k: deepcopy(loadout[k]) for k in keep if k in loadout}
    attachments = []
    for a in out.get("attachments", []) or []:
        if not isinstance(a, dict):
            continue
        if a.get("slot") and a.get("name"):
            attachments.append({
                "slot": str(a["slot"]),
                "name": str(a["name"]),
            })
        if len(attachments) >= 5:
            break
    if attachments:
        out["attachments"] = attachments
    return out


def _weapon_snapshot(resolved):
    w = resolved.get("weapon") or {}
    return {
        "name": w.get("name"),
        "game": w.get("game", "Black Ops 7"),
        "category": w.get("category"),
        "loadout": _stable_loadout(resolved.get("loadout") or {}),
        "meta_status": resolved.get("meta_status"),
        "meta_confidence": resolved.get("meta_confidence"),
        "last_live_refresh": resolved.get("refreshed"),
    }


def _diff(old, new):
    changes = []
    if old.get("meta_status") != new.get("meta_status"):
        changes.append({
            "type": "classification",
            "from": old.get("meta_status"),
            "to": new.get("meta_status"),
        })
    if old.get("loadout") != new.get("loadout"):
        changes.append({
            "type": "loadout",
            "from": old.get("loadout"),
            "to": new.get("loadout"),
        })
    return changes


def sync():
    catalog = WeaponCatalog(DATA_PATH)
    resolver = LiveResolver(cache_minutes=0)

    current = { _weapon_key(w): deepcopy(w) for w in catalog.weapons }
    history = catalog.data.setdefault("update_history", [])
    updated_weapons = []
    changes_count = 0

    for weapon in catalog.weapons:
        try:
            resolved = resolver.resolve(weapon)
            snapshot = _weapon_snapshot(resolved)
            key = _weapon_key(weapon)
            old = current.get(key, {})

            if snapshot.get("loadout", {}).get("attachments"):
                new_weapon = deepcopy(weapon)
                new_weapon["loadout"] = snapshot["loadout"]
                if snapshot.get("meta_status"):
                    new_weapon["meta_status"] = snapshot["meta_status"]
                new_weapon["last_live_refresh"] = snapshot["last_live_refresh"]

                changes = _diff(old, snapshot)
                if changes:
                    changes_count += len(changes)
                    history.append({
                        "at": utc_now(),
                        "weapon": weapon.get("name"),
                        "game": weapon.get("game", "Black Ops 7"),
                        "changes": changes,
                    })
                    updated_weapons.append(weapon.get("name"))
                current[key] = new_weapon
        except Exception as exc:
            # One bad source must never stop the entire synchronization.
            history.append({
                "at": utc_now(),
                "weapon": weapon.get("name"),
                "error": type(exc).__name__,
            })

    # Keep history bounded.
    catalog.data["update_history"] = history[-200:]
    catalog.data["weapons"] = list(current.values())
    catalog.data["weapons_count"] = len(current)
    catalog.data["last_sync"] = utc_now()
    catalog.data["data_checked"] = catalog.data["last_sync"]
    catalog.data["api_version"] = "3.1-auto-sync"

    DATA_PATH.write_text(
        json.dumps(catalog.data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(json.dumps({
        "ok": True,
        "updated_weapons": updated_weapons,
        "changes": changes_count,
        "last_sync": catalog.data["last_sync"],
        "weapons": len(current),
    }, ensure_ascii=False))


if __name__ == "__main__":
    sync()
