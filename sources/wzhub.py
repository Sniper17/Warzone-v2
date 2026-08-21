
from __future__ import annotations
import re
from .common import fetch, soup_from_html, clean_text, norm, slugify, normalize_slot, parse_date

URL = "https://wzhub.gg/pt/loadouts"
SLOTS = ["Lente","Boca","Cano","Acoplamento","Carregador","Cabo","Coronha","Laser","Munição","Mods de disparo","Pente"]

def fetch_weapon(name):
    try:
        html = fetch(URL)
    except Exception:
        return {"ok": False, "source": "WZHUB", "url": URL}
    text = clean_text(soup_from_html(html).get_text(" ", strip=True))
    pos = text.lower().find(name.lower())
    if pos < 0:
        return {"ok": False, "source": "WZHUB", "url": URL}
    chunk = text[pos:pos + 1800]
    cm = re.search(r"Loadout code\s+([A-Z0-9][A-Z0-9-]{7,})", chunk, re.I)
    dm = re.search(r"(?:Atualizada|Atualizado|Updated):\s*([A-Z][^|]{5,35}202[0-9])", chunk, re.I)
    attachments = []
    # WZHUB renders attachment name followed by its translated slot.
    for slot in SLOTS:
        m = re.search(r"(.{2,85}?)\s+" + re.escape(slot) + r"(?:\s|$)", chunk, re.I)
        if not m:
            continue
        name_part = clean_text(m.group(1))
        name_part = re.sub(r".*?(?:Loadout code\s+[A-Z0-9-]+\s+)?", "", name_part, flags=re.I)
        if 2 <= len(name_part) <= 85:
            attachments.append({"slot": slot, "name": name_part})
    return {
        "ok": bool(attachments), "source": "WZHUB", "url": URL,
        "code": cm.group(1) if cm else None,
        "updated": parse_date(dm.group(1)) if dm else None,
        "attachments": attachments[:8],
    }
