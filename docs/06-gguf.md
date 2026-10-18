# 06 - Flash em GGUF (llama.cpp)

O Flash agora roda de preferência como **GGUF Q4_K_M no llama.cpp**, direto no Windows, na porta 8080. O container Docker do Flash continua válido como reserva.

## Por que

Avaliação em 32 itens (mesmo conjunto para todos):

| Backend | Acurácia | ECE | Brier | Latência média |
| --- | --- | --- | --- | --- |
| Flash (Docker) | 0,906 | 0,1007 | 0,0621 | 354 ms |
| Full (Docker) | 0,9375 | 0,0772 | 0,0355 | 567 ms |
| Flash GGUF Q4_K_M | 0,906 | 0,0996 | 0,0631 | 54 ms |
| Flash GGUF Q8_0 | 0,906 | 0,0957 | 0,0588 | 50 ms |

- A qualidade do GGUF Q4 é praticamente igual à do Flash em Docker, com latência cerca de 6 vezes menor e subida em ~10 s.
- Q8_0 quase não ganha sobre Q4_K_M (e ocupa mais VRAM), por isso o padrão é Q4_K_M (~6,7 GB de VRAM).
- Ressalva: 32 itens é um conjunto pequeno; diferenças de 1 a 2 itens não são significativas.

## Ambiente testado

- llama.cpp **b11718**, build CUDA 13.4 (+ pacote cudart). GPU Blackwell (sm_120, RTX 5070 Ti) funciona.
- Modelo: `ggml-org/Clef-Flash-GGUF`, arquivo `Clef-Flash-Q4_K_M.gguf`. O servidor carrega sozinho um `mmproj` de visão (`mmproj-Clef-Flash-Q8_0.gguf`).
- A API é a mesma (`POST /v1/systemone`, modelo `clef-flash`). A diferença é o health check: o GGUF expõe **`/health`** (não existe `/readyz`, que é do portal Docker).

## Instalação

1. Baixe o llama.cpp (zip CUDA + cudart) para `~/tools/clef-gguf/`.
2. Baixe o modelo uma vez, com cache local:
   `LLAMA_CACHE=~/tools/clef-gguf/cache llama-server -hf ggml-org/Clef-Flash-GGUF:Q4_K_M --port 8090` (feche depois de carregar).
3. Copie [`tools/clef-gguf.ps1`](../tools/clef-gguf.ps1) para `~/tools/clef-gguf/` (ajuste os nomes dos arquivos no topo se mudar a versão).

O script usa o modelo e o `mmproj` do cache (`-m` e `--mmproj`), sem rede na subida.

## Uso

```
powershell -File clef-gguf.ps1 start    # recusa se clef-full/clef-flash (Docker) ou outro processo ocupar a 8080
powershell -File clef-gguf.ps1 status   # PID vivo + /health
powershell -File clef-gguf.ps1 stop     # confere que o PID é llama-server antes de encerrar
```

`start` roda `llama-server` oculto (`--host 127.0.0.1 --port 8080 --alias clef-flash -ngl 99`), grava `server.pid` e `logs/`, e espera o `/health` por até 120 s.

As skills usam esse script: `clef-flash start` sobe o GGUF e `clef-full start` o encerra antes de subir o Full.

## Voltar ao Docker

```
powershell -File clef-gguf.ps1 stop
docker start clef-flash
```

Dica: `docker update --restart=no clef-flash clef-full` evita que um container tome a 8080 no boot.
