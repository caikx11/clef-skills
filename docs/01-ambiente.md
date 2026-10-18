# 1. Preparando o ambiente (Windows 11)

Objetivo: ter o Docker enxergando a sua GPU NVIDIA.

## 1.1 Virtualização na BIOS

O WSL2 precisa de virtualização (Intel VT-x / AMD-V, chamada de "SVM Mode" ou "Virtualization Technology"). Entre na BIOS e ative. Para conferir no Windows: Gerenciador de Tarefas > Desempenho > CPU > "Virtualização: Habilitado".

## 1.2 WSL2

No PowerShell como administrador:

```powershell
wsl --install --no-distribution
```

Reinicie se pedir. O Docker Desktop usa o próprio backend WSL2; você não precisa instalar uma distribuição Linux.

## 1.3 Docker Desktop

Instale o Docker Desktop e, em *Settings > General*, deixe marcado **Use the WSL 2 based engine**. Abra o app e espere o motor ficar "running".

## 1.4 Teste da GPU

```powershell
docker run --rm --gpus all nvidia/cuda:12.9.1-base-ubuntu24.04 nvidia-smi
```

Se aparecer a tabela com o nome da sua placa, está pronto.

## Problemas que encontramos

**"WSL não está instalado" / mensagem sobre virtualização.** O Docker Desktop abriu pedindo WSL, ou o `wsl --install` reclamou de virtualização. Causa: virtualização desligada na BIOS (passo 1.1) ou WSL ainda não instalado (passo 1.2). Ative na BIOS, rode o comando e reinicie.

**`docker` não é reconhecido no terminal.** O Docker Desktop instala o `docker.exe` em `%LOCALAPPDATA%\Programs\DockerDesktop\resources\bin`, que pode não estar no `PATH`. Soluções:

- Abra um terminal novo (o instalador altera o PATH só para novas sessões).
- Ou adicione essa pasta ao PATH.
- Ou chame o caminho completo: `& "$env:LOCALAPPDATA\Programs\DockerDesktop\resources\bin\docker.exe" ps`.

O cliente das skills (`clef_call.py`) já procura o `docker.exe` nesse caminho quando ele não está no PATH.
