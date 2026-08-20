class MetaEngine:
    """Activision = authoritative patch facts; WZHUB = primary public loadout; others confirm."""
    def __init__(self, catalog): self.catalog = catalog
    def resolve(self, weapon):
        w = dict(weapon); patch = w.get('recent_change') or {}; attachments = w.get('attachments') or []
        meta = str(w.get('tier','')).upper() in {'META','META ABSOLUTA','ABSOLUTE META'} or bool(w.get('is_meta'))
        return {'weapon':w,'status':patch.get('type') if patch.get('type') in {'buff','nerf'} else ('confirmed_loadout' if attachments else 'unconfirmed_loadout'),'meta':meta,'attachments':attachments,'patch':patch,'loadout_source':w.get('loadout_source') or 'WZHUB','confidence':w.get('confidence')}
    def general_meta(self):
        c=self.catalog.data.get('categories',{}); ar=(c.get('ar') or [''])[0]; smg=(c.get('smg') or [''])[0]
        return f'🔥 META WARZONE: 🔫 {ar} (AR) • ⚡ {smg} (SMG)'
    def category_meta(self, cat):
        names=(self.catalog.data.get('categories',{}).get(cat) or [])[:3]
        if not names: return '⚠️ Nenhuma arma META confirmada nessa categoria.'
        labels={'ar':'🔥 META AR','smg':'⚡ META SMG','sniper':'🎯 META SNIPER','doze':'💥 META DOZE','pt':'🔫 META PISTOLAS'}
        return labels.get(cat,'🔥 META')+': '+' • '.join(names)
