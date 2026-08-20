import json, unicodedata
from pathlib import Path

def norm(s):
    s = unicodedata.normalize('NFKD', str(s or '').lower().strip())
    return ''.join(c for c in s if not unicodedata.combining(c))

class WeaponCatalog:
    def __init__(self, path: Path):
        self.path = path
        self.data = json.loads(path.read_text(encoding='utf-8'))
        self.weapons = list(self.data.get('weapons', {}).values())
    def search(self, query):
        q = norm(query)
        if not q: return []
        exact, partial = [], []
        for w in self.weapons:
            names = [w.get('name','')] + w.get('aliases', [])
            ns = [norm(x) for x in names]
            if q in ns: exact.append(w)
            elif any(x.startswith(q) for x in ns): partial.append(w)
            elif len(q) >= 3 and any(q in x for x in ns): partial.append(w)
        if exact: return exact
        seen, out = set(), []
        for w in partial:
            k = norm(w.get('name'))
            if k not in seen: seen.add(k); out.append(w)
        return sorted(out, key=lambda x:(len(norm(x.get('name'))), norm(x.get('name'))))
    def by_game(self, game):
        return [w for w in self.weapons if w.get('game') == game]
