
import random

PREFIX = {
    "buff": ["⚠️","🔥","⚡"],
    "nerf": ["📉","🎮","⚡","💀"],
    "confirmed_loadout": ["🎯","🔎","⚡"],
    "meta": ["🔥","🎯","⚡"],
}
ORDER = {
    "Boca":1, "Cano":2, "Lente":3, "Carregador":4, "Acoplamento":5,
    "Cabo":6, "Coronha":7, "Laser":8, "Munição":9, "Mods de disparo":10,
    "Pente":11, "Kit de conversão":12,
}

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
    return [f"{x.get('slot')}: {x.get('name')}" for x in rows if x.get("slot") and x.get("name")]

def format_class_response(r, username="@Gabriel"):
    w = r["weapon"]
    name = w.get("name", "Arma")
    changes = (r.get("patch") or {}).get("changes") or []
    typ = r.get("status")
    atts = r.get("attachments") or []

    if not atts and typ == "buff":
        return f"{random.choice(PREFIX['buff'])} {username} {name} em análise | 📈 Buff: {_changes(changes, '+') or 'mudanças de balanceamento'} | Ainda não encontrei um loadout 100% confiável. Vale testar!"
    if not atts and typ == "nerf":
        return f"{random.choice(PREFIX['nerf'])} {username} {name} | 📉 Nerf | {_changes(changes, '↓') or 'Alterações de balanceamento'} | Ainda não há loadout atualizado confirmado."
    if not atts:
        return f"🔎 {username} {name} | Ainda não encontrei um loadout 100% confiável. Estou aguardando confirmação das fontes."

    title = f"META atual da {name}" if r.get("meta") else f"Classe atual da {name}"
    prefix = random.choice(PREFIX["meta"] if r.get("meta") else PREFIX["confirmed_loadout"])
    bits = [f"{prefix} {username} {title}"]
    if typ == "buff" and changes:
        bits.append("📈 Buff: " + _changes(changes, "+"))
    if typ == "nerf" and changes:
        bits.append("📉 Nerf: " + _changes(changes, "↓"))
    bits.extend(_parts(atts))
    return " | ".join(bits)
