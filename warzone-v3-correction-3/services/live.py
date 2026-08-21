from __future__ import annotations
from datetime import datetime, timezone, timedelta
from difflib import SequenceMatcher
import re
import unicodedata

from sources.codmunity import fetch_weapon as codmunity
from sources.warzoneloadout import fetch_weapon as wlg
from sources.wzhub import fetch_weapon as wzhub
from sources.activision import fetch_weapon as activision
from sources.common import norm


class LiveResolver:
    """Combina fontes atuais, normalizando classes antes de medir consenso."""

    def __init__(self, cache_minutes=10):
        self.cache = {}
        self.cache_minutes = cache_minutes

    @staticmethod
    def _norm_text(value):
        value = str(value or "").lower().strip()
        value = unicodedata.normalize("NFKD", value)
        value = "".join(c for c in value if not unicodedata.combining(c))
        value = value.replace("×", "x")
        value = re.sub(r"[^a-z0-9]+", " ", value)
        return re.sub(r"\s+", " ", value).strip()

    @classmethod
    def _attachment_key(cls, item):
        slot = cls._norm_text(item.get("slot", ""))
        name = cls._norm_text(item.get("name", ""))
        # Remove o nome do slot do acessório caso uma fonte o repita.
        if slot and name.endswith(" " + slot):
            name = name[:-(len(slot) + 1)]
        return slot, name

    @classmethod
    def _attachment_similarity(cls, a_items, b_items):
        """Compara classes por slot, dando mais peso aos slots principais.

        A quantidade total de acessórios não deve derrubar a confiança quando
        uma fonte simplesmente publica slots extras (Laser, Mods etc.).
        """
        if not a_items or not b_items:
            return 0.0

        a = {}
        b = {}
        for item in a_items:
            slot, name = cls._attachment_key(item)
            if slot and name:
                a[slot] = name
        for item in b_items:
            slot, name = cls._attachment_key(item)
            if slot and name:
                b[slot] = name

        if not a or not b:
            return 0.0

        core = {
            "lente", "boca", "cano", "acoplamento",
            "carregador", "coronha", "cabo", "municao"
        }
        common_slots = set(a) & set(b)
        if not common_slots:
            return 0.0

        weighted_total = 0.0
        weighted_match = 0.0
        for slot in common_slots:
            left, right = a[slot], b[slot]
            if left == right:
                score = 1.0
            else:
                score = SequenceMatcher(None, left, right).ratio()
                lt, rt = set(left.split()), set(right.split())
                if lt and rt:
                    score = max(score, len(lt & rt) / len(lt | rt))
            weight = 2.0 if slot in core else 1.0
            weighted_total += weight
            weighted_match += weight * score

        # Cobertura dos slots principais que pelo menos uma das fontes possui.
        core_union = (set(a) | set(b)) & core
        core_overlap = (common_slots & core)
        coverage = len(core_overlap) / len(core_union) if core_union else 0.0

        base = weighted_match / weighted_total if weighted_total else 0.0
        # Não penaliza slots extras de uma fonte; penaliza apenas divergência
        # nos slots principais que ambas realmente oferecem.
        result = base * (0.70 + 0.30 * coverage)
        return round(result, 4)

    @classmethod
    def _normalize_loadout(cls, data):
        """Garante uma estrutura consistente para comparação e formatter."""
        if not data:
            return {}
        chosen = dict(data)
        attachments = []
        seen = set()
        for item in data.get("attachments") or []:
            if not isinstance(item, dict):
                continue
            slot = str(item.get("slot") or "").strip()
            name = str(item.get("name") or "").strip()
            if not slot or not name:
                continue
            key = (cls._norm_text(slot), cls._norm_text(name))
            if key in seen:
                continue
            seen.add(key)
            attachments.append({"slot": slot, "name": name})
        chosen["attachments"] = attachments
        return chosen

    @classmethod
    def _choose_loadout(cls, cm, wz, zh):
        valid = [
            ("CODMunity", cls._normalize_loadout(cm)),
            ("WarzoneLoadout.games", cls._normalize_loadout(wz)),
            ("WZHUB", cls._normalize_loadout(zh)),
        ]
        valid = [(n, d) for n, d in valid if d.get("attachments")]

        if not valid:
            return {}, "nenhuma", 0.0

        best = None
        for i, (na, a) in enumerate(valid):
            for nb, b in valid[i + 1:]:
                sim = cls._attachment_similarity(a["attachments"], b["attachments"])
                if sim >= 0.55 and (best is None or sim > best[0]):
                    best = (sim, na, a, nb, b)

        if best:
            sim, na, a, nb, b = best

            # Quando há consenso, escolhe a versão mais completa. Em empate,
            # mantém a prioridade CODMunity -> WarzoneLoadout -> WZHUB.
            priority = {"CODMunity": 3, "WarzoneLoadout.games": 2, "WZHUB": 1}
            if (len(b["attachments"]), priority.get(nb, 0)) > (len(a["attachments"]), priority.get(na, 0)):
                chosen = dict(b)
            else:
                chosen = dict(a)

            chosen["confirmation"] = f"{na} + {nb}"
            chosen["consensus_sources"] = [na, nb]
            chosen["consensus_details"] = {
                "score": round(sim, 3),
                "common_slots": len(set(x.get("slot") for x in a["attachments"]) & set(x.get("slot") for x in b["attachments"])),
                "source_slots": {na: len(a["attachments"]), nb: len(b["attachments"])},
            }
            return chosen, chosen["confirmation"], sim

        # Sem consenso, CODMunity continua sendo a fonte principal.
        na, a = valid[0]
        chosen = dict(a)
        chosen["confirmation"] = na
        chosen["consensus_sources"] = [na]
        return chosen, na, 0.0

    @staticmethod
    def _meta(cm, wz, zh):
        values = [cm.get("meta_status"), wz.get("meta_status"), zh.get("meta_status")]
        values = [x for x in values if x]

        if not values:
            return None, "nao_confirmado"

        normalized = [norm(x) for x in values]
        if any("absolute" in x for x in normalized):
            return "Absolute Meta", "alta"
        if any(x == "meta" or x.endswith(" meta") for x in normalized):
            return "Meta", "alta" if len(values) >= 2 else "boa"

        return values[0], "boa" if len(values) >= 2 else "provavel"

    @staticmethod
    def _loadout_confidence(chosen, confirmation, consensus):
        if not chosen.get("attachments"):
            return "nenhuma"
        if consensus >= 0.85:
            return "alta"
        if consensus >= 0.70:
            return "boa"
        if confirmation == "CODMunity":
            return "boa"
        if confirmation == "WarzoneLoadout.games":
            return "provavel"
        return "baixa"

    def resolve(self, weapon):
        key = f"{weapon.get('game', 'Black Ops 7')}:{weapon.get('name', '')}"
        now = datetime.now(timezone.utc)

        cached = self.cache.get(key)
        if cached and now < cached["expires_at"]:
            return cached["data"]

        name = weapon.get("name")
        game = weapon.get("game", "Black Ops 7")
        sources = {}

        for key_name, fn in (
            ("codmunity", lambda: codmunity(name, game)),
            ("warzoneloadout", lambda: wlg(name, game)),
            ("wzhub", lambda: wzhub(name, game)),
            ("patch", lambda: activision(name)),
        ):
            try:
                sources[key_name] = fn() or {}
            except Exception as exc:
                sources[key_name] = {"ok": False, "error": type(exc).__name__}

        cm = sources["codmunity"]
        wz = sources["warzoneloadout"]
        zh = sources["wzhub"]
        patch = sources["patch"]

        chosen, confirmation, consensus = self._choose_loadout(cm, wz, zh)
        loadout_confidence = self._loadout_confidence(chosen, confirmation, consensus)
        meta_status, meta_confidence = self._meta(cm, wz, zh)

        data = {
            "loadout": chosen,
            "confirmation": confirmation,
            "loadout_confidence": loadout_confidence,
            "loadout_consensus": round(consensus, 3),
            "meta_status": meta_status,
            "meta_confidence": meta_confidence,
            "pick_rate": cm.get("pick_rate"),
            "patch": patch,
            "codmunity": cm,
            "warzoneloadout": wz,
            "wzhub": zh,
            "refreshed": now.isoformat(timespec="seconds"),
        }

        self.cache[key] = {
            "expires_at": now + timedelta(minutes=self.cache_minutes),
            "data": data,
        }
        return data
