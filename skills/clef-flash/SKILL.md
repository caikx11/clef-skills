---
name: clef-flash
description: Usa o Clef Flash local (llama.cpp GGUF, 127.0.0.1:8080) para decisões estruturadas choice, score e noul, como alternativa ao laya. Somente invocação explícita pelo usuário - "$clef-flash on", "$clef-flash off", "$clef-flash status", "$clef-flash ask", "$clef-flash start" ou "$clef-flash stop" (ou "/clef-flash ..."). Nunca use por conta própria.
disable-model-invocation: true
allow_implicit_invocation: false
---

# Skill `clef-flash`

Usa só o **Clef Flash** (servidor llama.cpp GGUF Q4_K_M, `127.0.0.1:8080`, modelo da API `clef-flash`; gerenciado por `~/tools/clef-gguf/clef-gguf.ps1`). Regra de ouro: **o Clef decide; o modelo principal escreve.**

- Cliente: `scripts/clef_call.py` (biblioteca padrão do Python 3; no Windows `python` ou `py -3`). Modelo fixo; independe da skill `clef`.
- **Nunca envie dados para outro endereço**; o script recusa hosts não locais (`CLEF_URL` sobrescreve). Sem chaves de API.
- Flash e Full **não rodam juntos** (16 GB de VRAM): iniciar este para o outro container antes.
- Backend: llama.cpp GGUF Q4_K_M (~50 ms por chamada, ~6,7 GB de VRAM, sobe em segundos). O container Docker `clef-flash` fica só de reserva (restart policy `no`); para voltar a ele manualmente: `clef-gguf.ps1 stop` e depois `docker start clef-flash` (readiness em `/readyz`).
- O GGUF expõe `/health` (não há `/readyz`); o script usa `/health` com fallback para `/readyz`.

## Estado (só na conversa atual)

Começa **desativado**. Não grave em arquivo. Nenhum `ask` antes de `$clef-flash on`.

## Comandos

### `$clef-flash on`
1. Rode `python scripts/clef_call.py status`.
2. Se `ok` for `true`: ative. Estado: `⚪ Clef Flash não usado — ativado, nenhuma decisão feita ainda`.
3. Se o servidor GGUF não estiver rodando: **não ative nem inicie**; **pergunte** se pode iniciá-lo (isso para o container do Full, se estiver rodando) e espere o sim. Com o sim, rode `python scripts/clef_call.py start` (espera o `/health`, até 120 s) e ative.
4. Se o `clef-gguf.ps1` não for encontrado, informe e não ative.

### `$clef-flash off`
Desative. Não rode o script. Estado: `⚪ Clef Flash não usado — desativado`.

### `$clef-flash status`
Rode `status`: estado da skill, processo GGUF e `/health`, container do Full. Estado: `⚪ Clef Flash não usado — apenas status consultado`.

### `$clef-flash start` / `$clef-flash stop`
Só quando o usuário digitar o comando. `python scripts/clef_call.py start` para o container do Full (e o Docker Flash, se estiver de pé), roda `clef-gguf.ps1 start` e espera o `/health`. `stop` roda `clef-gguf.ps1 stop` (só este). Nunca por conta própria.

### `$clef-flash ask`
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
Se `confidence` < 0,6, sugira repetir a pergunta com `$clef-full` (o usuário decide; esta skill não troca de modelo).

## Estado final (obrigatório)

Toda resposta termina com **exatamente um**:

- `⚡ Clef Flash usado — tipos: <choice/score/noul>`
- `🟡 Clef Flash consultado, mas não utilizado — confiança insuficiente`
- `⚪ Clef Flash não usado — <motivo>`
- `🔴 Clef Flash falhou — resposta produzida pelo modelo principal`

- `⚡` só depois de `ok: true` do script.
- Após cada `ask`, acrescente: `Tempo: <latencia_ms> ms · Cache de prefixo: <hit|miss>`.
- Falha (🔴): mostre a mensagem curta do script e responda com o modelo principal. Não repita em loop.

## Segurança

- Só `start`/`stop` do `clef-gguf.ps1` e dos containers `clef-flash` e `clef-full`. Nunca instale pacotes nem rode outros comandos Docker. Nunca peça chaves no chat.
