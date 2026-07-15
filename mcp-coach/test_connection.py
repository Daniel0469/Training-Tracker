#!/usr/bin/env python3
"""Quick check that the coach can read your data with the settings in ../.mcp.json.

Run:  python mcp-coach/test_connection.py
It reads the token/repo/path straight from .mcp.json (never printed) and either
prints your people + session counts, or a clear error to fix.
"""
import json, os, sys

here = os.path.dirname(os.path.abspath(__file__))
cfg_path = os.path.join(here, "..", ".mcp.json")
try:
    cfg = json.load(open(cfg_path, encoding="utf-8"))
    env = cfg["mcpServers"]["training-tracker"]["env"]
except Exception as e:
    print("Couldn't read ../.mcp.json:", e); sys.exit(1)

if "PASTE" in env.get("TT_GITHUB_TOKEN", ""):
    print("Token not set yet — replace PASTE_YOUR_GITHUB_TOKEN_HERE in .mcp.json first."); sys.exit(1)

for k, v in env.items():
    os.environ[k] = v
sys.path.insert(0, here)
import server

try:
    data = server.load_data()
    print("Connected to", env.get("TT_GITHUB_REPO"), "/", env.get("TT_GITHUB_PATH"))
    print(json.dumps(server.list_people(data), indent=2))
    print("\nLooks good - restart Claude Code and the coach is ready.")
except Exception as e:
    print("FAILED:", e)
    print("- Is TT_GITHUB_PATH the exact file name in your Training-Data repo?")
    print("- Was the token pasted fully, with Contents: read on Training-Data?")
