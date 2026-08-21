
from __future__ import annotations
import re
from .common import fetch, soup_from_html, clean_text, slugify, parse_date, normalize_slot

BASE = "https://warzoneloadout.games"
SLOT_RE = re.compile(
    r"(Muzzle|Barrel|Optic|Underbarrel|Magazine|Stock|Rear Grip|Fire Mods|Laser|Comb|Ammunition):\s*(.*?)"
    r"(?=\s+(?:Muzzle|Barrel|Optic|Underbarrel|Magazine|Stock|Rear Grip|Fire Mods|Laser|Comb|Ammunition):|"
    r"\s+Updated:|\s+Atualizado:|$)", re.I
)

def fetch_weapon(name, game="Black Ops 7"):
    slug = slugify(name)
    game_slug = "bo7" if game.lower().startswith("black ops 7") else ("mw4" if "modern warfare 4" in game.lower() else "mw3")
    url = f"{BASE}/{game_slug}/{slug}/"
    try:
        html = fetch(url)
    except Exception:
        return {"ok": False, "source": "WarzoneLoadout.games", "url": url}
    soup = soup_from_html(html)
    text = clean_text(soup.get_text(" ", strip=True))
    if name.lower() not in text.lower():
        return {"ok": False, "source": "WarzoneLoadout.games", "url": url}
    # Prefer the first Warzone loadout block.
    start = text.lower().find(f"{name.lower()} warzone loadouts")
    chunk = text[start:start + 6000] if start >= 0 else text[:6000]
    matches = SLOT_RE.findall(chunk)
    attachments = []
    for slot, value in matches:
        value = clean_text(value)
        if value and len(value) < 90 and not any(a["slot"] == normalize_slot(slot) for a in attachments):
            attachments.append({"slot": normalize_slot(slot), "name": value})
    dm = re.search(r"(?:Updated|Atualizado):\s*([A-Z][^|]{5,35}202[0-9])", chunk, re.I)
    cm = re.search(r"(?:Loadout Code|Código):\s*([A-Z0-9-]{8,})", chunk, re.I)
    return {
        "ok": bool(attachments),
        "source": "WarzoneLoadout.games",
        "url": url,
        "attachments": attachments[:8],
        "code": cm.group(1) if cm else None,
        "updated": parse_date(dm.group(1)) if dm else None,
    }
