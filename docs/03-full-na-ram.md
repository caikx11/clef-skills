# 3. Clef Full em placa de 16 GB (embeddings na RAM)

O Full original exige **22 GiB de VRAM**. Aqui ele rodou numa placa de 16 GB mantendo parte do modelo na RAM do computador. Isto é experimental.

## 3.1 O problema

O Full (27B parâmetros) é quantizado em NF4, mas duas tabelas ficam densas em BF16: `embed_tokens` e `lm_head`, juntas ~4,7 GiB. O projeto original não tem offload de pesos e assume uma única GPU com pelo menos 22 GiB.

## 3.2 Análise

- Boa parte do peso extra vem dessas duas tabelas.
- Elas são acessadas só por **linhas** (buscar o vetor de um token), então não precisam estar na GPU.
- Estratégia mínima, "etapa 1": tirar só essas tabelas da VRAM, sem mexer no resto.

## 3.3 A solução

Os patches em [`patches/`](../patches/) adicionam:

- `runtime/cpu_embeddings.py`: troca `embed_tokens` e `lm_head` por consultas de linhas feitas na CPU/RAM.
- Duas variáveis de ambiente opt-in:
  - `CLEF_ALLOW_LOW_VRAM_FULL=1`: libera o piso de 22 GiB.
  - `CLEF_OFFLOAD_EMBEDDINGS=1`: carrega o Full na CPU, substitui as tabelas e só então move o restante para a GPU.
- `CLEF_MAX_LENGTH=8192`: limita o tamanho da entrada.
- `Dockerfile.full-offload`: camada extra por cima da imagem `clef:local`.

O arquivo do fornecedor (`vendor/cloudflare/joint_schema_model.py`) **não foi alterado**, então a checagem de hash continua valendo.

## 3.4 Aplicar e construir

```powershell
cd clef-lcv
git checkout -b full-ram-offload main
git am ..\clef-skills\patches\*.patch      # ver patches/README.md
docker build -t clef:local .
docker build -f Dockerfile.full-offload -t clef:full-offload .
```

## 3.5 Rodar

Pare o Flash antes (`docker stop clef-flash`):

```powershell
docker run -d --name clef-full --gpus device=0 `
  -p 127.0.0.1:8081:8080 -v clef-cache-full:/data `
  -e CLEF_MAX_LENGTH=8192 clef:full-offload --full
docker logs -f clef-full
```

Porta 8081, volume `clef-cache-full`. Primeiro start: download do modelo, ~22 minutos. Disco total: ~69 GB.

## 3.6 Resultados

Mesmas perguntas, Flash x Full:

| Medida | Flash | Full |
| --- | --- | --- |
| "urgente" (noul) | 0,9427 | 0,9842 |
| Categoria "outage" (choice) | 0,9643 | 0,9825 |
| Severidade (score) | 1,9073 | 1,9642 |

Recursos e tempo (Full):

| Medida | Valor |
| --- | --- |
| VRAM, entrada curta | pico ~12,7 GB |
| VRAM, ~9,7 mil tokens | ~14,7 GB |
| Latência | ~1,1 a 1,5 s frio, ~0,4 s quente |
| Prompt longo | 87,7 s frio, 2,1 s com cache |

## 3.7 Riscos e limitações

- **Margem de VRAM pequena:** com menos de ~14 GB livres, entradas longas podem dar falta de memória. Feche outros programas que usam a GPU.
- `CLEF_MAX_LENGTH` pode exigir também `CLEF_CONTEXT_LIMIT_MODE=fixed` (a confirmar).
- **Imagens não foram testadas.**
- Não foi comparado com um Full "de verdade" numa placa de 24 GB.
- Prompts longos e frios são lentos.
