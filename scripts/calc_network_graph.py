#!/usr/bin/env python3
"""
Derive NETWORK_GRAPH + ECOSYSTEM_NETWORK edges from the COMPANIES array.

Edges are generated from:
  * `competitors` field (undirected competes-with edges)
  * `founder` field clustering (founder-alumni co-affiliation edges)
  * shared `thesisCluster` (same-thesis edges)

Outputs:
  data/network_graph_auto.json   — {nodes: [...], edges: [...]}

Part of Round 7l.
"""

import json
import re
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_JS = Path(__file__).resolve().parent.parent / "data.js"
OUT_PATH = DATA_DIR / "network_graph_auto.json"


def parse_companies():
    text = DATA_JS.read_text()
    start = text.find("const COMPANIES = [")
    i = text.find("[", start)
    depth = 0; in_str = False; sc = None; esc = False; end = None
    for k in range(i, len(text)):
        c = text[k]
        if esc: esc = False; continue
        if c == "\\" and in_str: esc = True; continue
        if in_str:
            if c == sc: in_str = False
            continue
        if c in "\"'": in_str = True; sc = c; continue
        if c == "[": depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0: end = k; break
    block = text[i+1:end]
    entries = []
    idx = 0; n = len(block); d = 0; in_str = False; sc = None; esc = False
    while idx < n:
        while idx < n and block[idx] in " \t\n,": idx += 1
        if idx >= n: break
        if block[idx] != "{": idx += 1; continue
        s = idx
        while idx < n:
            c = block[idx]
            if esc: esc = False; idx += 1; continue
            if c == "\\" and in_str: esc = True; idx += 1; continue
            if in_str:
                if c == sc: in_str = False
                idx += 1; continue
            if c in "\"'": in_str = True; sc = c; idx += 1; continue
            if c == "{": d += 1
            elif c == "}":
                d -= 1
                if d == 0: idx += 1; entries.append(block[s:idx]); break
            idx += 1

    out = []
    for e in entries:
        def gs(f):
            m = re.search(rf"\b{f}:\s*\"((?:[^\"\\]|\\.)*)\"", e)
            return m.group(1) if m else ""
        comps = []
        mc = re.search(r"competitors:\s*\[([^\]]*)\]", e)
        if mc:
            comps = [x.strip().strip('"\'') for x in re.findall(r"\"([^\"]+)\"", mc.group(1))]
        out.append({
            "name": gs("name"),
            "sector": gs("sector"),
            "founder": gs("founder"),
            "thesisCluster": gs("thesisCluster"),
            "competitors": comps,
        })
    return out


def main():
    companies = parse_companies()
    by_name = {c["name"]: c for c in companies}
    print(f"  Parsed {len(companies)} companies")

    nodes = []
    edges = []
    edge_keys = set()

    for c in companies:
        nodes.append({
            "id": c["name"],
            "sector": c["sector"],
            "thesisCluster": c["thesisCluster"],
        })

    # 1. Competitor edges
    for c in companies:
        for comp in c["competitors"]:
            if comp in by_name:
                key = tuple(sorted([c["name"], comp]))
                if key in edge_keys: continue
                edge_keys.add(key)
                edges.append({"src": key[0], "dst": key[1], "type": "competitor"})

    # 2. Thesis-cluster edges (connect companies sharing a thesisCluster —
    #    but only include clusters with ≥2 and ≤8 members to avoid noise)
    by_cluster = defaultdict(list)
    for c in companies:
        if c["thesisCluster"]:
            by_cluster[c["thesisCluster"]].append(c["name"])
    for cluster, names in by_cluster.items():
        if not (2 <= len(names) <= 8): continue
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                key = tuple(sorted([names[i], names[j]]))
                if key in edge_keys: continue
                edge_keys.add(key)
                edges.append({"src": key[0], "dst": key[1],
                              "type": "thesis", "cluster": cluster})

    # 3. Founder-alumni edges (companies sharing a prior-employer keyword)
    alumni_kws = {
        "SpaceX":    ["ex-SpaceX", "SpaceX alum", "SpaceX engineer"],
        "Palantir":  ["ex-Palantir", "Palantir alum"],
        "OpenAI":    ["ex-OpenAI", "OpenAI alum"],
        "Anduril":   ["ex-Anduril", "Anduril alum"],
        "DeepMind":  ["ex-DeepMind", "DeepMind alum"],
        "Tesla":     ["ex-Tesla", "Tesla alum"],
    }
    alumni_groups = defaultdict(list)
    for c in companies:
        text = c["founder"]
        for parent, kws in alumni_kws.items():
            if any(k in text for k in kws):
                alumni_groups[parent].append(c["name"])
    for parent, names in alumni_groups.items():
        # One hub node per parent, edges from parent to each
        hub = f"{parent}-alumni-hub"
        nodes.append({"id": hub, "sector": "alumni", "thesisCluster": ""})
        for n in names:
            edges.append({"src": hub, "dst": n, "type": "alumni"})

    payload = {
        "nodes": nodes,
        "edges": edges,
        "counts": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "competitor_edges": sum(1 for e in edges if e["type"] == "competitor"),
            "thesis_edges": sum(1 for e in edges if e["type"] == "thesis"),
            "alumni_edges": sum(1 for e in edges if e["type"] == "alumni"),
        },
    }
    OUT_PATH.write_text(json.dumps(payload, indent=2))
    print(f"  Wrote network graph: {len(nodes)} nodes / {len(edges)} edges")
    print(f"    competitor={payload['counts']['competitor_edges']} "
          f"thesis={payload['counts']['thesis_edges']} "
          f"alumni={payload['counts']['alumni_edges']}")


if __name__ == "__main__":
    main()
