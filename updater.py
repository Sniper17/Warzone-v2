
from __future__ import annotations
import json, re, sys
from pathlib import Path
from sources.common import now_utc, canonical_id, norm
from sources.codmunity import discover_database, fetch_weapon as codmunity_weapon
from sources.activision import load_latest_patch, parse_weapon
from sources.warzoneloadout import fetch_weapon as wlg_weapon

ROOT = Path(__file__).resolve().parent
PATH = ROOT / "data" / "meta.json"

CATEGORY = {
    "assault rifle":"ar", "assault rifles":"ar", "fuzis de assalto":"ar",
    "smg":"smg", "shotgun":"doze", "escopeta":"doze", "pistol":"pt",
    "pistola":"pt", "sniper rifle":"sniper", "sniper":"sniper",
    "marksman rifle":"marksman", "lmg":"lmg", "rifle":"marksman"
}

def load():
    return json.loads(PATH.read_text(encoding="utf-8"))

def main():
    data = load()
    old = data.get("weapons", {})
    if isinstance(old, list):
        old = {canonical_id(w.get("name",""), w.get("game","")): w for w in old}

    discovered = discover_database()
    if not discovered:
        print("Fonte CODMunity indisponível; mantendo dados anteriores.")
        return 2

    weapons = dict(old)
    failures = 0
    patch = None
    try:
        patch = load_latest_patch()
    except Exception as exc:
        print(f"Activision patch: {exc}")
    ranked = sorted(discovered, key=lambda r: float(r.get("pick_rate") or 0), reverse=True)
    detailed = {r["name"] + "|" + r["game"] for r in ranked[:60]}
    detailed.update(r["name"] + "|" + r["game"] for r in discovered
                    if not weapons.get(canonical_id(r["name"], r["game"]), {}).get("attachments"))
    for row in discovered:
        name, game = row["name"], row["game"]
        # Ignore pure legacy duplicates when a current Warzone version exists.
        wid = canonical_id(name, game)
        w = dict(weapons.get(wid, {}))
        w.update({
            "id": wid, "name": name, "game": game,
            "category": CATEGORY.get(norm(row.get("category_raw")), norm(row.get("category_raw"))),
            "meta_status": row.get("meta_status"),
            "pick_rate": row.get("pick_rate"),
            "source_url": row.get("url"),
        })
        w.setdefault("aliases", [])
        if name.lower() not in [str(x).lower() for x in w["aliases"]]:
            w["aliases"].append(name.lower())

        if name + "|" + game not in detailed:
            w["is_meta"] = str(w.get("meta_status","")).lower() in {"meta","absolute meta","meta absoluta"}
            weapons[wid] = w
            continue

        try:
            cm = codmunity_weapon(name, game)
            if cm.get("ok"):
                if cm.get("meta_status"): w["meta_status"] = cm["meta_status"]
                if cm.get("pick_rate") is not None: w["pick_rate"] = cm["pick_rate"]
                if cm.get("updated"): w["loadout_checked"] = cm["updated"]
                if cm.get("code"): w["code"] = cm["code"]
                if cm.get("attachments"): w["attachments"] = cm["attachments"]
                w["loadout_source"] = "CODMunity"
                w["loadout_source_url"] = cm.get("url")
        except Exception as exc:
            failures += 1
            print(f"CODMunity {name}: {exc}")

        # Confirmation/fallback. Do not replace a good CODMunity class with a worse scrape.
        try:
            wz = wlg_weapon(name, game)
            if wz.get("attachments"):
                if not w.get("attachments"):
                    w["attachments"] = wz["attachments"]
                    w["loadout_source"] = "WarzoneLoadout.games"
                    w["loadout_source_url"] = wz.get("url")
                w["confirmation_source"] = "WarzoneLoadout.games"
                w["confirmation_code"] = wz.get("code")
        except Exception as exc:
            failures += 1
            print(f"WarzoneLoadout {name}: {exc}")

        try:
            act = parse_weapon(patch, name)
            if act.get("ok"):
                w["recent_change"] = {
                    "type": act.get("type"),
                    "changes": act.get("changes") or [],
                    "source": "Activision/Raven Software",
                    "source_url": act.get("url"),
                }
        except Exception as exc:
            failures += 1
            print(f"Activision {name}: {exc}")

        w["is_meta"] = str(w.get("meta_status","")).lower() in {"meta","absolute meta","meta absoluta"}
        weapons[wid] = w

    # Current META lists are generated from live pick rate + status, never from hand-written categories.
    for cat in ("ar","smg","sniper","doze","pt","lmg","marksman"):
        rows = [w for w in weapons.values() if w.get("category") == cat and w.get("is_meta")]
        rows.sort(key=lambda x: float(x.get("pick_rate") or 0), reverse=True)
        data.setdefault("categories", {})[cat] = [w["name"] for w in rows[:10]]

    all_meta = [w for w in weapons.values() if w.get("is_meta")]
    all_meta.sort(key=lambda x: float(x.get("pick_rate") or 0), reverse=True)
    data["general_meta"] = [w["name"] for w in all_meta[:10]]
    data["weapons"] = weapons
    data["api_version"] = "3.0.0"
    data["data_checked"] = __import__("datetime").datetime.now().strftime("%d/%m/%Y")
    data["last_sync"] = now_utc()
    data["sync"] = {
        "status": "ok" if failures < max(5, len(discovered) // 5) else "partial",
        "discovered": len(discovered), "failures": failures,
        "meta_source": "CODMunity Warzone",
        "patch_source": "Activision/Raven Software",
        "loadout_primary": "CODMunity",
        "loadout_confirmation": ["WZHUB", "WarzoneLoadout.games"],
    }
    PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Sincronizado: {len(weapons)} armas; falhas: {failures}")

if __name__ == "__main__":
    sys.exit(main())
