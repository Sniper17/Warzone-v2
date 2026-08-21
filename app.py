
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
    return {"ok": True, "service": "warzone-api", "version": "3.0.0"}

@app.get("/status")
def status():
    d = catalog.data
    return {
        "online": True, "api_version": "3.0.0",
        "data_checked": d.get("data_checked"),
        "last_sync": d.get("last_sync"),
        "weapons": len(catalog.weapons),
        "primary_meta_source": "CODMunity Warzone",
        "primary_patch_source": "Activision/Raven Software",
        "primary_loadout_source": "CODMunity",
        "loadout_confirmation": ["WZHUB", "WarzoneLoadout.games"],
    }

@app.get("/bo7")
def bo7():
    w = catalog.by_game("Black Ops 7")
    return {"count": len(w), "weapons": sorted(x["name"] for x in w)}

@app.get("/classe")
def classe():
    q = request.args.get("arma", "").strip()
    user = request.args.get("user", "@Gabriel").strip() or "@Gabriel"
    if not q:
        return "⚠️ Informe a arma. Exemplo: !classe an94"
    matches = catalog.search(q)
    if not matches:
        return f"🔎 Não encontrei uma arma chamada {q}. Tente o nome completo ou parte do nome."
    if len(matches) > 1:
        names = ", ".join(x["name"] for x in matches[:6])
        return f"🤔 Qual arma você deseja? {names}"
    return format_class_response(engine.resolve(matches[0]), user)

@app.get("/meta")
def meta():
    q = request.args.get("tipo", "").strip().lower()
    aliases = {"ar":"ar","smg":"smg","sniper":"sniper","doze":"shotgun","shotgun":"shotgun","pt":"pistol","pistola":"pistol"}
    if not q:
        return engine.general_meta()
    if q in aliases:
        return engine.category_meta(aliases[q])
    matches = catalog.search(q)
    if len(matches) > 1:
        return "🤔 Qual arma você deseja? " + ", ".join(x["name"] for x in matches[:6])
    if not matches:
        return f"🔎 Não encontrei uma arma chamada {q}."
    return format_class_response(engine.resolve(matches[0]), request.args.get("user","@Gabriel"))

@app.get("/reload")
def reload_data():
    # Manual local refresh for a deployment; no mutation of the database is performed.
    catalog.reload()
    return {"ok": True, "weapons": len(catalog.weapons), "message": "Dados recarregados."}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
