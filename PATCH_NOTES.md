# Warzone API v3 — correção do !classe

- Removidos os rótulos META, BOA e RUIM das respostas de `!classe`.
- `!classe` agora mostra somente a arma e o loadout confirmado.
- Buff/nerf continua sendo exibido quando a fonte de patch confirmar a alteração, com o que mudou.
- O loadout continua sendo de uma única fonte confirmada; nunca mistura acessórios para montar um build.
- Máximo de 5 acessórios por arma. Quando a fonte fornecer 5 acessórios válidos, os 5 são preservados.
- Não são escolhidos "os melhores" acessórios pelo sistema; são exibidos os acessórios do build realmente encontrado na fonte.
- A lógica interna de META permanece disponível para os comandos gerais de META, mas não aparece no texto de `!classe`.
