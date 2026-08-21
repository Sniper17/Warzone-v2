import random

PREFIX = {
    "buff": ["⚠️", "🔥", "⚡"],
    "nerf": ["📉", "🎮", "⚡", "💀"],
    "confirmed_loadout": ["🎯", "🔎", "⚡"],
    "meta": ["🔥", "🎯", "⚡"],
}

ORDER = {
    "Boca": 1, "Cano": 2, "Lente": 3, "Carregador": 4,
    "Acoplamento": 5, "Cabo": 6, "Coronha": 7, "Laser": 8,
    "Munição": 9, "Mods de disparo": 10, "Pente": 11,
    "Kit de conversão": 12,
}

# O customapi do StreamElements limita a resposta a 400 bytes.
MAX_BYTES = 380


def _changes(changes, arrow=None):
    labels = []
    for c in changes or []:
        c = str(c).strip().rstrip("+↓ ")
        if c and c not in labels:
            labels.append(c)

    if arrow == "↓":
        return " | ".join(f"{x} ↓" for x in labels)
    if arrow == "+":
        return " + ".join(labels)
    return " | ".join(labels)


def _parts(atts):
    rows = sorted(atts, key=lambda x: ORDER.get(x.get("slot"), 99))
    return [
        f"{x.get('slot')}: {x.get('name')}"
        for x in rows
        if x.get("slot") and x.get("name")
    ]


def _fit_bytes(parts, limit=MAX_BYTES):
    """Monta a resposta sem ultrapassar o limite do StreamElements."""
    if not parts:
        return ""

    result = parts[0]

    for part in parts[1:]:
        candidate = result + " | " + part
        if len(candidate.encode("utf-8")) > limit:
            break
        result = candidate

    return result


def format_class_response(r, username="@Gabriel"):
    w = r["weapon"]
    name = w.get("name", "Arma")
    changes = (r.get("patch") or {}).get("changes") or []
    typ = r.get("status")
    atts = r.get("attachments") or []

    if not atts and typ == "buff":
        return _fit_bytes([
            f"{random.choice(PREFIX['buff'])} {username} {name} em análise",
            f"📈 Buff: {_changes(changes, '+') or 'mudanças de balanceamento'}",
            "Loadout ainda não confirmado",
        ])

    if not atts and typ == "nerf":
        return _fit_bytes([
            f"{random.choice(PREFIX['nerf'])} {username} {name}",
            "📉 Nerf",
            _changes(changes, "↓") or "Alterações de balanceamento",
            "Loadout ainda não confirmado",
        ])

    if not atts:
        return f"🔎 {username} {name} | Loadout ainda não confirmado."

    title = f"META atual da {name}" if r.get("meta") else f"Classe atual da {name}"
    prefix = random.choice(
        PREFIX["meta"] if r.get("meta") else PREFIX["confirmed_loadout"]
    )

    parts = [f"{prefix} {username} {title}"]

    if typ == "buff" and changes:
        parts.append("📈 Buff: " + _changes(changes, "+"))

    if typ == "nerf" and changes:
        parts.append("📉 Nerf: " + _changes(changes, "↓"))

    parts.extend(_parts(atts))
    return _fit_bytes(parts)
