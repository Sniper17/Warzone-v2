# Warzone API v3.1.1

## Classe rápida
- Fontes externas consultadas em paralelo.
- Prazo global de 4,5 s.
- Fonte lenta não bloqueia o `/classe`.
- Cache de 10 min.
- Fallback do último resultado bom por 30 min.
- WZHUB corrigido para a assinatura atual.

## StreamElements
- Formatter limitado a 380 bytes para ficar abaixo do limite de 400 bytes do `customapi`.
- A resposta é montada por blocos para não cortar um acessório no meio.
