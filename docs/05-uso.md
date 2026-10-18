# 5. Usando no chat

Os comandos funcionam com `$` (Codex) ou `/` (Claude Code). Troque `clef-flash` por `clef-full` para usar o Full.

## 5.1 Comandos

| Comando | O que faz |
| --- | --- |
| `$clef-flash on` | confere o status e ativa na conversa (pergunta antes de iniciar o container) |
| `$clef-flash status` | mostra containers e `readyz` |
| `$clef-flash ask ...` | faz uma decisão |
| `$clef-flash start` / `stop` | liga/desliga o container (o outro modelo é parado) |
| `$clef-flash off` | desativa na conversa |

## 5.2 Exemplos no chat

- **noul (urgência):** `$clef-flash ask "O servidor caiu e ninguém acessa o site": é urgente?`
- **choice (setor):** `$clef-flash ask classifique "Não consigo pagar a fatura" entre financeiro, suporte, vendas`
- **score 1 a 5:** `$clef-flash ask dê uma nota de 1 (calmo) a 5 (furioso) para este e-mail: "..."`
- **revisão de código (noul):** `$clef-flash ask este diff altera autenticação? <diff>`
- **várias perguntas:** `$clef-flash ask sobre este ticket: é urgente? qual setor (ti, rh, financeiro)? gravidade de 0 a 2?`

## 5.3 Lendo as probabilidades

- `noul`: número de 0 a 1 com a chance de "sim". 0,94 é "quase certamente sim"; entre 0,35 e 0,65 é incerto.
- `choice`: uma probabilidade por opção; somam 1. Olhe a maior e a distância para a segunda.
- `score`: valor contínuo na sua escala, com o nível e o rótulo mais próximos.
- `confidence` abaixo de 0,60, ou duas opções com diferença menor que 0,20, indica incerteza: o modelo principal revisa, e vale repetir a pergunta no Full.

## 5.4 Flash ou Full?

- **Flash:** muitas decisões, respostas rápidas, pouca VRAM.
- **Full:** quando a precisão importa mais ou o Flash veio incerto. Entradas de até ~8 mil tokens.

## 5.5 Marcador de estado final

Toda resposta termina com um destes:

- `⚡ Clef Flash usado — tipos: ...`
- `🟡 Clef Flash consultado, mas não utilizado — confiança insuficiente`
- `⚪ Clef Flash não usado — <motivo>`
- `🔴 Clef Flash falhou — resposta produzida pelo modelo principal`

## 5.6 Uso direto pela linha de comando

```powershell
python skills/clef-flash/scripts/clef_call.py status
python skills/clef-flash/scripts/clef_call.py ask --state "Site fora do ar" --noul "É urgente?"
python skills/clef-flash/scripts/clef_call.py ask --state "Não consigo pagar" --choice "Qual setor?" --options financeiro,suporte,vendas
python skills/clef-flash/scripts/clef_call.py ask --state "Muito ruim" --score "Quão insatisfeito?" --levels "1:calmo,2:leve,3:médio,4:alto,5:furioso"
python skills/clef-flash/scripts/clef_call.py ask --json pedido.json
```
