#!/usr/bin/env python3
"""Cliente do Clef Flash local (GGUF/llama.cpp) (somente biblioteca padrao). Subcomandos: status, ask, start, stop."""
import argparse, json, os, shutil, subprocess, sys, tempfile, time, urllib.request, urllib.error
from urllib.parse import urlparse

# Flash e Full nao cabem juntos nos 16 GB de VRAM: so um roda por vez.
# Backend do Flash: servidor llama.cpp GGUF Q4_K_M (clef-gguf.ps1), porta 8080. O container Docker clef-flash fica de reserva.
MODELS = {
    "flash": {"container": "clef-flash", "url": "http://127.0.0.1:8080", "api": "clef-flash"},
    "full": {"container": "clef-full", "url": "http://127.0.0.1:8081", "api": "clef"},
}
ENV_URL = os.environ.get("CLEF_URL", "").rstrip("/")
OWN = "flash"
OTHER = "full"
URL = ENV_URL or MODELS[OWN]["url"]
GGUF_PS1 = os.path.join(os.environ.get("USERPROFILE", os.path.expanduser("~")), "tools", "clef-gguf", "clef-gguf.ps1")
DOCKER_FALLBACK = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "DockerDesktop", "resources", "bin", "docker.exe")


def out(obj, code=0):
    print(json.dumps(obj, ensure_ascii=False, separators=(",", ":")))
    sys.exit(code)


def check_url(url=None):
    url = url or URL
    host = urlparse(url).hostname
    if host not in ("127.0.0.1", "localhost", "::1"):
        out({"ok": False, "erro": "CLEF_URL deve apontar para 127.0.0.1/localhost: " + url}, 2)


def docker_bin():
    return shutil.which("docker") or (DOCKER_FALLBACK if os.path.exists(DOCKER_FALLBACK) else None)


def docker(*args):
    d = docker_bin()
    if not d:
        return None, "docker nao encontrado"
    try:
        r = subprocess.run([d, *args], capture_output=True, text=True, timeout=60)
        return r.stdout.strip(), (r.stderr.strip() if r.returncode else "")
    except Exception as e:
        return None, str(e)


def http(path, payload=None, timeout=120, base=None):
    req = urllib.request.Request((base or URL) + path, method="POST" if payload is not None else "GET")
    data = None
    if payload is not None:
        data = json.dumps(payload).encode()
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, data=data, timeout=timeout) as r:
        return json.loads(r.read().decode())


def murl(m):
    return ENV_URL or MODELS[m]["url"]


def cstate(m):
    st, _ = docker("inspect", "-f", "{{.State.Status}}", MODELS[m]["container"])
    return st or "desconhecido"


def ready(m, timeout=5):
    # Flash (GGUF/llama.cpp) expoe /health; Full (Docker) expoe /readyz. Fallback cruzado.
    paths = ("/health", "/readyz") if m == OWN else ("/readyz", "/health")
    for p in paths:
        try:
            r = http(p, timeout=timeout, base=murl(m))
            if r.get("status") == "ok":
                return True
        except Exception:
            pass
    return False


def gguf(action):
    """Executa clef-gguf.ps1 e devolve (json|None, erro)."""
    if not os.path.exists(GGUF_PS1):
        return None, "clef-gguf.ps1 nao encontrado: " + GGUF_PS1
    try:
        # Saida em arquivo (nao pipe): o llama-server em background herda o handle e um pipe nunca fecharia.
        with tempfile.TemporaryFile("w+", encoding="utf-8", errors="replace") as fo:
            r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", GGUF_PS1, action],
                               stdin=subprocess.DEVNULL, stdout=fo, stderr=subprocess.STDOUT, timeout=180)
            fo.seek(0)
            txt = fo.read().strip()
    except Exception as e:
        return None, str(e)
    try:
        return json.loads(txt.splitlines()[-1]), ""
    except Exception:
        return None, (txt or "saida invalida de clef-gguf.ps1")[:300]


def gguf_state():
    j, _ = gguf("status")
    return "running" if j and j.get("alive") else "stopped"


def active():
    if gguf_state() == "running":
        return OWN
    if cstate(OTHER) == "running":
        return OTHER
    return None


def resolve(a):
    return a.model


def cmd_status(a):
    res = {"modelos": {}, "ativo": None}
    g = gguf_state()
    info = {"backend": "gguf-llama.cpp", "processo": g, "url": murl(OWN)}
    if g == "running":
        info["health"] = "ok" if ready(OWN, min(a.timeout, 10)) else "indisponivel"
        res["ativo"] = OWN
    res["modelos"][OWN] = info
    c = cstate(OTHER)
    info2 = {"container": c, "url": murl(OTHER)}
    if c == "running":
        info2["readyz"] = "ok" if ready(OTHER, min(a.timeout, 10)) else "indisponivel"
        res["ativo"] = res["ativo"] or OTHER
    res["modelos"][OTHER] = info2
    res["docker_flash_reserva"] = cstate_name("clef-flash")
    res["ok"] = info.get("health") == "ok"
    out(res)


def cstate_name(name):
    st, _ = docker("inspect", "-f", "{{.State.Status}}", name)
    return st or "desconhecido"


def cmd_ctl(a):
    m = OWN
    if a.cmd == "start":
        if cstate(OTHER) == "running":
            _, err = docker("stop", MODELS[OTHER]["container"])
            if err:
                out({"ok": False, "erro": "falha ao parar %s: %s" % (OTHER, err)}, 1)
        if cstate_name("clef-flash") == "running":
            _, err = docker("stop", "clef-flash")
            if err:
                out({"ok": False, "erro": "falha ao parar container clef-flash: " + err}, 1)
        t0 = time.time()
        j, err = gguf("start")
        if not j or not j.get("ok"):
            out({"ok": False, "erro": (j or {}).get("erro") or err}, 1)
        while time.time() - t0 < 120:
            if ready(m, 5):
                out({"ok": True, "ativo": m, "backend": "gguf", "pronto_em_s": round(time.time() - t0, 1)})
            time.sleep(1)
        out({"ok": False, "erro": "timeout (120 s) esperando /health de " + m}, 1)
    j, err = gguf("stop")
    out({"ok": bool(j and j.get("ok")), "modelo": m, "gguf": j, "erro": err or None})


def build_payload(a):
    if a.json:
        if a.json == "-":
            p = json.loads(sys.stdin.read().lstrip("﻿"))
        else:
            with open(a.json, encoding="utf-8-sig") as f:
                p = json.load(f)
        p.setdefault("model", MODELS[a._m]["api"])
        return p
    q = {}
    if a.noul:
        q["noul"] = {"type": "noul", "instructions": a.noul}
    if a.choice:
        if not a.options:
            out({"ok": False, "erro": "--choice exige --options a,b,c"}, 2)
        q["choice"] = {"type": "choice", "instructions": a.choice,
                       "criteria": {o.strip(): o.strip() for o in a.options.split(",")}}
    if a.score:
        if not a.levels:
            out({"ok": False, "erro": "--score exige --levels '1:desc,2:desc'"}, 2)
        labels = []
        for i, x in enumerate(a.levels.split(",")):
            num, sep, desc = x.partition(":")
            try:
                n = int(num.strip()) if sep else i
            except ValueError:
                n, desc, sep = i, x, ":"
            labels.append((n, (desc if sep else x).strip()))
        a._levels = labels
        q["score"] = {"type": "score", "instructions": a.score,
                      "criteria": [d for _, d in labels]}
    if not q:
        out({"ok": False, "erro": "informe --json ou --noul/--choice/--score"}, 2)
    p = {"model": MODELS[a._m]["api"], "questions": q, "image_pooling": False}
    # A API exige "state". --state e o texto principal; so com --context, ele vira o state.
    if a.state:
        p["state"] = a.state
        if a.context:
            p["context"] = a.context
    elif a.context:
        p["state"] = a.context
    else:
        out({"ok": False, "erro": "informe --state (texto a avaliar)"}, 2)
    return p


def map_score(ans, levels):
    """Converte o score do indice 0..N-1 da API para a escala do usuario."""
    if not isinstance(ans, dict) or not levels:
        return ans
    raw = ans.get("score")
    if not isinstance(raw, (int, float)):
        return ans
    nums = [n for n, _ in levels]
    last = len(levels) - 1
    k = min(max(int(round(raw)), 0), last)
    lo, hi = nums[0], nums[-1]
    ans = dict(ans)
    ans["score_raw"] = raw
    ans["nivel"] = nums[k]
    ans["rotulo"] = levels[k][1]
    ans["score"] = round(lo + (raw / last) * (hi - lo), 4) if last else lo
    return ans


def cmd_ask(a):
    a._m = resolve(a)
    payload = build_payload(a)
    t0 = time.time()
    try:
        r = http("/v1/systemone", payload, a.timeout, base=murl(a._m))
    except urllib.error.HTTPError as e:
        out({"ok": False, "erro": "HTTP %s: %s" % (e.code, e.read().decode()[:300])}, 1)
    except Exception as e:
        out({"ok": False, "erro": str(e)}, 1)
    u = r.get("usage", {})
    ans = r.get("answers")
    lv = getattr(a, "_levels", None)
    if lv and isinstance(ans, dict) and "score" in ans:
        ans["score"] = map_score(ans["score"], lv)
    out({"ok": True, "modelo": a._m, "respostas": ans,
         "latencia_ms": u.get("latency_ms") if u.get("latency_ms") is not None else round((time.time() - t0) * 1000), "prefix_cache": u.get("prefix_cache")})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout", type=float, default=120)
    ap.add_argument("--model", choices=[OWN], default=OWN)
    sub = ap.add_subparsers(dest="c", required=True)
    sub.add_parser("status").set_defaults(f=cmd_status)
    for n in ("start", "stop"):
        sub.add_parser(n).set_defaults(f=cmd_ctl, cmd=n)
    s = sub.add_parser("ask")
    s.add_argument("--json", help="arquivo com o payload completo, ou - para stdin")
    s.add_argument("--context")
    s.add_argument("--state")
    s.add_argument("--noul")
    s.add_argument("--choice")
    s.add_argument("--options")
    s.add_argument("--score")
    s.add_argument("--levels")
    s.set_defaults(f=cmd_ask)
    a = ap.parse_args()
    check_url(murl(OWN))
    a.f(a)


if __name__ == "__main__":
    main()
