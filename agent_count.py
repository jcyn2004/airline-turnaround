#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path
import pandas as pd

# Matches:
# "name": "agent"
# "name" = "agent"
# agent: agent,
AGENT_PATTERN = re.compile(
    r'"name"\s*[:=]\s*"([^"]+)"|\bagent\s*:\s*([^,\n]+)',
    re.IGNORECASE
)

def extract_agents_from_text(text: str) -> list[str]:
    agents = []
    for m in AGENT_PATTERN.finditer(text):
        agent = m.group(1) or m.group(2)
        if agent:
            agents.append(agent.strip())

    # de-duplicate while preserving order
    return list(dict.fromkeys(agents))

def main() -> None:
    root = Path.cwd()

    registries_dirs = [p for p in root.rglob("registries") if p.is_dir()]
    hocon_files = []
    for d in registries_dirs:
        hocon_files.extend(d.rglob("*.hocon"))

    rows = []
    for f in sorted(set(hocon_files)):
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            rows.append({
                "hocon_file": str(f.relative_to(root)),
                "agent_name": "",
                "error": f"read_error: {e}",
            })
            continue

        agents = extract_agents_from_text(text)

        for agent in agents:
            rows.append({
                "hocon_file": str(f.relative_to(root)),
                "agent_name": agent,
                "error": "",
            })

    df = pd.DataFrame(rows).sort_values(["hocon_file", "agent_name"]).reset_index(drop=True)

    out_csv = root / "hocon_agents_per_agent.csv"
    df.to_csv(out_csv, index=False)

    print(f"Wrote {len(df)} rows to {out_csv}")
    print(df.head(10).to_string(index=False))

if __name__ == "__main__":
    main()
