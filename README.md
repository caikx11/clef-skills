# clef-skills

Duas *skills* de agente (Claude Code e Codex) que usam os modelos de decisão **Clef**, da Cloudflare, rodando **localmente** na sua placa NVIDIA:

- `clef-flash`: versão rápida e leve.
- `clef-full`: versão maior e mais precisa, adaptada aqui para caber em uma placa de 16 GB.

Elas servem para **decisões estruturadas**, em três formatos:

| Tipo | Pergunta | Resposta |
| --- | --- | --- |
| `noul` | sim ou não? | probabilidade de "sim" (0 a 1) |
| `choice` | qual destas opções? | probabilidade de cada opção |
| `score` | quanto, numa escala? | nota e rótulo na sua escala |

> **Regra de ouro: o modelo de decisão decide; o modelo principal escreve.**
> O Clef só classifica e pontua. Texto, código e raciocínio continuam com o Claude/Codex.

O servidor é o portal autohospedado [BlueFinLab-ai/clef-lcv](https://github.com/BlueFinLab-ai/clef-lcv). Este repositório traz o passo a passo, as skills e os patches que fizeram o Full rodar em 16 GB.

## Início rápido

1. Prepare o ambiente (WSL2 + Docker + GPU): [docs/01-ambiente.md](docs/01-ambiente.md).
2. Construa e rode o Flash: [docs/02-flash.md](docs/02-flash.md).
3. (Opcional) Rode o Full em 16 GB com os patches: [docs/03-full-na-ram.md](docs/03-full-na-ram.md).
4. Instale as skills: [docs/04-skills.md](docs/04-skills.md).
5. Use no chat: [docs/05-uso.md](docs/05-uso.md). Por exemplo: `$clef-flash on` e depois `$clef-flash ask`.
6. (Recomendado) Rode o Flash como GGUF no llama.cpp, mais rápido: [docs/06-gguf.md](docs/06-gguf.md).

## Requisitos

- GPU NVIDIA com driver atualizado.
  - **Flash:** a partir de 8 GB de VRAM.
  - **Full:** com o patch deste repositório, rodou numa RTX 5070 Ti de 16 GB com 64 GB de RAM.
- Windows 11 + WSL2 + Docker Desktop, com virtualização ativada na BIOS.
- Python 3 (só biblioteca padrão) para o cliente das skills.
- Espaço em disco: o Full usa cerca de 69 GB (modelo + cache).

## Flash x Full

| | Flash | Full (com o patch) |
| --- | --- | --- |
| VRAM | ~5,5 GB | ~12,7 GB (pico ~14,7 GB com ~10 mil tokens) |
| Latência | ~0,3 s (quente) | ~0,4 s (quente), ~1,1 a 1,5 s (frio) |
| Benchmark (README do projeto original, vs. referência) | 96/100 | 100/100 |

Os dois **não rodam ao mesmo tempo** numa placa de 16 GB: as skills param um para iniciar o outro.

## Conteúdo

- [`docs/`](docs/): guias em português, na ordem de leitura.
- [`skills/clef-flash`](skills/clef-flash) e [`skills/clef-full`](skills/clef-full): as skills (SKILL.md + cliente Python).
- [`tools/clef-gguf.ps1`](tools/clef-gguf.ps1): liga/desliga o Flash GGUF (llama.cpp).
- [`patches/`](patches/): patches `git am` sobre o clef-lcv que habilitam o Full em 16 GB.

## Créditos e licenças

- **clef-lcv** (o servidor): Apache-2.0, de BlueFinLab-ai.
- **Pesos dos modelos Clef:** pertencem à Cloudflare e seguem os termos de liberação dela. **Não estão incluídos** aqui; o container os baixa na primeira execução.
- **Conteúdo deste repositório** (docs, skills, patches próprios): licença [MIT](LICENSE), copyright caikx11. Os patches modificam arquivos do clef-lcv e, nessa parte, seguem a Apache-2.0 dele.
