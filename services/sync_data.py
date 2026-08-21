from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import unicodedata

BASE = Path(__file__).resolve().parent.parent
DATA_PATH = BASE / "data" / "meta.json"

if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from services.catalog import WeaponCatalog
from services.live import LiveResolver

TARGET_GAME = "Black Ops 7"

# Whitelist oficial do arsenal de BO7 (Season 5).
# A sincronização NÃO confia mais no campo "game" vindo do JSON antigo.
BO7_WEAPONS = ["M15 Mod 0", "AK-27", "MXR-17", "X9 Maverick", "DS20 Mirage", "Peacekeeper MK1", "Maddox RFB", "EGRT-17", "Voyak KT-3", "MK35 ISR", "VX Compact", "AN-94", "FG42", "Ryden 45K", "RK-9", "Razor 9mm", "Dravec 45", "Carbon 57", "MPC-25", "Kogot-7", "Sturmwolf 45", "REV-46", "VST", "CBRS-3", "Gremlin", "M10 Breacher", "Echo 12", "Akita", "SG-12", "MK.78", "XM325", "Sokol 545", "M8A1", "Warden 308", "M34 Novaline", "Swordfish A1", "KRS-7.62", "VS Recon", "Shadow SK", "XR-3 Ion", "Hawker HX", "Strider 300", "Jager 45", "Velox 5.7", "CODA 9", "1911", "AAROW 109", "A.R.C. M1", "NX Ravager", "GDL Havoc", "Siren", "GRIMHAWK", "KNIFE", "Flatline MK.II", "Ballistic Knife", "H311-SAW", "Katana", "EXECUTIONER'S DUET"]

DISCOVERY_WEAPONS = [
    {
        "name": "AN-94",
        "game": TARGET_GAME,
        "category": "ar",
        "aliases": ["an94", "an-94"],
    },
]


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _norm_name(value):
    value = str(value or "").strip().lower().replace("–", "-")
    value = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in value if not unicodedata.combining(c))
    return " ".join(value.split())


BO7_WEAPON_KEYS = {_norm_name(x) for x in BO7_WEAPONS}


def _weapon_key(w):
    return (
        str(w.get("game", "")).strip().lower(),
        _norm_name(w.get("name", "")),
    )


def _is_target_game(w):
    # Primeiro valida o nome contra a whitelist.
    # O campo game antigo não é suficiente para autorizar uma arma.
    return (
        str(w.get("game", "")).strip().lower() == TARGET_GAME.lower()
        and _norm_name(w.get("name", "")) in BO7_WEAPON_KEYS
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
    seen = set()

    for item in out.get("attachments", []) or []:
        if not isinstance(item, dict):
            continue

        slot = str(item.get("slot") or "").strip()
        name = str(item.get("name") or "").strip()

        if not slot or not name:
            continue

        key = (_norm_name(slot), _norm_name(name))
        if key in seen:
            continue

        seen.add(key)
        attachments.append({"slot": slot, "name": name})

        if len(attachments) >= 5:
            break

    out["attachments"] = attachments
    out["attachments_count"] = len(attachments)
    out["max_attachments"] = 5
    return out


def _diff(old, new):
    changes = []

    if old.get("loadout") != new.get("loadout"):
        changes.append({
            "type": "loadout",
            "from": old.get("loadout"),
            "to": new.get("loadout"),
        })

    old_patch = old.get("patch") or {}
    new_patch = new.get("patch") or {}

    if old_patch != new_patch and new_patch:
        changes.append({
            "type": "patch",
            "from": old_patch,
            "to": new_patch,
        })

    return changes


def _clean_catalog(existing):
    cleaned = {}

    for weapon in existing:
        if not isinstance(weapon, dict):
            continue

        # Só entra se estiver na whitelist oficial.
        if not _is_target_game(weapon):
            continue

        key = _weapon_key(weapon)

        if key not in cleaned:
            cleaned[key] = deepcopy(weapon)

    return cleaned


def _add_discovery_weapons(current):
    for weapon in DISCOVERY_WEAPONS:
        key = _weapon_key(weapon)
        if key not in current:
            current[key] = deepcopy(weapon)


def sync():
    catalog = WeaponCatalog(DATA_PATH)
    resolver = LiveResolver(cache_minutes=0)

    before = len(catalog.weapons)
    current = _clean_catalog(catalog.weapons)

    # Adiciona somente armas explicitamente autorizadas pela whitelist.
    _add_discovery_weapons(current)

    removed_non_bo7 = before - len(current)
    history = catalog.data.setdefault("update_history", [])
    updated_weapons = []
    changes_count = 0

    for key, weapon in list(current.items()):
        try:
            resolved = resolver.resolve(weapon)

            loadout = _stable_loadout(resolved.get("loadout") or {})
            patch = resolved.get("patch") or {}

            old = deepcopy(weapon)
            new_weapon = deepcopy(weapon)

            if loadout.get("attachments"):
                new_weapon["loadout"] = loadout
                new_weapon["attachments"] = deepcopy(loadout["attachments"])

            if resolved.get("refreshed"):
                new_weapon["last_live_refresh"] = resolved["refreshed"]

            # Sem sistema de META.
            for field in (
                "meta_status", "meta_confidence", "meta_sources",
                "pick_rate", "tier", "rank"
            ):
                new_weapon.pop(field, None)

            changes = _diff(
                {
                    "loadout": old.get("loadout", {}),
                    "patch": old.get("patch", {}),
                },
                {
                    "loadout": new_weapon.get("loadout", {}),
                    "patch": patch,
                },
            )

            if changes:
                changes_count += len(changes)
                updated_weapons.append(new_weapon.get("name"))
                history.append({
                    "at": utc_now(),
                    "weapon": new_weapon.get("name"),
                    "game": TARGET_GAME,
                    "changes": changes,
                })

            current[key] = new_weapon

        except Exception as exc:
            history.append({
                "at": utc_now(),
                "weapon": weapon.get("name"),
                "game": TARGET_GAME,
                "error": type(exc).__name__,
            })

    # Garantia final: somente whitelist.
    weapons = [
        w for w in current.values()
        if _is_target_game(w)
    ]

    catalog.data["weapons"] = weapons
    catalog.data["weapons_count"] = len(weapons)
    catalog.data["update_history"] = history[-200:]
    catalog.data["last_sync"] = utc_now()
    catalog.data["data_checked"] = catalog.data["last_sync"]
    catalog.data["api_version"] = "3.5-bo7-whitelist-class-only"
    catalog.data["active_game"] = TARGET_GAME
    catalog.data["bo7_whitelist_count"] = len(BO7_WEAPONS)
    catalog.data["removed_non_bo7"] = removed_non_bo7

    for field in (
        "general_meta", "categories", "meta_rebuilt_at",
        "category_aliases"
    ):
        catalog.data.pop(field, None)

    catalog.data.pop("meta", None)

    DATA_PATH.write_text(
        json.dumps(catalog.data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(json.dumps({
        "ok": True,
        "active_game": TARGET_GAME,
        "whitelist": len(BO7_WEAPONS),
        "removed_non_bo7": removed_non_bo7,
        "updated_weapons": updated_weapons,
        "changes": changes_count,
        "last_sync": catalog.data["last_sync"],
        "weapons": len(weapons),
        "mode": "classe_loadout_only",
    }, ensure_ascii=False))


if __name__ == "__main__":
    sync()
