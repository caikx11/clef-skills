# 2. Construindo e rodando o Clef Flash

## 2.1 Clonar sem quebrar o hash (CRLF)

No Windows o Git pode converter finais de linha para CRLF. O projeto confere o hash de `vendor/cloudflare/joint_schema_model.py`; com CRLF o hash muda e o build falha com:

```
Downloaded decision wrapper differs from the saved pinned source
```

Por isso desligue a conversão **antes** do checkout:

```powershell
git clone --no-checkout https://github.com/BlueFinLab-ai/clef-lcv.git
cd clef-lcv
git config core.autocrlf false
git checkout main
```

Se já clonou com CRLF: apague a pasta e clone de novo com o `autocrlf false`.

## 2.2 Corrigir o pin do setuptools

`requirements/base.lock` fixa `setuptools==84.0.0`, mas o `torch 2.11.0+cu128` exige `setuptools<82`. O build dá conflito de dependências. A correção é trocar para `81.0.0` (é o primeiro patch em [`patches/`](../patches/)):

```
setuptools==81.0.0
```

## 2.3 Build

```powershell
docker build -t clef:local .
```

Demora: baixa as dependências do PyTorch.

## 2.4 Rodar (somente local)

```powershell
docker run -d --name clef-flash --gpus device=0 `
  -p 127.0.0.1:8080:8080 -v clef-cache:/data clef:local
docker logs -f clef-flash
```

- `127.0.0.1:8080` limita o acesso à sua máquina.
- O volume `clef-cache` guarda o modelo baixado (~18 GB) e os pesos preparados, para os próximos starts serem rápidos.
- O nome `clef-flash` é o que a skill espera.

Verifique:

```powershell
curl http://127.0.0.1:8080/readyz
```

## 2.5 Primeira chamada

```powershell
curl -X POST http://127.0.0.1:8080/v1/systemone -H "Content-Type: application/json" -d '{
  "model": "clef-flash",
  "state": "O servidor de pagamentos está fora do ar desde as 14h.",
  "questions": {"urgente": {"type": "noul", "instructions": "O texto descreve algo urgente?"}},
  "image_pooling": false
}'
```

Atenção: o campo `state` é obrigatório (sem ele a API devolve 422).

## 2.6 Resultados medidos (RTX 5070 Ti, 16 GB)

| Medida | Valor |
| --- | --- |
| Primeira requisição com contexto novo | ~11 s |
| Requisição repetida (cache de prefixo) | ~0,3 s |
| VRAM | ~5,5 GB |
