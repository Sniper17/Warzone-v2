
from __future__ import annotations
import re
from .common import fetch, soup_from_html, clean_text, norm

BASE = "https://www.callofduty.com"
INDEX = f"{BASE}/patchnotes"

KEYWORDS = [
    ("damage range", "Alcance"), ("damage", "Dano"), ("range", "Alcance"),
    ("recoil", "Estabilidade"), ("aim down sight", "ADS"), ("ads speed", "ADS"),
    ("bullet velocity", "Velocidade da bala"), ("fire rate", "Cadência"),
    ("movement", "Mobilidade"), ("magazine", "Carregador"),
    ("reload", "Recarga"), ("handling", "Manuseio"), ("headshot", "Dano de cabeça"),
]

_PATCH_CACHE = None

def latest_warzone_patch():
    html = fetch(INDEX)
    soup = soup_from_html(html)
    candidates = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/patchnotes/" not in href or "warzone" not in href.lower():
            continue
        full = href if href.startswith("http") else BASE + href
        m = re.search(r"/patchnotes/(\\d{4}/\\d{2})/", href)
        candidates.append((m.group(1) if m else "", full))
    if not candidates:
        return None
    return sorted(set(candidates), reverse=True)[0][1]

def load_latest_patch(force=False):
    global _PATCH_CACHE
    if _PATCH_CACHE and not force:
        return _PATCH_CACHE
    url = latest_warzone_patch()
    if not url:
        return None
    html = fetch(url)
    text = clean_text(soup_from_html(html).get_text(" ", strip=True))
    _PATCH_CACHE = {"url": url, "text": text}
    return _PATCH_CACHE

def _weapon_chunk(text, weapon_name):
    pat = re.compile(r"Weapon:\\s*" + re.escape(weapon_name) + r"(.*?)(?=Weapon:\\s*[A-Z0-9][A-Z0-9 .’'/-]{2,45}\\s|$)", re.I | re.S)
    m = pat.search(text)
    return m.group(1) if m else ""

def _changes(chunk):
    if not chunk:
        return [], None
    lines = [clean_text(x) for x in re.split(r"[.;•]", chunk) if clean_text(x)]
    labels, ups, downs = [], 0, 0
    for line in lines:
        low = norm(line)
        up = bool(re.search(r"\b(increased|improved|raised|boosted|faster)\b|[↑⇧]", low))
        down = bool(re.search(r"\b(decreased|reduced|slowed|lowered|worse)\b|[↓⇩]", low))
        if up: ups += 1
        if down: downs += 1
        for key, label in KEYWORDS:
            if key in low:
                if label not in labels:
                    labels.append(label)
                break
    if ups > downs: typ = "buff"
    elif downs > ups: typ = "nerf"
    elif ups or downs: typ = "mixed"
    else: typ = None
    return labels[:6], typ

def parse_weapon(patch, name):
    if not patch:
        return {"ok": False, "source": "Activision"}
    chunk = _weapon_chunk(patch["text"], name)
    changes, typ = _changes(chunk)
    return {
        "ok": bool(chunk), "source": "Activision/Raven Software",
        "url": patch["url"], "changes": changes, "type": typ
    }

def fetch_weapon(name):
    return parse_weapon(load_latest_patch(), name)
