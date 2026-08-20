from flask import Flask, request
from pathlib import Path
from services.catalog import WeaponCatalog
from services.meta_engine import MetaEngine
from services.formatter import format_class_response
app=Flask(__name__); base=Path(__file__).resolve().parent; catalog=WeaponCatalog(base/'data/meta.json'); engine=MetaEngine(catalog)
@app.get('/')
def home(): return '🔥 Warzone API v2 online!'
@app.get('/health')
def health(): return {'ok':True,'service':'warzone-api','version':'2.0.0'}
@app.get('/status')
def status():
 d=catalog.data; return {'online':True,'api_version':'2.0.0','data_checked':d.get('data_checked'),'last_sync':d.get('last_sync'),'weapons':len(d.get('weapons',{})),'primary_loadout_source':'WZHUB','primary_patch_source':'Activision','confirmation_sources':['WZStats','CODMunity','WarzoneLoadout']}
@app.get('/bo7')
def bo7():
 w=catalog.by_game('Black Ops 7'); return {'count':len(w),'weapons':sorted(x['name'] for x in w)}
@app.get('/classe')
def classe():
 q=request.args.get('arma','').strip()
 if not q:return '⚠️ Informe a arma. Exemplo: /classe?arma=an94'
 m=catalog.search(q)
 if not m:return f'🔎 Não encontrei uma arma chamada {q}.'
 if len(m)>1:return '🤔 Qual arma você deseja? '+', '.join(x['name'] for x in m[:6])
 return format_class_response(engine.resolve(m[0]), '@'+request.args.get('user','Gabriel'))
@app.get('/meta')
def meta():
 q=request.args.get('tipo','').strip().lower(); aliases={'ar':'ar','smg':'smg','sniper':'sniper','doze':'doze','shotgun':'doze','pt':'pt','pistola':'pt','pistolas':'pt'}
 if not q:return engine.general_meta()
 if q in aliases:return engine.category_meta(aliases[q])
 m=catalog.search(q)
 if len(m)>1:return '🤔 Qual arma você deseja? '+', '.join(x['name'] for x in m[:6])
 if not m:return f'🔎 Não encontrei uma arma chamada {q}.'
 return format_class_response(engine.resolve(m[0]), '@'+request.args.get('user','Gabriel'))
if __name__=='__main__': app.run(host='0.0.0.0',port=int(__import__('os').environ.get('PORT',5000)))
