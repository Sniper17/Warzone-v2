from flask import Flask, request
from pathlib import Path
import os

from services.catalog import WeaponCatalog
from services.meta_engine import MetaEngine
from services.formatter import format_class_response

app = Flask(__name__)

BASE = Path(__file__).resolve().parent
catalog = WeaponCatalog(BASE / "data" / "meta.json")
engine = MetaEngine(catalog)


@app.get("/")
def home():
    return "🔥 Warzone API v3 online!"


@app.get("/health")
def health():
    return {
        "ok": True,
        "service": "warzone-api",
        "version": "3.5-bo7-whitelist-class-only",
    }


@app.get("/status")
def status():
    d = catalog.data
    return {
        "online": True,
        "api_version": "3.5-bo7-whitelist-class-only",
        "data_checked": d.get("data_checked"),
        "last_sync": d.get("last_sync"),
        "weapons": len(catalog.weapons),
        "active_game": d.get("active_game", "Black Ops 7"),
        "mode": "classe_loadout_only",
    }


@app.get("/bo7")
def bo7():
    w = catalog.by_game("Black Ops 7")
    return {
        "count": len(w),
        "weapons": sorted(x["name"] for x in w),
    }


@app.get("/classe")
def classe():
    q = request.args.get("arma", "").strip()

    if not q:
        return "⚠️ Informe a arma. Exemplo: !classe an94"

    matches = catalog.search(q)

    if not matches:
        return (
            f"🔎 Não encontrei uma arma chamada {{q}}. "
            "Tente o nome completo ou parte do nome."
        )

    if len(matches) > 1:
        names = ", ".join(x["name"] for x in matches[:6])
        return f"🤔 Qual arma você deseja? {{names}}"

    return format_class_response(engine.resolve(matches[0]))


@app.get("/reload")
def reload_data():
    catalog.reload()
    return {
        "ok": True,
        "weapons": len(catalog.weapons),
        "message": "Dados recarregados.",
    }


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
    )
