import random
PREFIX={'buff':['⚠️','🔥','⚡'],'nerf':['🎮','⚡','💀','🔥'],'confirmed_loadout':['🔎','🎯','⚡'],'meta':['🔥','🎯','⚡']}
ORDER={'Boca':1,'Silenciador':1,'Cano':2,'Lente':3,'Mira':3,'Carregador':4,'Pente':4,'Acoplamento':5,'Cabo':6,'Empunhadura':6,'Coronha':7,'Laser':8,'Munição':9,'Mods de disparo':10,'Kit de conversão':11}
def parts(atts):
    a=sorted(atts,key=lambda x:ORDER.get(x.get('slot'),99)); return [f"{x.get('slot')}: {x.get('name')}" for x in a if x.get('slot') and x.get('name')]
def format_class_response(r, username='@Gabriel'):
    w=r['weapon']; name=w.get('name','Arma'); p=r.get('patch') or {}; changes=p.get('changes') or []; typ=p.get('type'); atts=r.get('attachments') or []
    if not atts and typ=='buff':
        return f"{random.choice(PREFIX['buff'])} {username} {name} em análise | 📈 Buff: {' + '.join(changes) if changes else 'mudanças de balanceamento'} | Ainda não encontrei um loadout 100% confiável. Vale testar!"
    if not atts and typ=='nerf':
        detail=' | '.join(f'{c} ↓' for c in changes) if changes else 'Alterações de balanceamento'
        return f"{random.choice(PREFIX['nerf'])} {username} {name} | 📉 Nerf | {detail} | Ainda não há loadout atualizado confirmado."
    if atts:
        title=f"META {name}" if r.get('meta') else f"Classe atual {name}"; bits=[f"{random.choice(PREFIX['meta'] if r.get('meta') else PREFIX['confirmed_loadout'])} {username} {title}"]
        if typ=='buff' and changes: bits.append('📈 Buff: '+' + '.join(changes))
        if typ=='nerf' and changes: bits.append('📉 Nerf: '+' | '.join(f'{c} ↓' for c in changes))
        bits += parts(atts); return ' | '.join(bits)
    return f'🔎 {username} {name} | Ainda não encontrei um loadout 100% confiável.'
