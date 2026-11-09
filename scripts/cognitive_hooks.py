#!/usr/bin/env python3
"""
cognitive_hooks.py - Gobernador Determinista de Ciclo de Vida para Google Antigravity.
Optimizado para Gemini 3.8 Flash, Gemini 4 Argon y Claude 4.6 / 5.5.
"""

from __future__ import annotations
import json, os, re, sys
from pathlib import Path
from typing import Any, Dict, Optional

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stdin.reconfigure(encoding='utf-8')
except Exception:
    pass

ZEN_DIR = Path(".zen")
STATE_FILE = ZEN_DIR / "state.json"
HANDOFF_FILE = ZEN_DIR / "handoff.md"
METRICS_FILE = ZEN_DIR / "runtime_metrics.json"

def find_project_root(payload: Optional[Dict[str, Any]] = None) -> Path:
    """Descubre dinámicamente la raíz del proyecto para aislamiento estricto por proyecto."""
    env_root = os.environ.get("ZEN_PROJECT_DIR") or os.environ.get("ZEN_ROOT")
    if env_root:
        p = Path(env_root).resolve()
        if p.exists() and p.is_dir():
            return p

    start_path: Optional[Path] = None
    if payload:
        ws = payload.get("workspaceRoot") or payload.get("cwd") or payload.get("workspace_path")
        if not ws and payload.get("workspacePaths"):
            paths = payload.get("workspacePaths")
            if isinstance(paths, list) and len(paths) > 0:
                ws = paths[0]
        if ws:
            p = Path(ws).resolve()
            if p.exists():
                start_path = p

    curr = (start_path or Path.cwd()).resolve()
    root_markers = [
        ".git", ".zen", "pyproject.toml", "package.json",
        "Cargo.toml", "go.mod", "pom.xml", "CMakeLists.txt",
        "requirements.txt", "README.md",
    ]
    for parent in [curr] + list(curr.parents):
        for marker in root_markers:
            if (parent / marker).exists():
                return parent
    return curr

def resolve_zen_paths(payload: Optional[Dict[str, Any]] = None) -> Path:
    global ZEN_DIR, STATE_FILE, HANDOFF_FILE, METRICS_FILE
    if not ZEN_DIR.is_absolute():
        root = find_project_root(payload)
        effective_dir = root / ZEN_DIR.name
    else:
        effective_dir = ZEN_DIR

    STATE_FILE = effective_dir / "state.json"
    HANDOFF_FILE = effective_dir / "handoff.md"
    METRICS_FILE = effective_dir / "runtime_metrics.json"
    return effective_dir

STRESS_TRIGGER_WORDS = re.compile(
    r"\b(wrong again|still broken|you broke|stop hallucinating|urgent|wtf|stupid|"
    r"otra vez mal|sigue roto|no funciona|deja de inventar|urgente|error tras error)\b",
    re.IGNORECASE,
)

SAFE_TOOLS = {
    "read_file", "view_file", "grep_search", "find_by_name", "invoke_subagent",
    "define_subagent", "manage_subagents", "send_message", "list_resources",
    "read_resource", "ask_question", "search_web", "search_marketplace",
    "list_plugin_accounts", "manage_task", "schedule",
}

def load_metrics(conversation_id: str = "default", payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    target_dir = resolve_zen_paths(payload)
    target_dir.mkdir(parents=True, exist_ok=True)
    default_m = {
        "conversation_id": conversation_id,
        "invocation_count": 0,
        "consecutive_errors": 0,
        "code_modified_since_test": False,
        "last_checkpoint_turn": 0,
        "stop_continuations": 0,
        "direct_reads_count": 0,
        "csi": 0,
    }
    if METRICS_FILE.exists():
        try:
            data = json.loads(METRICS_FILE.read_text(encoding="utf-8"))
            return {**default_m, **data}
        except Exception:
            pass
    return default_m

def save_metrics(metrics: Dict[str, Any], payload: Optional[Dict[str, Any]] = None) -> None:
    target_dir = resolve_zen_paths(payload)
    target_dir.mkdir(parents=True, exist_ok=True)
    METRICS_FILE.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")

def handle_session_start(payload: Dict[str, Any]) -> Dict[str, Any]:
    resolve_zen_paths(payload)
    conv_id = payload.get("conversationId", "default")
    save_metrics(load_metrics(conv_id, payload), payload)
    if HANDOFF_FILE.exists():
        try:
            handoff_text = HANDOFF_FILE.read_text(encoding="utf-8").strip()
            if handoff_text:
                return {
                    "injectSteps": [
                        {
                            "systemMessage": {
                                "systemMessage": (
                                    "[ANTIGRAVITY-ZEN SESSION HANDOFF RESTORED]\n"
                                    "Se ha restaurado el estado limpio consolidado (CONCAT) de la sesión previa. "
                                    "Toma una respiración analítica profunda, adopta la perspectiva objetiva de "
                                    "'El Arquitecto Auditor' y continúa por el siguiente objetivo atómico pendiente:\n\n"
                                    + handoff_text
                                ),
                                "metadata": {"source": "antigravity-zen-handoff"},
                            }
                        }
                    ]
                }
        except Exception:
            pass
    return {}

def handle_pre_invocation(payload: Dict[str, Any]) -> Dict[str, Any]:
    resolve_zen_paths(payload)
    conv_id = payload.get("conversationId", "default")
    model_name = str(payload.get("modelName", "")).lower()
    invocation_num = int(payload.get("invocationNum", 0))
    last_user_input = str(payload.get("lastUserInput", ""))

    metrics = load_metrics(conv_id, payload)
    metrics["invocation_count"] = max(metrics["invocation_count"], invocation_num + 1)
    save_metrics(metrics, payload)

    turns_since_cp = metrics["invocation_count"] - metrics.get("last_checkpoint_turn", 0)
    consec_errors = metrics.get("consecutive_errors", 0)
    direct_reads = metrics.get("direct_reads_count", 0)
    user_stressed = bool(STRESS_TRIGGER_WORDS.search(last_user_input))

    # Umbral calibrado: 12 turnos para Gemini 3.8 Flash (en lugar de 6)
    if turns_since_cp < 12 and consec_errors == 0 and not user_stressed and direct_reads < 8:
        return {}

    directives = [
        "[ZEN COGNITIVE ANCHOR - RECENCY ZONE]",
        "1. DESESCALADA Y MINDFULNESS: Toma una respiración analítica profunda y trabaja paso a paso con calma objetiva. Descarta cualquier residuo atencional.",
        "2. DISTANCIAMIENTO EN 3ª PERSONA (ANTI-SYCOPHANCY): Evalúa en tercera persona como 'El Arquitecto Auditor'. No concedas premisas erróneas por complacencia.",
    ]

    if "claude" in model_name:
        directives.append(
            "3. PROTOCOLO CLAUDE (EXTRACCIÓN LITERAL): Cita textualmente (verbatim) entre comillas las 3 a 5 líneas exactas de código o test conflictivas antes de razonar para evitar la abstención."
        )
    else:
        directives.append(
            "3. PROTOCOLO GEMINI (CONTINUIDAD Y PRECISIÓN): No omitas precondiciones por impaciencia. Preserva intacta la secuencia thought_signature del turno actual."
        )

    if direct_reads >= 8:
        directives.append(
            f"4. SUGERENCIA DE EFICIENCIA ({direct_reads} lecturas directas acumuladas): Si necesitas auditar múltiples archivos adicionales, considera delegar a 'zen-explorer' para mantener tu ventana de contexto despejada."
        )
        metrics["direct_reads_count"] = 0
        save_metrics(metrics, payload)

    if consec_errors >= 1:
        directives.append(
            f"5. ALERTA DE CASCADA ({consec_errors} error(es)): El 78% de los errores tempranos se propagan con parches rápidos. Si este paso falla, detente y consulta la pizarra con 'zen board'."
        )

    return {"injectSteps": [{"ephemeralMessage": "\n".join(directives)}]}

def handle_pre_tool(payload: Dict[str, Any]) -> Dict[str, Any]:
    resolve_zen_paths(payload)
    conv_id = payload.get("conversationId", "default")
    tool_call = payload.get("toolCall", {})
    tool_name = str(tool_call.get("name", ""))
    tool_args_str = json.dumps(tool_call.get("args", {})).lower()
    metrics = load_metrics(conv_id, payload)

    if tool_name in SAFE_TOOLS or "zen.py" in tool_args_str:
        return {"decision": "allow"}

    # Cortafuegos activo al 2º error consecutivo
    if metrics.get("consecutive_errors", 0) >= 2:
        return {
            "decision": "deny",
            "reason": (
                "[ZEN CIRCUIT BREAKER ACTIVADO]: Has acumulado 2 fallos consecutivos de herramientas. "
                "Para evitar una cascada de errores (61% de probabilidad de propagación), "
                "tienes bloqueadas las herramientas de modificación a ciegas. "
                "Acción obligatoria: (1) Consulta la pizarra con 'zen board', o "
                "(2) Delega el diagnóstico a 'zen-investigator' con 'invoke_subagent'."
            ),
        }
    return {"decision": "allow"}

def handle_post_tool(payload: Dict[str, Any]) -> Dict[str, Any]:
    resolve_zen_paths(payload)
    conv_id = payload.get("conversationId", "default")
    tool_call = payload.get("toolCall", {})
    tool_name = str(tool_call.get("name", ""))
    tool_args_str = json.dumps(tool_call.get("args", {})).lower()
    error_msg = str(payload.get("error", "")).strip()

    metrics = load_metrics(conv_id, payload)
    if error_msg:
        metrics["consecutive_errors"] = metrics.get("consecutive_errors", 0) + 1
    else:
        if "zen.py" not in tool_args_str:
            metrics["consecutive_errors"] = 0

    if tool_name == "read_file":
        metrics["direct_reads_count"] = metrics.get("direct_reads_count", 0) + 1
    elif tool_name == "invoke_subagent":
        metrics["direct_reads_count"] = 0

    write_tools = {"write_file", "edit_file", "replace_file_content", "multi_replace_file_content"}
    if tool_name in write_tools:
        args = tool_call.get("args", {})
        fpath = str(args.get("Path", "") or args.get("path", "")).lower()
        is_doc = fpath.endswith((".md", ".txt", ".json", ".log")) or "\\brain\\" in fpath or "/brain/" in fpath
        if not is_doc:
            metrics["code_modified_since_test"] = True
    elif tool_name == "run_command" and not error_msg:
        test_indicators = ["test", "pytest", "jest", "vitest", "cargo", "go test", "lint", "check"]
        if any(k in tool_args_str for k in test_indicators):
            metrics["code_modified_since_test"] = False

    save_metrics(metrics, payload)
    return {}

def handle_stop_gate(payload: Dict[str, Any]) -> Dict[str, Any]:
    resolve_zen_paths(payload)
    conv_id = payload.get("conversationId", "default")
    reason = str(payload.get("terminationReason", ""))
    fully_idle = bool(payload.get("fullyIdle", True))
    metrics = load_metrics(conv_id, payload)

    if reason in ("NO_TOOL_CALL", "model_stop", "") and fully_idle:
        if metrics.get("code_modified_since_test", False) and metrics.get("stop_continuations", 0) < 1:
            metrics["stop_continuations"] = metrics.get("stop_continuations", 0) + 1
            save_metrics(metrics, payload)
            return {
                "decision": "continue",
                "reason": (
                    "[ZEN ANTI-CEREMONIALIZATION GATE]: Modificaste archivos de código pero no ejecutaste "
                    "ningún comando de prueba posterior. Corre las pruebas de tu stack o guarda el checkpoint "
                    "con 'zen checkpoint' antes de cerrar el turno."
                ),
            }
    metrics["stop_continuations"] = 0
    save_metrics(metrics, payload)
    return {"decision": "allow_stop"}

def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    raw_input = sys.stdin.read().strip()
    payload = {}
    if raw_input:
        try: payload = json.loads(raw_input)
        except Exception: payload = {}

    if mode == "session-start": out = handle_session_start(payload)
    elif mode == "pre-invocation": out = handle_pre_invocation(payload)
    elif mode == "pre-tool": out = handle_pre_tool(payload)
    elif mode == "post-tool": out = handle_post_tool(payload)
    elif mode == "stop-gate": out = handle_stop_gate(payload)
    else: out = {}

    sys.stdout.write(json.dumps(out, ensure_ascii=False) + "\n")
    sys.stdout.flush()

if __name__ == "__main__":
    main()
