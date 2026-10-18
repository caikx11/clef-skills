---
name: clef-full
description: Usa o Clef Full local (Docker, 127.0.0.1:8081) para decisões estruturadas choice, score e noul, como alternativa ao laya. Somente invocação explícita pelo usuário - "$clef-full on", "$clef-full off", "$clef-full status", "$clef-full ask", "$clef-full start" ou "$clef-full stop" (ou "/clef-full ..."). Nunca use por conta própria.
disable-model-invocation: true
allow_implicit_invocation: false
---

# Skill `clef-full`

Usa só o **Clef Full** (container `clef-full`, `127.0.0.1:8081`, modelo da API `clef`). Regra de ouro: **o Clef decide; o modelo principal escreve.**

- Cliente: `scripts/clef_call.py` (biblioteca padrão do Python 3; no Windows `python` ou `py -3`). Modelo fixo; independe da skill `clef`.
- **Nunca envie dados para outro endereço**; o script recusa hosts não locais (`CLEF_URL` sobrescreve). Sem chaves de API.
- Flash e Full **não rodam juntos** (16 GB de VRAM): iniciar este para o outro container antes.
- **Cuidados do Full:** usa ~12,7 GB de VRAM (pico ~14,7 GB com ~10k tokens): mantenha entradas em **até ~8k tokens**. Subir leva ~1-2 min (timeout 5 min). Latência: ~1-1,5 s frio, ~0,4 s quente.

## Estado (só na conversa atual)

Começa **desativado**. Não grave em arquivo. Nenhum `ask` antes de `$clef-full on`.

## Comandos

### `$clef-full on`
1. Rode `python scripts/clef_call.py status`.
2. Se `ok` for `true`: ative. Estado: `⚪ Clef Full não usado — ativado, nenhuma decisão feita ainda`.
3. Se o container `clef-full` não estiver rodando: **não ative nem inicie**; **pergunte** se pode iniciá-lo (isso para o outro container e leva ~1-2 min) e espere o sim. Com o sim, rode `python scripts/clef_call.py start` (espera o `/readyz`, até 300 s) e ative.
4. Se o Docker não for encontrado, informe e não ative.

### `$clef-full off`
Desative. Não rode o script. Estado: `⚪ Clef Full não usado — desativado`.

### `$clef-full status`
Rode `status`: estado da skill, containers, `readyz`. Estado: `⚪ Clef Full não usado — apenas status consultado`.

### `$clef-full start` / `$clef-full stop`
Só quando o usuário digitar o comando. `python scripts/clef_call.py start` para o outro container, inicia este e espera o `/readyz` (leva ~1-2 min). `stop` para só este. Nunca por conta própria.

### `$clef-full ask`
Monte o pedido e rode:

```
python scripts/clef_call.py ask --context "..." --state "texto a avaliar" --noul "pergunta sim/não"
python scripts/clef_call.py ask --state "..." --choice "pergunta" --options a,b,c
python scripts/clef_call.py ask --state "..." --score "pergunta" --levels "0:sem impacto,1:leve,2:grave"
python scripts/clef_call.py ask --json pedido.json     # ou --json - para stdin
```
- `--state` é o texto principal (a API exige `state`). `--context` é opcional (instruções reutilizáveis, vem antes). Só com `--context`, ele vira o `state`.
- `--levels "1:nenhum,2:leve,..."`: a API usa índice 0..N-1; o script devolve em `score` os campos `nivel`, `rotulo` e `score` na sua escala, e `score_raw` (bruto).
- `--json` aceita arquivo com ou sem BOM UTF-8 e o payload completo da API. `--timeout` (padrão 120 s) vai antes do subcomando.
- `choice`: opções com nomes claros. `score`: níveis crescentes. `noul`: probabilidade de "sim" (0 a 1).
- Só para decisões `choice`, `score` e `noul`; não para gerar texto, resumir nem raciocinar em etapas.
- `state`/`context` podem ter texto real do usuário: envie só o necessário (fica na máquina local).

Devolva por pergunta: escolha/valor, probabilidades principais e confiança.

### Revisão de incerteza
Se `confidence` < 0,60, as duas maiores probabilidades diferirem menos de 0,20, ou `noul` ficar entre 0,35 e 0,65: revise com o modelo principal e sinalize a incerteza.

## Estado final (obrigatório)

Toda resposta termina com **exatamente um**:

- `⚡ Clef Full usado — tipos: <choice/score/noul>`
- `🟡 Clef Full consultado, mas não utilizado — confiança insuficiente`
- `⚪ Clef Full não usado — <motivo>`
- `🔴 Clef Full falhou — resposta produzida pelo modelo principal`

- `⚡` só depois de `ok: true` do script.
- Após cada `ask`, acrescente: `Tempo: <latencia_ms> ms · Cache de prefixo: <hit|miss>`.
- Falha (🔴): mostre a mensagem curta do script e responda com o modelo principal. Não repita em loop.

## Segurança

- Só `start`/`stop` dos containers `clef-flash` e `clef-full`. Nunca instale pacotes nem rode outros comandos Docker. Nunca peça chaves no chat.
