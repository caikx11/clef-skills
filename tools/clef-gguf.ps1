# Clef Flash GGUF (llama.cpp) na porta 8080. Uso: clef-gguf.ps1 start|stop|status
param([Parameter(Mandatory = $true)][ValidateSet('start', 'stop', 'status')][string]$Action)

$ErrorActionPreference = 'Stop'
$Root = $PSScriptRoot
$Port = 8080
$Base = "http://127.0.0.1:$Port"
$Server = Join-Path $Root 'llama-b11718-cuda13.4\llama-server.exe'
$Snap = Get-ChildItem (Join-Path $Root 'cache\models--ggml-org--Clef-Flash-GGUF\snapshots') -Directory | Select-Object -First 1
$Model = Join-Path $Snap.FullName 'Clef-Flash-Q4_K_M.gguf'
$Mmproj = Join-Path $Snap.FullName 'mmproj-Clef-Flash-Q8_0.gguf'
$LogDir = Join-Path $Root 'logs'
$Log = Join-Path $LogDir 'server.log'
$PidFile = Join-Path $Root 'server.pid'
$Docker = Join-Path $env:LOCALAPPDATA 'Programs\DockerDesktop\resources\bin\docker.exe'

function Get-GgufProc {
    if (-not (Test-Path $PidFile)) { return $null }
    $id = [int](Get-Content $PidFile -Raw).Trim()
    $p = Get-Process -Id $id -ErrorAction SilentlyContinue
    if ($p -and $p.ProcessName -eq 'llama-server') { return $p }
    return $null
}

function Test-Health {
    try { return (Invoke-RestMethod "$Base/health" -TimeoutSec 3).status -eq 'ok' } catch { return $false }
}

function Get-PortOwner {
    Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
}

switch ($Action) {
    'status' {
        $p = Get-GgufProc
        $h = Test-Health
        [pscustomobject]@{ ok = [bool]($p -and $h); pid = $(if ($p) { $p.Id } else { $null }); alive = [bool]$p; health = $h; url = $Base } | ConvertTo-Json -Compress
        if (-not ($p -and $h)) { exit 1 }
    }
    'stop' {
        $p = Get-GgufProc
        if (-not $p) {
            Remove-Item $PidFile -ErrorAction SilentlyContinue
            '{"ok":true,"parado":false,"motivo":"nenhum llama-server do PID file em execucao"}'
            exit 0
        }
        Stop-Process -Id $p.Id -Force
        $p.WaitForExit(15000) | Out-Null
        Remove-Item $PidFile -ErrorAction SilentlyContinue
        "{`"ok`":true,`"parado`":true,`"pid`":$($p.Id)}"
    }
    'start' {
        if (Get-GgufProc) { '{"ok":true,"ja_rodando":true}'; exit 0 }
        if (Test-Path $Docker) {
            $c = & $Docker ps --filter 'name=^clef-full$' --filter 'status=running' --format '{{.Names}}' 2>$null
            if ($c) { '{"ok":false,"erro":"container clef-full em execucao; pare-o antes (docker stop clef-full)"}'; exit 1 }
            $c = & $Docker ps --filter 'name=^clef-flash$' --filter 'status=running' --format '{{.Names}}' 2>$null
            if ($c) { '{"ok":false,"erro":"container clef-flash (Docker) em execucao; pare-o antes (docker stop clef-flash)"}'; exit 1 }
        }
        $o = Get-PortOwner
        if ($o) {
            $n = (Get-Process -Id $o.OwningProcess -ErrorAction SilentlyContinue).ProcessName
            "{`"ok`":false,`"erro`":`"porta $Port ocupada por PID $($o.OwningProcess) ($n)`"}"
            exit 1
        }
        foreach ($f in @($Server, $Model, $Mmproj)) { if (-not (Test-Path $f)) { "{`"ok`":false,`"erro`":`"arquivo ausente: $f`"}"; exit 1 } }
        New-Item -ItemType Directory $LogDir -Force | Out-Null
        $srvArgs = @('-m', $Model, '--mmproj', $Mmproj, '--host', '127.0.0.1', '--port', "$Port", '--alias', 'clef-flash', '-ngl', '99')
        $t0 = Get-Date
        $p = Start-Process -FilePath $Server -ArgumentList $srvArgs -WindowStyle Hidden -PassThru `
            -RedirectStandardOutput $Log -RedirectStandardError (Join-Path $LogDir 'server.err.log')
        Set-Content $PidFile $p.Id
        while (((Get-Date) - $t0).TotalSeconds -lt 120) {
            if ($p.HasExited) { Remove-Item $PidFile -ErrorAction SilentlyContinue; "{`"ok`":false,`"erro`":`"llama-server saiu (codigo $($p.ExitCode)); veja $LogDir`"}"; exit 1 }
            if (Test-Health) {
                "{`"ok`":true,`"pid`":$($p.Id),`"pronto_em_s`":$([math]::Round(((Get-Date) - $t0).TotalSeconds, 1))}"
                exit 0
            }
            Start-Sleep -Milliseconds 500
        }
        Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
        Remove-Item $PidFile -ErrorAction SilentlyContinue
        '{"ok":false,"erro":"timeout (120 s) esperando /health"}'
        exit 1
    }
}
