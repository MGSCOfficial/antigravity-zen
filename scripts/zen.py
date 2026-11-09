#!/usr/bin/env python3
"""
zen.py - Motor de Pizarra Dinámica y Gobernanza Cognitiva para Google Antigravity.
Calibrado para Gemini 3.8 Flash, Gemini 4 Argon y Claude 4.6 / 5.5.
"""

from __future__ import annotations
import argparse, json, math, os, re, subprocess, sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stdin.reconfigure(encoding='utf-8')
except Exception:
    pass

ZEN_DIR = Path(".zen")
STATE_FILE = ZEN_DIR / "state.json"
BLACKBOARD_FILE = ZEN_DIR / "blackboard.md"
HANDOFF_FILE = ZEN_DIR / "handoff.md"
METRICS_FILE = ZEN_DIR / "runtime_metrics.json"
GRAPH_FILE = ZEN_DIR / "knowledge_graph.json"

def find_project_root(start_path: Optional[Path] = None) -> Path:
    """
    Descubre dinámicamente la raíz del proyecto activo para garantizar aislamiento estricto.
    Busca marcadores de proyecto (.git, .zen, pyproject.toml, package.json, Cargo.toml, go.mod).
    Si no encuentra ninguno, retorna cwd.
    """
    env_root = os.environ.get("ZEN_PROJECT_DIR") or os.environ.get("ZEN_ROOT")
    if env_root:
        p = Path(env_root).resolve()
        if p.exists() and p.is_dir():
            return p

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

def resolve_zen_paths() -> Path:
    """Sincroniza las rutas de la Pizarra con la raíz del proyecto activo."""
    global ZEN_DIR, STATE_FILE, BLACKBOARD_FILE, HANDOFF_FILE, METRICS_FILE, GRAPH_FILE
    if not ZEN_DIR.is_absolute():
        root = find_project_root()
        effective_dir = root / ZEN_DIR.name
    else:
        effective_dir = ZEN_DIR

    STATE_FILE = effective_dir / "state.json"
    BLACKBOARD_FILE = effective_dir / "blackboard.md"
    HANDOFF_FILE = effective_dir / "handoff.md"
    METRICS_FILE = effective_dir / "runtime_metrics.json"
    GRAPH_FILE = effective_dir / "knowledge_graph.json"
    return effective_dir

IMPERATIVE_PATTERN = re.compile(
    r"^\s*(?:[-*+]|\d+\.)?\s*\b(always|never|must|ensure|use|avoid|do not|don't|"
    r"run|verify|prefer|require|siempre|nunca|debes|asegura|usa|evita|no\s+\w+)\b",
    re.IGNORECASE,
)
NEGATIVE_ONLY_PATTERN = re.compile(
    r"\b(never|do not|don't|avoid|prohibited|nunca|jamás|evita|prohibido)\b",
    re.IGNORECASE,
)
WEAK_HEDGING_PATTERN = re.compile(
    r"\b(try to|maybe|if possible|consider|ideally|perhaps|intenta|tal vez|si es posible|quizás)\b",
    re.IGNORECASE,
)

def get_iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def ensure_zen_dir() -> Path:
    target_dir = resolve_zen_paths()
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir

def load_state() -> Dict[str, Any]:
    ensure_zen_dir()
    default_state: Dict[str, Any] = {
        "project_goal": "",
        "updated_at": get_iso_now(),
        "invariants": [],
        "features": [],
        "active_target": "",
        "preconditions": "Ninguna requerida.",
        "verification_cmd": "",
        "known_blockers": [],
        "discarded_dead_ends": [],
    }
    if STATE_FILE.exists():
        try:
            data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            return {**default_state, **data}
        except Exception:
            pass
    return default_state

def save_state(state: Dict[str, Any]) -> None:
    ensure_zen_dir()
    state["updated_at"] = get_iso_now()
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    render_blackboard(state)
    render_handoff(state)

def load_knowledge_graph() -> List[Dict[str, Any]]:
    ensure_zen_dir()
    if GRAPH_FILE.exists():
        try:
            return json.loads(GRAPH_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []

def save_knowledge_graph(graph: List[Dict[str, Any]]) -> None:
    ensure_zen_dir()
    GRAPH_FILE.write_text(json.dumps(graph, indent=2, ensure_ascii=False), encoding="utf-8")

def get_git_info() -> Dict[str, Any]:
    info = {"branch": "unknown", "modified_files": [], "recent_commits": []}
    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            stderr=subprocess.DEVNULL, text=True, timeout=3
        ).strip()
        info["branch"] = branch
    except Exception:
        pass
    try:
        status = subprocess.check_output(
            ["git", "status", "--short"],
            stderr=subprocess.DEVNULL, text=True, timeout=3
        ).strip().splitlines()
        info["modified_files"] = status[:12]
    except Exception:
        pass
    return info

def load_metrics() -> Dict[str, Any]:
    default_m = {
        "invocation_count": 0,
        "consecutive_errors": 0,
        "code_modified_since_test": False,
        "last_checkpoint_turn": 0,
        "stop_continuations": 0,
        "csi": 0,
    }
    if METRICS_FILE.exists():
        try:
            data = json.loads(METRICS_FILE.read_text(encoding="utf-8"))
            return {**default_m, **data}
        except Exception:
            pass
    return default_m

def save_metrics(metrics: Dict[str, Any]) -> None:
    ensure_zen_dir()
    METRICS_FILE.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")

def render_blackboard(state: Dict[str, Any]) -> None:
    git_info = get_git_info()
    metrics = load_metrics()
    csi = metrics.get("csi", 0)
    badge = f"🟢 Zen Óptimo (CSI: {csi})"
    if csi >= 75:
        badge = f"🔴 Estrés Crítico (CSI: {csi})"
    elif csi >= 40:
        badge = f"🟠 Context Rot (CSI: {csi})"
    elif csi >= 20:
        badge = f"🟡 Drift Leve (CSI: {csi})"

    invariants_lines = [f"{i+1}. {inv}" for i, inv in enumerate(state.get("invariants", []))]
    if not invariants_lines:
        invariants_lines = ["1. Mantener arquitectura limpia y modular.", "2. Verificar con pruebas antes de reportar completitud."]

    milestones_lines = []
    for feat in state.get("features", []):
        checked = "x" if feat.get("passes") else " "
        evidence = f" *(Verificado: `{feat.get('evidence_cmd')}`)*" if feat.get("evidence_cmd") else ""
        milestones_lines.append(f"- [{checked}] {feat.get('description', '')}{evidence}")
    if not milestones_lines:
        milestones_lines = ["- [ ] Sin hitos definidos todavía."]

    kg = load_knowledge_graph()
    kg_lines = []
    for entry in kg[-6:]:
        why = f" *(Razón: {entry['why']})*" if entry.get("why") else ""
        kg_lines.append(f"- **{entry.get('subject')}** {entry.get('predicate')} `{entry.get('object')}`{why}")
    if not kg_lines:
        kg_lines = ["- Sin decisiones registradas todavía."]

    dead_ends_lines = []
    for d in state.get("discarded_dead_ends", []):
        if isinstance(d, dict):
            hyp = d.get("hypothesis", "")
            reason = d.get("reason", "")
            ts = f" *({d.get('timestamp')})*" if d.get("timestamp") else ""
            dead_ends_lines.append(f"- ❌ **{hyp}**: {reason}{ts}")
        else:
            dead_ends_lines.append(f"- ❌ {d}")
    if not dead_ends_lines:
        dead_ends_lines = ["- Sin hipótesis descartadas (ningún callejón sin salida registrado)."]

    blockers_lines = [f"- [!] {b}" for b in state.get("known_blockers", [])]
    if not blockers_lines:
        blockers_lines = ["- Sin bloqueos activos."]

    mod_lines = [f"- `{m}`" for m in git_info["modified_files"]]
    if not mod_lines:
        mod_lines = ["- Working tree limpio."]

    content = [
        "# 🧘 ZEN DYNAMIC BLACKBOARD",
        "*Pizarra Persistente de Memoria de Trabajo e Invariantes Arquitectónicas*",
        "",
        f"- **Última Actualización**: `{state.get('updated_at', get_iso_now())}`",
        f"- **Rama Git**: `{git_info['branch']}`",
        f"- **Estado Cognitivo**: {badge}",
        "",
        "---",
        "",
        "## 1. OBJETIVO CONSOLIDADO (CONCAT SPECIFICATION)",
        f"> {state.get('project_goal', 'No definido aún.')}",
        "",
        "---",
        "",
        "## 2. REGLAS INVARIANTES Y CONTRATOS TÉCNICOS (MÁXIMO 5)",
        "\n".join(invariants_lines),
        "",
        "---",
        "",
        "## 3. HITOS VERIFICADOS (NO RE-IMPLEMENTAR NI ADIVINAR)",
        "\n".join(milestones_lines),
        "",
        "---",
        "",
        "## 4. FOCO ATÓMICO INMEDIATO (MÁXIMO 1 TAREA ACTIVA)",
        f"> 🎯 **{state.get('active_target', 'Definir siguiente paso atómico.')}**",
        f"- Precondiciones verificadas: {state.get('preconditions', 'Verificadas.')}",
        f"- Comando de verificación asignado: `{state.get('verification_cmd', 'No especificado.')}`",
        "",
        "---",
        "",
        "## 5. GRAFO DE CONOCIMIENTO Y DECISIONES (POR QUÉ HICIMOS X EN VEZ DE Y)",
        "\n".join(kg_lines),
        "",
        "---",
        "",
        "## 6. ENFOQUES DESCARTADOS / DEAD ENDS (NO REPETIR HIPÓTESIS FALLIDAS)",
        "\n".join(dead_ends_lines),
        "",
        "---",
        "",
        "## 7. BLOQUEOS E HIPÓTESIS DE CAUSA RAÍZ ACTIVAS",
        "\n".join(blockers_lines),
        "",
        "---",
        "",
        "## 8. MAPA DE ARCHIVOS DEL WORKSPACE MODIFICADOS",
        "\n".join(mod_lines),
        "",
    ]
    BLACKBOARD_FILE.write_text("\n".join(content), encoding="utf-8")

def render_handoff(state: Dict[str, Any]) -> None:
    git_info = get_git_info()
    passing = [f["description"] for f in state.get("features", []) if f.get("passes")]
    pending = [f["description"] for f in state.get("features", []) if not f.get("passes")]

    lines = [
        "# ZEN CONTEXT HANDOFF (SINGLE-BLOCK CONCAT SPECIFICATION)",
        f"- **Timestamp**: `{get_iso_now()}` | **Git Branch**: `{git_info['branch']}`",
        f"- **Core Objective (Consolidated)**: {state.get('project_goal', 'No especificado')}",
        "",
        "## 1. Verified Passing Milestones (DO NOT RE-IMPLEMENT)",
    ]
    for p in passing[-8:] or ["Ninguno registrado aún."]:
        lines.append(f"- [x] {p}")

    active_target = state.get("active_target") or (pending[0] if pending else "Continuar siguiente tarea.")
    lines.append("\n## 2. Active Next Atomic Target (FOCUS ONLY HERE)")
    lines.append(f"- [ ] {active_target}")

    lines.append("\n## 3. Discarded Dead Ends (PROHIBITED APPROACHES - DO NOT RETRY)")
    dead_ends = state.get("discarded_dead_ends", [])
    if dead_ends:
        for d in dead_ends[-6:]:
            if isinstance(d, dict):
                lines.append(f"- ❌ **{d.get('hypothesis', '')}**: {d.get('reason', '')}")
            else:
                lines.append(f"- ❌ {d}")
    else:
        lines.append("- Ningún enfoque descartado aún.")

    lines.append("\n## 4. Active Root-Cause Hypotheses & Blockers")
    for b in state.get("known_blockers", []) or ["Sin bloqueos activos."]:
        lines.append(f"- [!] {b}")

    lines.append("\n## 5. Modified Workspace Files")
    for mf in git_info["modified_files"][:10] or ["Working tree limpio."]:
        lines.append(f"- `{mf}`")

    HANDOFF_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")

def find_latest_transcript() -> Optional[Path]:
    home = Path.home()
    search_roots = [
        Path.cwd() / ".gemini" / "antigravity",
        home / ".gemini" / "antigravity" / "brain",
        home / ".gemini" / "antigravity-cli" / "brain",
        home / ".gemini" / "antigravity-ide" / "brain",
    ]
    candidates: List[Path] = []
    for root in search_roots:
        if root.exists():
            candidates.extend(root.glob("*/.system_generated/logs/transcript.jsonl"))
            candidates.extend(root.glob("*/*.jsonl"))
            candidates.extend(root.glob("transcript.jsonl"))
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)

def compute_shannon_entropy(words: List[str]) -> float:
    """Calcula la entropía léxica de Shannon para detectar colapso léxico y bucles obsesivos."""
    if not words or len(words) < 20:
        return 0.0
    total = len(words)
    counts = Counter(words)
    entropy = 0.0
    for count in counts.values():
        p = count / total
        entropy -= p * math.log2(p)
    return round(entropy, 2)

def analyze_transcript(transcript_path: Optional[Path]) -> Dict[str, Any]:
    stats = {
        "turns": 0,
        "estimated_tokens": 0,
        "tool_calls": 0,
        "tool_result_chars": 0,
        "total_chars": 0,
        "consecutive_errors": 0,
        "assistant_avg_words": 0,
        "extraneous_load_ratio": 0.0,
        "shannon_entropy": 0.0,
    }
    m = load_metrics()
    stats["consecutive_errors"] = m.get("consecutive_errors", 0)
    stats["turns"] = max(stats["turns"], m.get("invocation_count", 0))

    if not transcript_path or not transcript_path.exists():
        return stats

    assistant_words: List[int] = []
    assistant_corpus: List[str] = []
    try:
        with transcript_path.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line_str = line.strip()
                if not line_str:
                    continue
                stats["total_chars"] += len(line_str)
                try:
                    entry = json.loads(line_str)
                except Exception:
                    continue
                role = str(entry.get("role", entry.get("type", ""))).lower()
                content_str = json.dumps(entry, ensure_ascii=False)
                if "user" in role:
                    stats["turns"] += 1
                elif "assistant" in role or "model" in role or "planner_response" in role:
                    tokens = re.findall(r"\b[a-zA-ZáéíóúÁÉÍÓÚñÑ_0-9]{2,}\b", content_str.lower())
                    assistant_corpus.extend(tokens)
                    assistant_words.append(len(content_str.split()))
                if "tool" in role or "functionResponse" in content_str or "tool_result" in content_str:
                    stats["tool_calls"] += 1
                    stats["tool_result_chars"] += len(content_str)
    except Exception:
        pass

    stats["estimated_tokens"] = stats["total_chars"] // 4
    if assistant_words:
        stats["assistant_avg_words"] = sum(assistant_words) // len(assistant_words)
    if stats["total_chars"] > 0:
        stats["extraneous_load_ratio"] = round(stats["tool_result_chars"] / stats["total_chars"], 3)
    if assistant_corpus:
        stats["shannon_entropy"] = compute_shannon_entropy(assistant_corpus[-500:])
    return stats

def compute_csi(stats: Dict[str, Any]) -> Tuple[int, str]:
    tokens = stats["estimated_tokens"]
    turns = stats["turns"]
    errors = stats["consecutive_errors"]
    total_chars = stats["total_chars"]
    tool_share = (stats["tool_result_chars"] / max(1, total_chars)) * 100 if total_chars > 0 else 0

    score = 0
    # Umbrales CSI 2.0 optimizados para Gemini 3.8 Flash
    if tokens > 140000:
        score += 45
    elif tokens > 80000:
        score += 30
    elif tokens > 40000:
        score += 15
    elif tokens > 10000:
        score += 5

    if turns > 25:
        score += 35
    elif turns > 18:
        score += 25
    elif turns > 12:
        score += 12

    score += min(40, errors * 18)
    if tool_share > 65:
        score += 15

    csi = min(100, score)
    if csi >= 75:
        status = "CRÍTICO (Saturación Cognitiva CS=1 / Requiere Reset CONCAT)"
    elif csi >= 40:
        status = "MODERADO-ALTO (Context Rot Activo / Valle de U)"
    elif csi >= 20:
        status = "LEVE (Inicio de Atenuación)"
    else:
        status = "ÓPTIMO (Atención Plena Intacta)"

    m = load_metrics()
    m["csi"] = csi
    save_metrics(m)
    return csi, status

def cmd_audit(_args: argparse.Namespace) -> None:
    transcript = find_latest_transcript()
    stats = analyze_transcript(transcript)
    csi, status = compute_csi(stats)
    tool_pct = round((stats["tool_result_chars"] / max(1, stats["total_chars"])) * 100, 1) if stats["total_chars"] > 0 else 0.0

    report = {
        "cognitive_stress_index_csi": csi,
        "diagnostic_status": status,
        "calibrated_for": "Gemini 3.8 Flash / Claude 4.6+",
        "project_root": str(find_project_root()),
        "metrics": {
            "active_turns": stats["turns"],
            "estimated_context_tokens": stats["estimated_tokens"],
            "tool_calls_count": stats["tool_calls"],
            "extraneous_cognitive_load_ratio_ek": f"{tool_pct}%",
            "shannon_lexical_entropy": stats.get("shannon_entropy", 0.0),
            "consecutive_tool_errors": stats["consecutive_errors"],
            "assistant_avg_words_per_turn": stats["assistant_avg_words"],
        },
        "prescribed_actions": [],
    }

    if stats["consecutive_errors"] >= 2:
        report["prescribed_actions"].append(
            "ALTO EL FUEGO: >=2 errores consecutivos. Prohibido adivinar. Formula hipótesis en pizarra o delega a zen-investigator."
        )
    if tool_pct > 65.0:
        report["prescribed_actions"].append(
            "CARGA EXTRÍNSECA ELEVADA (Ek > 65%): Los resultados de herramientas saturan el contexto. Delega búsquedas a zen-explorer."
        )
    if stats.get("shannon_entropy", 0.0) > 0 and stats.get("shannon_entropy", 0.0) < 3.2:
        report["prescribed_actions"].append(
            "COLAPSO LÉXICO DETECTADO: Entropía Shannon < 3.2 bits. El agente exhibe bucle obsesivo o lenguaje repetitivo. Guarda checkpoint y reinicia sesión con /clear."
        )
    if csi >= 75:
        report["prescribed_actions"].append(
            "COMPACTACIÓN REQUERIDA: Ejecuta 'zen checkpoint' y solicita al usuario ejecutar '/clear' (Principio CONCAT)."
        )
    elif csi >= 40:
        report["prescribed_actions"].append(
            "HIGIENE PREVENTIVA: Delega inspecciones pesadas a 'zen-investigator' vía invoke_subagent."
        )
    else:
        report["prescribed_actions"].append(
            "CONTINUAR: Contexto saludable. Mantén la perspectiva de 'El Arquitecto Auditor' y foco en 1 tarea a la vez."
        )

    print(json.dumps(report, indent=2, ensure_ascii=False))

def cmd_board(args: argparse.Namespace) -> None:
    state = load_state()
    changed = False

    if args.goal:
        state["project_goal"] = args.goal
        changed = True
    if args.target:
        state["active_target"] = args.target
        changed = True
    if args.preconditions:
        state["preconditions"] = args.preconditions
        changed = True
    if args.verification_cmd:
        state["verification_cmd"] = args.verification_cmd
        changed = True
    if args.add_invariant:
        for inv in [x.strip() for x in args.add_invariant.split(";") if x.strip()]:
            if inv not in state.setdefault("invariants", []):
                state["invariants"].append(inv)
                changed = True
        state["invariants"] = state["invariants"][:5]
    if args.add_task:
        for t in [x.strip() for x in args.add_task.split(";") if x.strip()]:
            if not any(f.get("description") == t for f in state.setdefault("features", [])):
                state["features"].append({"description": t, "passes": False, "verified_at": None, "evidence_cmd": None})
                changed = True
    if args.complete_task:
        now = get_iso_now()
        for t in [x.strip() for x in args.complete_task.split(";") if x.strip()]:
            found = False
            for f in state.setdefault("features", []):
                if f.get("description") == t:
                    f["passes"] = True
                    f["verified_at"] = now
                    f["evidence_cmd"] = args.evidence
                    found = True
                    changed = True
            if not found:
                state["features"].append({"description": t, "passes": True, "verified_at": now, "evidence_cmd": args.evidence})
                changed = True
    if args.add_blocker:
        for b in [x.strip() for x in args.add_blocker.split(";") if x.strip()]:
            if b not in state.setdefault("known_blockers", []):
                state["known_blockers"].append(b)
                changed = True
    if args.clear_blockers:
        state["known_blockers"] = []
        changed = True
    if getattr(args, "add_dead_end", None):
        now = get_iso_now()
        for de in [x.strip() for x in args.add_dead_end.split(";") if x.strip()]:
            if ":" in de:
                hyp, reason = de.split(":", 1)
                entry = {"hypothesis": hyp.strip(), "reason": reason.strip(), "timestamp": now}
            else:
                entry = {"hypothesis": de, "reason": "No viable / falló verificación", "timestamp": now}
            state.setdefault("discarded_dead_ends", []).append(entry)
            changed = True

    if changed or not BLACKBOARD_FILE.exists():
        save_state(state)

    if args.show or not changed:
        if BLACKBOARD_FILE.exists():
            print(BLACKBOARD_FILE.read_text(encoding="utf-8"))
        else:
            print("Pizarra vacía. Usa 'zen board --goal \"...\"' para inicializar.")

def cmd_checkpoint(args: argparse.Namespace) -> None:
    state = load_state()
    now = get_iso_now()

    if args.goal:
        state["project_goal"] = args.goal
    if args.completed:
        for item in [x.strip() for x in args.completed.split(";") if x.strip()]:
            found = False
            for feat in state.setdefault("features", []):
                if feat.get("description") == item:
                    feat["passes"] = True
                    feat["verified_at"] = now
                    feat["evidence_cmd"] = args.evidence
                    found = True
            if not found:
                state["features"].append({"description": item, "passes": True, "verified_at": now, "evidence_cmd": args.evidence})
    if args.next_step:
        targets = [x.strip() for x in args.next_step.split(";") if x.strip()]
        if targets:
            state["active_target"] = targets[0]
            for item in targets:
                if not any(f.get("description") == item for f in state.setdefault("features", [])):
                    state["features"].append({"description": item, "passes": False, "verified_at": None, "evidence_cmd": None})
    if args.blockers is not None:
        state["known_blockers"] = [x.strip() for x in args.blockers.split(";") if x.strip()]
    if getattr(args, "dead_end", None):
        now = get_iso_now()
        for de in [x.strip() for x in args.dead_end.split(";") if x.strip()]:
            if ":" in de:
                hyp, reason = de.split(":", 1)
                entry = {"hypothesis": hyp.strip(), "reason": reason.strip(), "timestamp": now}
            else:
                entry = {"hypothesis": de, "reason": "Descartado durante checkpoint", "timestamp": now}
            state.setdefault("discarded_dead_ends", []).append(entry)

    m = load_metrics()
    m["consecutive_errors"] = 0
    m["last_checkpoint_turn"] = m.get("invocation_count", 0)
    save_metrics(m)

    save_state(state)

    passing = sum(1 for f in state.get("features", []) if f.get("passes"))
    pending = sum(1 for f in state.get("features", []) if not f.get("passes"))

    print(json.dumps({
        "status": "CHECKPOINT_SAVED",
        "state_file": str(STATE_FILE),
        "blackboard_file": str(BLACKBOARD_FILE),
        "handoff_file": str(HANDOFF_FILE),
        "passing_features": passing,
        "pending_features": pending,
        "active_target": state.get("active_target"),
    }, indent=2, ensure_ascii=False))

def cmd_memory(args: argparse.Namespace) -> None:
    graph = load_knowledge_graph()
    subcmd = args.mem_command
    if subcmd == "add":
        entry = {
            "subject": args.subject,
            "predicate": args.predicate,
            "object": args.object,
            "why": args.why or "",
            "timestamp": get_iso_now(),
        }
        graph.append(entry)
        save_knowledge_graph(graph)
        render_blackboard(load_state())
        print(json.dumps({"status": "MEMORY_RECORDED", "entry": entry}, indent=2, ensure_ascii=False))
    elif subcmd == "query":
        query = args.term.lower()
        results = [
            e for e in graph
            if query in e.get("subject", "").lower()
            or query in e.get("predicate", "").lower()
            or query in e.get("object", "").lower()
            or query in e.get("why", "").lower()
        ]
        print(json.dumps({"query": args.term, "results_count": len(results), "matches": results}, indent=2, ensure_ascii=False))
    elif subcmd == "list":
        print(json.dumps({"total_entries": len(graph), "entries": graph}, indent=2, ensure_ascii=False))

def cmd_lint_rules(_args: argparse.Namespace) -> None:
    candidates = [
        Path("AGENTS.md"), Path("GEMINI.md"), Path(".agents/AGENTS.md"),
        Path(".agents/GEMINI.md"), Path.home() / ".gemini" / "config" / "GEMINI.md",
    ]
    rule_files = [p for p in candidates if p.exists()]
    if Path(".agents/rules").exists():
        rule_files.extend(Path(".agents/rules").glob("*.md"))
    home_rules = Path.home() / ".agents" / "rules"
    if home_rules.exists():
        rule_files.extend(home_rules.glob("*.md"))

    rule_files = list(dict.fromkeys(rule_files))
    total_instructions = 0
    total_tokens = 0
    findings: List[str] = []

    for rf in rule_files:
        try:
            text = rf.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        tokens = len(text) // 4
        total_tokens += tokens
        lines = text.splitlines()
        file_imperatives = 0
        negatives = 0
        hedges = 0

        for line in lines:
            if IMPERATIVE_PATTERN.search(line):
                file_imperatives += 1
            if NEGATIVE_ONLY_PATTERN.search(line) and "instead" not in line.lower() and "en su lugar" not in line.lower():
                negatives += 1
            if WEAK_HEDGING_PATTERN.search(line):
                hedges += 1

        total_instructions += file_imperatives
        if tokens > 5000:
            findings.append(f"{rf}: Supera el umbral seguro ({tokens} tokens).")
        if negatives > 3:
            findings.append(f"{rf}: Contiene {negatives} prohibiciones negativas puras ('Pink Elephant Problem').")
        if hedges > 2:
            findings.append(f"{rf}: Contiene {hedges} expresiones dubitativas ('try to/intenta').")

    status = "HEALTHY"
    if total_instructions > 250 or total_tokens > 15000:
        status = "OVERLOADED (Supera el techo seguro IFScale 2.0 de 250 directivas)"
    elif total_instructions > 150 or total_tokens > 8000:
        status = "WARNING (Acercándose al límite de directivas)"

    print(json.dumps({
        "rules_health_status": status,
        "files_scanned": [str(f) for f in rule_files],
        "total_estimated_rule_tokens": total_tokens,
        "total_imperative_directives": total_instructions,
        "ifscale_2_safe_ceiling": 250,
        "lint_findings": findings,
    }, indent=2, ensure_ascii=False))

def cmd_reset_session(_args: argparse.Namespace) -> None:
    state = load_state()
    render_handoff(state)
    m = load_metrics()
    m["invocation_count"] = 0
    m["consecutive_errors"] = 0
    m["stop_continuations"] = 0
    save_metrics(m)
    print(json.dumps({
        "status": "SESSION_PREPARED_FOR_RESET",
        "message": "Handoff CONCAT listo en .zen/handoff.md. Ejecuta '/clear' para recargar al 95% de precisión.",
        "handoff_file": str(HANDOFF_FILE),
    }, indent=2, ensure_ascii=False))

def cmd_worker(args: argparse.Namespace) -> None:
    root = find_project_root()
    workers_dir = root / ZEN_DIR / "workers"
    workers_dir.mkdir(parents=True, exist_ok=True)
    index_file = workers_dir / "workers_index.json"

    def load_index() -> dict:
        if index_file.exists():
            try:
                return json.loads(index_file.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def save_index(idx: dict) -> None:
        index_file.write_text(json.dumps(idx, indent=2, ensure_ascii=False), encoding="utf-8")

    index = load_index()
    now = get_iso_now()

    if args.worker_cmd == "create":
        job_id = args.id
        board_path = workers_dir / f"{job_id}.md"
        content = (
            f"# WORKER BOARD: {job_id}\n"
            f"* **Modelo Asignado:** {args.model or 'unassigned'}\n"
            f"* **Micro-Problema:** {args.target or 'General task'}\n"
            f"* **Invariantes del Worker:** {args.invariants or '100% PASS en suite de pruebas nativa'}\n"
            f"* **Estado:** RUNNING\n"
            f"* **Iniciado:** {now}\n"
        )
        board_path.write_text(content, encoding="utf-8")
        index[job_id] = {
            "job_id": job_id,
            "model": args.model,
            "target": args.target,
            "status": "RUNNING",
            "created_at": now,
            "board_file": str(board_path)
        }
        save_index(index)
        print(f"[ZEN] Pizarra satélite creada para worker '{job_id}' en {board_path}")

    elif args.worker_cmd == "complete":
        job_id = args.id
        if job_id in index:
            index[job_id]["status"] = "COMPLETED"
            index[job_id]["completed_at"] = now
            index[job_id]["evidence"] = args.evidence or ""
            save_index(index)
        board_path = workers_dir / f"{job_id}.md"
        if board_path.exists():
            txt = board_path.read_text(encoding="utf-8")
            txt = txt.replace("* **Estado:** RUNNING", "* **Estado:** COMPLETED")
            txt += f"\n* **Completado:** {now}\n* **Evidencia:** {args.evidence or 'Verificado'}\n"
            board_path.write_text(txt, encoding="utf-8")
        print(f"[ZEN] Worker '{job_id}' marcado como COMPLETED.")

    elif args.worker_cmd == "list":
        if not index:
            print("[ZEN] No hay pizarras satélite de workers activas.")
        else:
            print(f"[ZEN] {len(index)} Pizarras satélite registradas:")
            for jid, info in index.items():
                print(f"  - [{info.get('status')}] {jid} ({info.get('model')}): {info.get('target')}")

    elif args.worker_cmd == "show":
        job_id = args.id
        board_path = workers_dir / f"{job_id}.md"
        if board_path.exists():
            print(board_path.read_text(encoding="utf-8"))
        else:
            print(f"[ZEN] No se encontró pizarra satélite para '{job_id}'")

def main() -> None:
    parser = argparse.ArgumentParser(description="ZEN Engine: Pizarra Dinámica y Gobernanza Cognitiva.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("audit", help="Audita transcript y calcula CSI.")
    
    b_p = sub.add_parser("board", help="Gestiona Pizarra Dinámica.")
    b_p.add_argument("--show", action="store_true")
    b_p.add_argument("--goal", type=str)
    b_p.add_argument("--target", type=str)
    b_p.add_argument("--preconditions", type=str)
    b_p.add_argument("--verification-cmd", type=str)
    b_p.add_argument("--add-invariant", type=str)
    b_p.add_argument("--add-task", type=str)
    b_p.add_argument("--complete-task", type=str)
    b_p.add_argument("--evidence", type=str, default="")
    b_p.add_argument("--add-blocker", type=str)
    b_p.add_argument("--clear-blockers", action="store_true")
    b_p.add_argument("--add-dead-end", type=str, help="Registra enfoque descartado (Hipótesis: Razón)")

    cp_p = sub.add_parser("checkpoint", help="Guarda checkpoint CONCAT.")
    cp_p.add_argument("--goal", type=str)
    cp_p.add_argument("--completed", type=str)
    cp_p.add_argument("--next-step", type=str)
    cp_p.add_argument("--evidence", type=str, default="")
    cp_p.add_argument("--blockers", type=str)
    cp_p.add_argument("--dead-end", type=str, help="Registra enfoque descartado (Hipótesis: Razón)")

    mem_p = sub.add_parser("memory", help="Gestiona grafo de memoria causal.")
    mem_sub = mem_p.add_subparsers(dest="mem_command", required=True)
    m_add = mem_sub.add_parser("add")
    m_add.add_argument("--subject", type=str, required=True)
    m_add.add_argument("--predicate", type=str, required=True)
    m_add.add_argument("--object", type=str, required=True)
    m_add.add_argument("--why", type=str, default="")
    m_query = mem_sub.add_parser("query")
    m_query.add_argument("--term", type=str, required=True)
    mem_sub.add_parser("list")

    sub.add_parser("lint-rules", help="Audita reglas del proyecto.")
    sub.add_parser("reset-session", help="Genera handoff CONCAT.")

    w_p = sub.add_parser("worker", help="Gestiona pizarras satélite federadas para agentes y trabajadores remotos.")
    w_sub = w_p.add_subparsers(dest="worker_cmd", required=True)
    w_create = w_sub.add_parser("create", help="Crea una pizarra satélite para un worker.")
    w_create.add_argument("--id", type=str, required=True, help="ID único del worker/job")
    w_create.add_argument("--model", type=str, default="unassigned", help="Modelo asignado")
    w_create.add_argument("--target", type=str, default="", help="Micro-problema o foco")
    w_create.add_argument("--invariants", type=str, default="", help="Invariantes obligatorios")

    w_comp = w_sub.add_parser("complete", help="Marca una pizarra satélite como completada.")
    w_comp.add_argument("--id", type=str, required=True, help="ID del worker/job")
    w_comp.add_argument("--evidence", type=str, default="", help="Evidencia de verificación")

    w_sub.add_parser("list", help="Lista todas las pizarras satélite activas.")
    w_show = w_sub.add_parser("show", help="Muestra el contenido de una pizarra satélite.")
    w_show.add_argument("--id", type=str, required=True, help="ID del worker/job")

    args = parser.parse_args()
    if args.command == "audit": cmd_audit(args)
    elif args.command == "board": cmd_board(args)
    elif args.command == "checkpoint": cmd_checkpoint(args)
    elif args.command == "memory": cmd_memory(args)
    elif args.command == "lint-rules": cmd_lint_rules(args)
    elif args.command == "reset-session": cmd_reset_session(args)
    elif args.command == "worker": cmd_worker(args)

if __name__ == "__main__":
    main()
