
from __future__ import annotations
import re
from .common import fetch, soup_from_html, clean_text, norm, slugify, game_slug, parse_date, normalize_slot

BASE = "https://codmunity.gg"
WARZONE_URL = f"{BASE}/pt/warzone"
DATABASE_URL = f"{BASE}/database/weapons"

def _text(soup):
    return clean_text(soup.get_text(" ", strip=True))

def _meta_status(text):
    m = re.search(r"(?:WZ Meta Status|Meta Status)\s+(Absolute Meta|Meta|Very Good|Contender|Viable|Acceptable|Unrated)", text, re.I)
    return m.group(1) if m else None

def _pick_rate(text):
    for pat in (r"Pick Rate\s*([0-9]+(?:\.[0-9]+)?)\s*%",
                r"taxa de escolha atual.*?([0-9]+(?:\.[0-9]+)?)\s*%",
                r"([0-9]+(?:\.[0-9]+)?)\s*%\s*Pick"):
        m = re.search(pat, text, re.I)
        if m:
            try: return float(m.group(1))
            except ValueError: pass
    return None

def _code(text):
    m = re.search(r"(?:Code|Código|Loadout Code)\s*:\s*([A-Z0-9][A-Z0-9-]{7,})", text, re.I)
    return m.group(1) if m else None

def _attachments(text):
    slots = ["Optic","Muzzle","Barrel","Underbarrel","Magazine","Stock","Rear Grip","Fire Mods","Laser","Comb","Ammunition"]
    # CODMunity's rendered text usually puts the slot after the attachment.
    found = []
    for i, slot in enumerate(slots):
        for m in re.finditer(r"(.{2,90}?)\s+" + re.escape(slot) + r"(?:\s|$)", text, re.I):
            name = clean_text(m.group(1))
            name = re.sub(r"^(?:Image|Attachments?)\s+", "", name, flags=re.I)
            if 2 <= len(name) <= 70 and not any(x["name"].lower() == name.lower() for x in found):
                # Avoid swallowing headings by preferring the last phrase.
                name = name.split(" Image ")[-1].strip()
                if name and name.lower() not in {s.lower() for s in slots}:
                    found.append({"slot": normalize_slot(slot), "name": name})
                    break
    return found[:8]

def weapon_url(name, game="Black Ops 7"):
    return f"{BASE}/pt/weapon/{game_slug(game)}/{slugify(name)}"

def fetch_weapon(name, game="Black Ops 7"):
    url = weapon_url(name, game)
    try:
        html = fetch(url)
    except Exception:
        return {"ok": False, "source": "CODMunity", "url": url}
    soup = soup_from_html(html)
    text = _text(soup)
    data = {
        "ok": True, "source": "CODMunity", "url": url,
        "meta_status": _meta_status(text),
        "pick_rate": _pick_rate(text),
        "code": _code(text),
        "attachments": _attachments(text),
    }
    m = re.search(r"(?:Last Updated|Última atualização|Atualizado)\s*[:\-]?\s*([A-Z][^|]{5,35}202[0-9])", text, re.I)
    data["updated"] = parse_date(m.group(1)) if m else None
    # FAQ is surprisingly stable and gives the current best build.
    faq = re.search(r"(?:Qual é o melhor armamento.*?Para os acessórios, você deve usar:)(.*?)(?:A AN-94|A .{2,20} é fácil|Quais são as melhores alternativas|Qual é a taxa de escolha)", text, re.I)
    data["faq_loadout_text"] = clean_text(faq.group(1)) if faq else None
    return data

def discover_warzone():
    html = fetch(WARZONE_URL)
    soup = soup_from_html(html)
    text = _text(soup)
    results = []
    # Main Warzone ranking has explicit weapon headings and pick rates.
    pattern = re.compile(
        r"(?:###\s*)?([A-Z][A-Za-z0-9 .’'/-]{1,35})\s+(?:New|Pro Favorite|Meta|Absolute Meta|Muito Bom|Novo)?\s*"
        r".{0,180}?(?:([0-9]+(?:\.[0-9]+)?)\s*%\s*Pick)",
        re.I
    )
    seen = set()
    for m in pattern.finditer(text):
        name = clean_text(m.group(1))
        if len(name) < 2 or name.lower() in {"warzone", "assault rifle", "smg", "sniper rifle"}:
            continue
        key = norm(name)
        if key in seen: continue
        seen.add(key)
        results.append({"name": name, "pick_rate": float(m.group(2))})
    return results

def discover_database():
    rows = []
    seen = set()
    for page in range(1, 11):
        url = DATABASE_URL if page == 1 else f"{DATABASE_URL}?page={page}"
        try:
            html = fetch(url)
        except Exception:
            break
        soup = soup_from_html(html)
        page_added = 0
        for tr in soup.find_all("tr"):
            cells = [clean_text(x.get_text(" ", strip=True)) for x in tr.find_all(["td","th"])]
            if len(cells) < 5:
                continue
            links = tr.find_all("a", href=True)
            href = next((a.get("href","") for a in links if "/weapon/" in a.get("href","")), "")
            if not href:
                continue
            name, game, category, status, pick = cells[0], cells[1], cells[2], cells[3], cells[4]
            if name.lower() in {"weapon name","nome da arma"}:
                continue
            m = re.search(r"([0-9]+(?:\.[0-9]+)?)", pick)
            key = (norm(name), norm(game))
            if key in seen:
                continue
            seen.add(key)
            rows.append({
                "name": name, "game": game, "category_raw": category,
                "meta_status": status, "pick_rate": float(m.group(1)) if m else None,
                "url": href if href.startswith("http") else BASE + href
            })
            page_added += 1
        if page_added == 0:
            break
    return rows
