# Warzone API v3

API focada no comando principal `!classe`.

## Como funciona

1. **Activision/Raven Software** é a fonte oficial para buff, nerf e mudanças de balanceamento.
2. **CODMunity Warzone** é a fonte principal para status de META, pick rate e melhor classe.
3. **WZHUB** e **WarzoneLoadout.games** são fontes de confirmação/fallback para classes.
4. A API nunca inventa acessórios. Sem confirmação suficiente, informa que a classe ainda está em análise.
5. O GitHub Actions sincroniza os dados de hora em hora e também pode ser executado manualmente.

## Comando

O endpoint principal é `/classe?arma=AN-94&user=@Gabriel`.

No StreamElements, o nome do comando pode ser `!classe`, `!arma`, `!build` ou qualquer outro. O nome do comando fica no próprio StreamElements/SN7 Core; a API não depende do texto `!classe`.

Exemplos:

- `!classe an94`
- `!classe mk35`
- `!classe carbon`
- `!classe ak`

Quando houver mais de uma correspondência, a API pede a escolha.

## Fallbacks

Buff sem classe confirmada:
`⚠️ @Gabriel AN-94 em análise | 📈 Buff: Dano + Alcance + Estabilidade | Ainda não encontrei um loadout 100% confiável. Vale testar!`

Nerf sem classe confirmada:
`📉 @Gabriel AN-94 | 📉 Nerf | Dano ↓ | Alcance ↓ | Ainda não há loadout atualizado confirmado.`

Com classe confirmada:
`🎯 @Gabriel META atual da AN-94 | Lente: ... | Boca: ... | Cano: ...`

A V3 mantém `/meta` por compatibilidade, mas `!classe` é o comando principal.
