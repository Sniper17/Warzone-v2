import json
from datetime import datetime, timezone
from pathlib import Path
DATA=Path(__file__).resolve().parent/'data/meta.json'
d=json.loads(DATA.read_text(encoding='utf-8')); now=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
d['api_version']='2.0.0'; d['last_sync']=now; d['data_checked']=now[:10]; d['source_policy']={'patch_primary':'Activision','loadout_primary':'WZHUB','confirmation_sources':['WZStats','CODMunity','WarzoneLoadout'],'never_invent_loadout':True}; d['class_search']='exact_partial_ambiguous'
DATA.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print('WARZONE_V2_SYNC_OK',now)
