# Warzone API v3 — melhorias

- `!classe` é o comando principal.
- O nome do comando não fica preso na API: StreamElements/SN7 Core pode chamar `/classe` usando qualquer gatilho (`!classe`, `!arma`, `!build` etc.).
- Busca parcial, aliases e desambiguação.
- Prioridade para armas atuais quando existe o mesmo nome em jogos antigos.
- Activision/Raven Software para buff/nerf.
- CODMunity como fonte principal de META/pick rate/classe.
- WZHUB e WarzoneLoadout.games como confirmação/fallback.
- Atualização automática de hora em hora via GitHub Actions.
- Se não houver classe confiável, a API informa isso em vez de inventar acessórios.
- `data/meta.json` NÃO está incluído neste pacote para não apagar os dados atuais do repositório. O `updater.py` faz a migração/mesclagem e adiciona novas armas.
