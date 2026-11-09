#!/usr/bin/env bash
# zen-statusline.sh - Telemetría de Estrés Cognitivo en Vivo para Antigravity CLI (Bash)
# Recibe el payload JSON de estado por stdin y renderiza el indicador CSI.

payload="$(cat)"
if [ -z "$payload" ]; then
    echo -n "🧘 Zen: Inicializando..."
    exit 0
fi

python3 -c '
import json, sys
from pathlib import Path

try:
    data = json.loads(sys.argv[1])
except Exception:
    print("🧘 Zen: Activo", end="")
    sys.exit(0)

cw = data.get("context_window") or {}
total_in = int(cw.get("total_input_tokens") or 0)
used_pct = float(cw.get("used_percentage") or 0.0)

model_obj = data.get("model") or {}
model_name = model_obj.get("display_name") or model_obj.get("id") or "Model"
effort = model_obj.get("effort") or "default"
state = data.get("agent_state") or "idle"

subagents = data.get("subagents") or []
running_subs = sum(1 for s in subagents if s.get("status") == "running")

errors = 0
turns = 0
m_file = Path(".zen/runtime_metrics.json")
if m_file.exists():
    try:
        m = json.loads(m_file.read_text(encoding="utf-8"))
        errors = int(m.get("consecutive_errors", 0))
        turns = int(m.get("invocation_count", 0)) - int(m.get("last_checkpoint_turn", 0))
    except Exception:
        pass

GREEN = "\033[38;5;114m"
YELLOW = "\033[38;5;221m"
ORANGE = "\033[38;5;209m"
RED = "\033[38;5;203m"
CYAN = "\033[38;5;117m"
RESET = "\033[0m"

tok_k = f"{total_in/1000:.1f}k" if total_in > 0 else "0k"

if total_in >= 75000 or turns >= 15 or errors >= 2:
    badge = f"{RED}🔴 ESTRES CRITICO (/zen-reset + /clear){RESET}"
elif total_in >= 32000 or turns >= 10 or errors == 1:
    badge = f"{ORANGE}🟠 CONTEXT ROT (Usa /zen-reset o /btw){RESET}"
elif total_in >= 12000 or turns >= 6:
    badge = f"{YELLOW}🟡 DRIFT LEVE (Valle U){RESET}"
else:
    badge = f"{GREEN}🟢 ZEN OPTIMO{RESET}"

err_str = f" | {RED}⚠ Err:{errors}{RESET}" if errors > 0 else ""
sub_str = f" | 🤖 Subs:{running_subs}" if running_subs > 0 else ""

print(f"{badge} | {CYAN}{model_name} ({effort}){RESET} | Tok:{tok_k} ({used_pct:.1f}%) | Turnos:{turns}{err_str}{sub_str} | [{state}]", end="")
' "$payload"
