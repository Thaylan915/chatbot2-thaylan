"""Lista issues do SonarCloud para o projeto Pedro-Iglesias_chatbot2.

Uso:
    $env:SONAR_TOKEN = "<seu_token>"   # gere em https://sonarcloud.io/account/security
    python scripts/sonar_issues.py
    python scripts/sonar_issues.py --severity CRITICAL,BLOCKER
    python scripts/sonar_issues.py --type BUG --status OPEN
    python scripts/sonar_issues.py --json > issues.json
"""

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from base64 import b64encode

ORGANIZATION = "pedro-iglesias"
PROJECT_KEY = "Pedro-Iglesias_chatbot2"
BASE_URL = "https://sonarcloud.io/api/issues/search"
PAGE_SIZE = 100


def fetch_issues(token, severities=None, types=None, statuses=None):
    issues = []
    page = 1
    while True:
        params = {
            "organization": ORGANIZATION,
            "componentKeys": PROJECT_KEY,
            "ps": PAGE_SIZE,
            "p": page,
        }
        if severities:
            params["severities"] = severities
        if types:
            params["types"] = types
        if statuses:
            params["statuses"] = statuses

        url = f"{BASE_URL}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url)
        auth = b64encode(f"{token}:".encode()).decode()
        req.add_header("Authorization", f"Basic {auth}")

        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())

        batch = data.get("issues", [])
        issues.extend(batch)
        total = data.get("total", 0)
        if page * PAGE_SIZE >= total or not batch:
            break
        page += 1

    return issues


SEVERITY_ORDER = {"BLOCKER": 0, "CRITICAL": 1, "MAJOR": 2, "MINOR": 3, "INFO": 4}


def print_issues(issues):
    if not issues:
        print("Nenhuma issue encontrada.")
        return

    issues.sort(key=lambda i: (SEVERITY_ORDER.get(i.get("severity", ""), 99), i.get("component", "")))

    by_sev = {}
    for i in issues:
        by_sev.setdefault(i.get("severity", "?"), 0)
        by_sev[i.get("severity", "?")] += 1

    print(f"\nTotal: {len(issues)} issues")
    print("Por severidade:", ", ".join(f"{k}={v}" for k, v in sorted(by_sev.items(), key=lambda x: SEVERITY_ORDER.get(x[0], 99))))
    print("-" * 80)

    for i in issues:
        component = i.get("component", "").replace(f"{PROJECT_KEY}:", "")
        line = i.get("line", "?")
        severity = i.get("severity", "?")
        itype = i.get("type", "?")
        rule = i.get("rule", "?")
        message = i.get("message", "")
        status = i.get("status", "?")
        print(f"[{severity:<8}] [{itype:<11}] {component}:{line}")
        print(f"           rule: {rule}  status: {status}")
        print(f"           {message}")
        print()


def main():
    parser = argparse.ArgumentParser(description="Lista issues do SonarCloud.")
    parser.add_argument("--severity", help="Filtrar por severidade (BLOCKER,CRITICAL,MAJOR,MINOR,INFO)")
    parser.add_argument("--type", help="Filtrar por tipo (BUG,VULNERABILITY,CODE_SMELL)")
    parser.add_argument("--status", help="Filtrar por status (OPEN,CONFIRMED,REOPENED,RESOLVED,CLOSED)", default="OPEN,CONFIRMED,REOPENED")
    parser.add_argument("--json", action="store_true", help="Saida em JSON bruto")
    args = parser.parse_args()

    token = os.environ.get("SONAR_TOKEN")
    if not token:
        print("ERRO: defina a variavel de ambiente SONAR_TOKEN.", file=sys.stderr)
        print('  PowerShell:  $env:SONAR_TOKEN = "seu_token"', file=sys.stderr)
        sys.exit(1)

    try:
        issues = fetch_issues(token, args.severity, args.type, args.status)
    except urllib.error.HTTPError as e:
        print(f"ERRO HTTP {e.code}: {e.reason}", file=sys.stderr)
        print(e.read().decode(errors="ignore"), file=sys.stderr)
        sys.exit(2)

    if args.json:
        json.dump(issues, sys.stdout, indent=2, ensure_ascii=False)
    else:
        print_issues(issues)


if __name__ == "__main__":
    main()
