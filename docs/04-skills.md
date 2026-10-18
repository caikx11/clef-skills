# 4. As skills: como foram feitas e como instalar

## 4.1 Como foram criadas

O desenho espelha uma skill local de decisão que já existia (o padrão "decisão estruturada local"):

- **Só invocação explícita.** No frontmatter do `SKILL.md`: `disable-model-invocation: true` e `allow_implicit_invocation: false` (e o mesmo em `agents/openai.yaml`, para o Codex). A skill nunca roda por conta própria.
- **Cliente em Python, só biblioteca padrão** (`scripts/clef_call.py`): subcomandos `status`, `start`, `stop`, `ask`.
- **Trava de rede local:** o script recusa qualquer endereço que não seja `127.0.0.1`/`localhost`. Nenhum dado sai do computador e não há chaves de API.
- **Um modelo por vez:** `start` para o outro container antes de iniciar este.

## 4.2 Bugs encontrados e corrigidos

1. **422 na API:** o campo `state` é obrigatório. O cliente agora exige `--state` (ou usa `--context` como `state`).
2. **Escala do score:** a API devolve índice 0..N-1. O cliente converte para a escala definida em `--levels` e devolve `nivel`, `rotulo`, `score` e `score_raw`.
3. **BOM UTF-8:** o PowerShell grava JSON com BOM e o `json.load` falhava. O cliente lê com `utf-8-sig`.

## 4.3 Instalação

Copie as pastas de `skills/` para o diretório de skills da sua ferramenta:

- Codex / compartilhado: `~/.agents/skills`
- Claude Code: `~/.claude/skills`

```powershell
Copy-Item -Recurse skills\clef-flash, skills\clef-full "$HOME\.claude\skills\"
```

No Windows, para manter uma única cópia usada pelas duas ferramentas, crie uma junção:

```powershell
New-Item -ItemType Junction -Path "$HOME\.claude\skills\clef-flash" -Target "$HOME\.agents\skills\clef-flash"
```

Os containers precisam se chamar `clef-flash` (porta 8080) e `clef-full` (porta 8081), como nos guias 2 e 3.

Teste: `python skills/clef-flash/scripts/clef_call.py status`.
