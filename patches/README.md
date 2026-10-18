# Patches sobre o clef-lcv

Quatro patches, em ordem, sobre a branch `main` de [BlueFinLab-ai/clef-lcv](https://github.com/BlueFinLab-ai/clef-lcv):

1. `0001`: `base.lock` com `setuptools==81.0.0` (conflito com torch 2.11).
2. `0002`: Full com baixa VRAM (embeddings na RAM, `CLEF_ALLOW_LOW_VRAM_FULL`, `CLEF_OFFLOAD_EMBEDDINGS`, `Dockerfile.full-offload`).
3. `0003`: documentação no README do clef-lcv.
4. `0004`: normaliza os finais de linha do README para LF.

## Aplicar

Antes de tudo, `git config core.autocrlf false` no clone (veja docs/02-flash.md).

```sh
cd clef-lcv
git checkout -b full-ram-offload main
git am /caminho/para/clef-skills/patches/*.patch
```

A ordem alfabética dos arquivos já é a ordem correta. Se o `git am` falhar: `git am --abort` e confira se está na `main` limpa.
