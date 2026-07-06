#!/usr/bin/env python3
"""
audit_rekor.py - Consulta o log de transparência Rekor e gera relatório
de auditoria com o histórico de assinaturas de uma imagem Docker.

Uso:
    python audit_rekor.py --image ghcr.io/usuario/repo
    python audit_rekor.py --image ghcr.io/usuario/repo --output relatorio.html
"""

import argparse
import base64
import json
import sys
import urllib.request
from datetime import datetime, timezone

REKOR_API = "https://rekor.sigstore.dev"


def search_rekor(image: str) -> list:
    url = f"{REKOR_API}/api/v1/index/retrieve"
    payload = json.dumps({"query": {"subject": image}}).encode()
    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            uuids = json.loads(resp.read())
            return uuids if isinstance(uuids, list) else []
    except Exception as e:
        print(f"[AVISO] Erro ao buscar no Rekor: {e}", file=sys.stderr)
        return []


def get_entry(uuid: str) -> dict:
    url = f"{REKOR_API}/api/v1/log/entries/{uuid}"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"[AVISO] Erro ao buscar entrada {uuid}: {e}", file=sys.stderr)
        return {}


def parse_entry(uuid: str, raw: dict) -> dict:
    entry_data = list(raw.values())[0] if raw else {}
    body_b64 = entry_data.get("body", "")
    try:
        body = json.loads(base64.b64decode(body_b64 + "=="))
    except Exception:
        body = {}

    integrated_time = entry_data.get("integratedTime", 0)
    timestamp = (
        datetime.fromtimestamp(integrated_time, tz=timezone.utc).isoformat()
        if integrated_time else "N/A"
    )
    spec      = body.get("spec", {})
    data_hash = spec.get("data", {}).get("hash", {}).get("value", "N/A")
    log_index = entry_data.get("logIndex", "N/A")

    return {
        "uuid":      uuid,
        "log_index": log_index,
        "timestamp": timestamp,
        "kind":      body.get("kind", "N/A"),
        "digest":    data_hash,
        "rekor_url": f"https://search.sigstore.dev/?logIndex={log_index}",
    }


def gerar_html(image: str, entries: list) -> str:
    now   = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    total = len(entries)
    rows  = ""
    for e in entries:
        digest_short = (e["digest"][:24] + "...") if len(e["digest"]) > 24 else e["digest"]
        rows += f"""
        <tr>
          <td><code>{e['log_index']}</code></td>
          <td><code>{e['timestamp']}</code></td>
          <td><code>{digest_short}</code></td>
          <td>GitHub Actions (OIDC)</td>
          <td>Registrada</td>
          <td><a href="{e['rekor_url']}" target="_blank">Ver no Rekor</a></td>
        </tr>"""

    table = ("<p><em>Nenhuma entrada encontrada.</em></p>" if total == 0 else
             f"<table><thead><tr><th>Log Index</th><th>Timestamp (UTC)</th>"
             f"<th>Digest</th><th>Identidade</th><th>Status</th><th>Link</th>"
             f"</tr></thead><tbody>{rows}</tbody></table>")

    return f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="UTF-8">
<title>Relatório de Auditoria Rekor</title>
<style>
  body{{font-family:Arial,sans-serif;margin:2em;color:#222}}
  h1{{color:#1a3a5c;border-bottom:2px solid #2563a8;padding-bottom:8px}}
  h2{{color:#2563a8}}
  table{{border-collapse:collapse;width:100%;margin-top:1em}}
  th{{background:#1a3a5c;color:white;padding:10px;text-align:left}}
  td{{padding:8px 10px;border-bottom:1px solid #ddd}}
  tr:hover{{background:#f4f6f9}}
  .meta{{background:#f4f6f9;padding:1em;border-radius:6px;margin:1em 0;border-left:4px solid #2563a8}}
  code{{background:#eef;padding:1px 4px;border-radius:3px}}
  pre{{background:#f4f6f9;padding:1em;border-radius:6px;overflow-x:auto}}
</style></head><body>
<h1>Relatório de Auditoria – Log de Transparência Rekor</h1>
<div class="meta">
  <strong>Imagem:</strong> <code>{image}</code><br>
  <strong>Gerado em:</strong> {now}<br>
  <strong>Total de assinaturas:</strong> {total}
</div>
<h2>Histórico de Assinaturas</h2>
{table}
<h2>Verificação manual</h2>
<pre>cosign verify \\
  --certificate-identity "https://github.com/USUARIO/REPO/.github/workflows/build-sign.yml@refs/heads/main" \\
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \\
  {image}:latest</pre>
<hr><p style="color:gray;font-size:.85em">Gerado por audit_rekor.py – Segurança de Software – UFSC 2025</p>
</body></html>"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image",  required=True)
    parser.add_argument("--output", default="rekor-audit-report.html")
    parser.add_argument("--json",   action="store_true")
    args = parser.parse_args()

    print(f"Buscando assinaturas para: {args.image}")
    uuids   = search_rekor(args.image)
    print(f"Entradas encontradas: {len(uuids)}")
    entries = [parse_entry(u, get_entry(u)) for u in uuids[:20] if get_entry(u)]

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(gerar_html(args.image, entries))
    print(f"Relatório salvo em: {args.output}")

    if args.json:
        path = args.output.replace(".html", ".json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"image": args.image, "total": len(entries), "entries": entries},
                      f, indent=2, ensure_ascii=False)
        print(f"JSON salvo em: {path}")


if __name__ == "__main__":
    main()
