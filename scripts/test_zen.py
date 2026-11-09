#!/usr/bin/env python3
"""
test_zen.py - Suite Completa de Pruebas Automatizadas para antigravity-zen.
Valida el motor zen.py (CSI 2.0), la pizarra dinámica, el grafo de memoria,
el linter IFScale y los Lifecycle Hooks de cognitive_hooks.py.
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

# Import modules under test
import zen
import cognitive_hooks


class TestZenSuite(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="zen_test_")
        self.old_cwd = os.getcwd()
        os.chdir(self.test_dir)

        # Point zen and hooks paths to test_dir
        self.zen_dir = Path(".zen")
        self.zen_dir.mkdir(parents=True, exist_ok=True)
        zen.ZEN_DIR = self.zen_dir
        zen.STATE_FILE = self.zen_dir / "state.json"
        zen.BLACKBOARD_FILE = self.zen_dir / "blackboard.md"
        zen.HANDOFF_FILE = self.zen_dir / "handoff.md"
        zen.METRICS_FILE = self.zen_dir / "runtime_metrics.json"
        zen.GRAPH_FILE = self.zen_dir / "knowledge_graph.json"

        cognitive_hooks.ZEN_DIR = self.zen_dir
        cognitive_hooks.STATE_FILE = self.zen_dir / "state.json"
        cognitive_hooks.HANDOFF_FILE = self.zen_dir / "handoff.md"
        cognitive_hooks.METRICS_FILE = self.zen_dir / "runtime_metrics.json"

    def tearDown(self):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_compute_csi_thresholds(self):
        """Verifica la calibración del Índice de Estrés Cognitivo CSI 2.0 para Gemini 3.8 Flash."""
        # 1. Caso Óptimo: 5k tokens, 2 turnos, 0 errores
        stats_opt = {
            "estimated_tokens": 5000,
            "turns": 2,
            "consecutive_errors": 0,
            "total_chars": 20000,
            "tool_result_chars": 1000,
        }
        csi, status = zen.compute_csi(stats_opt)
        self.assertLess(csi, 20)
        self.assertIn("ÓPTIMO", status)

        # 2. Caso Drift Leve: 50k tokens, 14 turnos (Valle U en Gemini 3.8)
        stats_drift = {
            "estimated_tokens": 50000,
            "turns": 14,
            "consecutive_errors": 0,
            "total_chars": 200000,
            "tool_result_chars": 30000,
        }
        csi, status = zen.compute_csi(stats_drift)
        self.assertTrue(20 <= csi < 40)
        self.assertIn("LEVE", status)

        # 3. Caso Context Rot: 90k tokens, 19 turnos
        stats_rot = {
            "estimated_tokens": 90000,
            "turns": 19,
            "consecutive_errors": 0,
            "total_chars": 360000,
            "tool_result_chars": 50000,
        }
        csi, status = zen.compute_csi(stats_rot)
        self.assertTrue(40 <= csi < 75)
        self.assertIn("Context Rot", status)

        # 4. Caso Crítico: 150k tokens, 26 turnos, 2 errores
        stats_crit = {
            "estimated_tokens": 150000,
            "turns": 26,
            "consecutive_errors": 2,
            "total_chars": 600000,
            "tool_result_chars": 400000,
        }
        csi, status = zen.compute_csi(stats_crit)
        self.assertGreaterEqual(csi, 75)
        self.assertIn("CRÍTICO", status)

    def test_board_lifecycle(self):
        """Valida la creación y actualización de la Pizarra Dinámica."""
        class MockArgs:
            show = False
            goal = "Construir motor de trading cuántico"
            target = "Implementar parser FIX v4.4"
            preconditions = "Protocolo socket TCP activo"
            verification_cmd = "pytest tests/test_fix.py"
            add_invariant = "Cero excepciones no tipadas; Latencia < 5ms"
            add_task = "Conexión SSL; Heartbeat 30s; Parser FIX"
            complete_task = "Conexión SSL"
            evidence = "pytest tests/test_ssl.py (exit code 0)"
            add_blocker = "Desconexión aleatoria en socket mock"
            clear_blockers = False
            add_dead_end = None

        zen.cmd_board(MockArgs())

        self.assertTrue(zen.STATE_FILE.exists())
        self.assertTrue(zen.BLACKBOARD_FILE.exists())

        state = zen.load_state()
        self.assertEqual(state["project_goal"], "Construir motor de trading cuántico")
        self.assertEqual(state["active_target"], "Implementar parser FIX v4.4")
        self.assertEqual(len(state["invariants"]), 2)

        passing = [f for f in state["features"] if f["passes"]]
        pending = [f for f in state["features"] if not f["passes"]]
        self.assertEqual(len(passing), 1)
        self.assertEqual(len(pending), 2)
        self.assertEqual(passing[0]["evidence_cmd"], "pytest tests/test_ssl.py (exit code 0)")

        # Verificar renderizado en Markdown de la pizarra
        bb_text = zen.BLACKBOARD_FILE.read_text(encoding="utf-8")
        self.assertIn("ZEN DYNAMIC BLACKBOARD", bb_text)
        self.assertIn("Construir motor de trading cuántico", bb_text)
        self.assertIn("🎯 **Implementar parser FIX v4.4**", bb_text)
        self.assertIn("- [x] Conexión SSL", bb_text)
        self.assertIn("- [ ] Heartbeat 30s", bb_text)
        self.assertIn("- [!] Desconexión aleatoria en socket mock", bb_text)

    def test_checkpoint_and_handoff_concat(self):
        """Valida el protocolo CONCAT y la generación de handoff ultracompacto."""
        class MockArgs:
            goal = "API REST de autenticación OAuth2"
            completed = "Endpoints /token y /auth"
            next_step = "Implementar Refresh Token rotation"
            evidence = "go test ./auth/... -v"
            blockers = "Validación de firma JWT asimétrica pendiente"
            dead_end = None

        zen.cmd_checkpoint(MockArgs())

        self.assertTrue(zen.HANDOFF_FILE.exists())
        handoff_text = zen.HANDOFF_FILE.read_text(encoding="utf-8")

        self.assertIn("ZEN CONTEXT HANDOFF (SINGLE-BLOCK CONCAT SPECIFICATION)", handoff_text)
        self.assertIn("- [x] Endpoints /token y /auth", handoff_text)
        self.assertIn("- [ ] Implementar Refresh Token rotation", handoff_text)
        self.assertIn("- [!] Validación de firma JWT asimétrica pendiente", handoff_text)

        # Validar presupuesto de tokens: debe ser conciso (<400 tokens / <1600 caracteres)
        self.assertLess(len(handoff_text), 1600)

    def test_knowledge_graph_memory(self):
        """Valida el registro y consulta del grafo de conocimiento causal."""
        class MockAddArgs:
            mem_command = "add"
            subject = "PostgreSQL"
            predicate = "seleccionado_sobre"
            object = "MongoDB"
            why = "Requerimiento estricto de transacciones ACID para balances bancarios"

        zen.cmd_memory(MockAddArgs())

        kg = zen.load_knowledge_graph()
        self.assertEqual(len(kg), 1)
        self.assertEqual(kg[0]["subject"], "PostgreSQL")
        self.assertIn("ACID", kg[0]["why"])

        # Consulta
        class MockQueryArgs:
            mem_command = "query"
            term = "PostgreSQL"

        zen.cmd_memory(MockQueryArgs())

    def test_hooks_session_start(self):
        """Valida que SessionStart inyecte el handoff previo vía systemMessage."""
        zen.HANDOFF_FILE.write_text("# Test Handoff\n- [x] Feature 1", encoding="utf-8")

        payload = {"conversationId": "test_conv_123"}
        out = cognitive_hooks.handle_session_start(payload)

        self.assertIn("injectSteps", out)
        steps = out["injectSteps"]
        self.assertEqual(len(steps), 1)
        sys_msg = steps[0]["systemMessage"]["systemMessage"]
        self.assertIn("[ANTIGRAVITY-ZEN SESSION HANDOFF RESTORED]", sys_msg)
        self.assertIn("# Test Handoff", sys_msg)

    def test_hooks_pre_invocation(self):
        """Valida que PreInvocation inyecte anclas efímeras en la zona de recencia."""
        # Caso 1: Chat limpio, sin errores ni estrés -> Vacío (ahorro de tokens)
        payload_clean = {
            "conversationId": "test_conv_123",
            "modelName": "gemini-3.8-flash",
            "invocationNum": 2,
            "lastUserInput": "Crea la función sumar",
        }
        out_clean = cognitive_hooks.handle_pre_invocation(payload_clean)
        self.assertEqual(out_clean, {})

        # Caso 2: Usuario con frustración o estrés -> Ancla inmediata con mindfulness y 3ª persona
        payload_stressed = {
            "conversationId": "test_conv_123",
            "modelName": "gemini-3.8-flash",
            "invocationNum": 3,
            "lastUserInput": "WTF sigue roto, deja de inventar otra vez mal!",
        }
        out_stressed = cognitive_hooks.handle_pre_invocation(payload_stressed)
        self.assertIn("injectSteps", out_stressed)
        eph = out_stressed["injectSteps"][0]["ephemeralMessage"]
        self.assertIn("DESESCALADA Y MINDFULNESS", eph)
        self.assertIn("DISTANCIAMIENTO EN 3ª PERSONA", eph)
        self.assertIn("PROTOCOLO GEMINI", eph)

        # Caso 3: Modelo Claude con >12 turnos -> Directiva específica de extracción literal
        payload_claude = {
            "conversationId": "test_conv_123",
            "modelName": "claude-sonnet-5-5",
            "invocationNum": 14,
            "lastUserInput": "Continuemos con el módulo",
        }
        out_claude = cognitive_hooks.handle_pre_invocation(payload_claude)
        self.assertIn("injectSteps", out_claude)
        eph_claude = out_claude["injectSteps"][0]["ephemeralMessage"]
        self.assertIn("PROTOCOLO CLAUDE (EXTRACCIÓN LITERAL)", eph_claude)

    def test_hooks_circuit_breaker(self):
        """Valida el cortafuegos de cascada (Circuit Breaker) tras 2 fallos consecutivos."""
        metrics = cognitive_hooks.load_metrics("test_conv_123")
        metrics["consecutive_errors"] = 2
        cognitive_hooks.save_metrics(metrics)

        # Intento de edición destructiva -> DENY
        payload_write = {
            "conversationId": "test_conv_123",
            "toolCall": {"name": "write_file", "args": {"Path": "src/app.py"}},
        }
        out_deny = cognitive_hooks.handle_pre_tool(payload_write)
        self.assertEqual(out_deny.get("decision"), "deny")
        self.assertIn("CIRCUIT BREAKER", out_deny.get("reason", ""))

        # Herramienta de lectura segura -> ALLOW
        payload_read = {
            "conversationId": "test_conv_123",
            "toolCall": {"name": "read_file", "args": {"Path": "src/app.py"}},
        }
        out_allow = cognitive_hooks.handle_pre_tool(payload_read)
        self.assertEqual(out_allow.get("decision"), "allow")

        # Invocación de zen.py -> ALLOW
        payload_zen = {
            "conversationId": "test_conv_123",
            "toolCall": {"name": "run_command", "args": {"CommandLine": "python zen.py audit"}},
        }
        out_zen = cognitive_hooks.handle_pre_tool(payload_zen)
        self.assertEqual(out_zen.get("decision"), "allow")

    def test_hooks_stop_gate_anti_ceremonialization(self):
        """Valida la puerta Stop anti-ceremonialización si hubo edición de código sin test."""
        # 1. Agente editó código
        payload_post_edit = {
            "conversationId": "test_conv_123",
            "toolCall": {"name": "write_file", "args": {"Path": "src/main.py"}},
            "error": "",
        }
        cognitive_hooks.handle_post_tool(payload_post_edit)

        # 2. Agente intenta parar sin correr test
        payload_stop = {
            "conversationId": "test_conv_123",
            "terminationReason": "model_stop",
            "fullyIdle": True,
        }
        out_stop = cognitive_hooks.handle_stop_gate(payload_stop)
        self.assertEqual(out_stop.get("decision"), "continue")
        self.assertIn("ANTI-CEREMONIALIZATION GATE", out_stop.get("reason", ""))

        # 3. Agente corre tests reales exitosos
        payload_post_test = {
            "conversationId": "test_conv_123",
            "toolCall": {"name": "run_command", "args": {"CommandLine": "pytest tests/"}},
            "error": "",
        }
        cognitive_hooks.handle_post_tool(payload_post_test)

        # 4. Agente ahora puede detenerse legítimamente
        out_stop_ok = cognitive_hooks.handle_stop_gate(payload_stop)
        self.assertEqual(out_stop_ok.get("decision"), "allow_stop")

    def test_project_isolation(self):
        """Valida que cada proyecto mantenga su propio estado y pizarra de forma 100% aislada."""
        proj_alpha = Path(self.test_dir) / "project_alpha"
        proj_beta = Path(self.test_dir) / "project_beta"
        proj_alpha.mkdir()
        proj_beta.mkdir()
        (proj_alpha / ".git").mkdir()
        (proj_beta / ".git").mkdir()

        # Configurar Alpha
        os.chdir(proj_alpha)
        class AlphaArgs:
            show = False
            goal = "Objetivo Alpha Único"
            target = "Target Alpha"
            preconditions = "Ninguna"
            verification_cmd = "pytest tests/alpha"
            add_invariant = "Invariant Alpha"
            add_task = "Task Alpha"
            complete_task = None
            evidence = ""
            add_blocker = None
            clear_blockers = False
            add_dead_end = None

        zen.cmd_board(AlphaArgs())
        self.assertTrue((proj_alpha / ".zen" / "blackboard.md").exists())
        self.assertFalse((proj_beta / ".zen").exists())

        # Configurar Beta
        os.chdir(proj_beta)
        class BetaArgs:
            show = False
            goal = "Objetivo Beta Único"
            target = "Target Beta"
            preconditions = "Ninguna"
            verification_cmd = "pytest tests/beta"
            add_invariant = "Invariant Beta"
            add_task = "Task Beta"
            complete_task = None
            evidence = ""
            add_blocker = None
            clear_blockers = False
            add_dead_end = None

        zen.cmd_board(BetaArgs())
        self.assertTrue((proj_beta / ".zen" / "blackboard.md").exists())

        # Verificar contenido aislado
        alpha_bb = (proj_alpha / ".zen" / "blackboard.md").read_text(encoding="utf-8")
        beta_bb = (proj_beta / ".zen" / "blackboard.md").read_text(encoding="utf-8")

        self.assertIn("Objetivo Alpha Único", alpha_bb)
        self.assertNotIn("Objetivo Beta Único", alpha_bb)

        self.assertIn("Objetivo Beta Único", beta_bb)
        self.assertNotIn("Objetivo Alpha Único", beta_bb)

        # Regresar a test_dir
        os.chdir(self.test_dir)

    def test_discarded_dead_ends(self):
        """Valida el registro y persistencia de hipótesis fallidas en la Pizarra y Handoff."""
        class MockDeadEndArgs:
            show = False
            goal = "Refactorización de motor AST"
            target = "Parser de expresiones lambdas"
            preconditions = "Gramática BNF compilada"
            verification_cmd = "pytest tests/test_ast.py"
            add_invariant = "Cero recursión infinita"
            add_task = "AST Lexer; AST Parser"
            complete_task = "AST Lexer"
            evidence = "pytest tests/test_lexer.py"
            add_blocker = None
            clear_blockers = False
            add_dead_end = "Regex recursivo: Provoca Catastrophic Backtracking en expresiones anidadas; Algoritmo Earley: Demasiado lento O(n^3) para streaming"

        zen.cmd_board(MockDeadEndArgs())

        state = zen.load_state()
        self.assertEqual(len(state.get("discarded_dead_ends", [])), 2)
        hypotheses = [d["hypothesis"] for d in state["discarded_dead_ends"]]
        self.assertIn("Regex recursivo", hypotheses)
        self.assertIn("Algoritmo Earley", hypotheses)

        # Verificar render en Pizarra
        bb_text = zen.BLACKBOARD_FILE.read_text(encoding="utf-8")
        self.assertIn("ENFOQUES DESCARTADOS / DEAD ENDS", bb_text)
        self.assertIn("❌ **Regex recursivo**", bb_text)
        self.assertIn("❌ **Algoritmo Earley**", bb_text)

        # Verificar render en Handoff
        handoff_text = zen.HANDOFF_FILE.read_text(encoding="utf-8")
        self.assertIn("Discarded Dead Ends (PROHIBITED APPROACHES - DO NOT RETRY)", handoff_text)
        self.assertIn("❌ **Regex recursivo**", handoff_text)

    def test_extraneous_load_and_shannon_entropy(self):
        """Valida el cálculo de entropía de Shannon y ratio de carga extrínseca Ek."""
        # 1. Texto variado -> Alta entropía léxica
        rich_corpus = [
            "arquitectura", "modular", "concurrencia", "latencia", "protocolo",
            "asíncrono", "persistencia", "particionamiento", "sharding", "consistencia",
            "transacción", "aislamiento", "optimización", "algoritmo", "complejidad",
            "memoria", "rendimiento", "verificación", "cobertura", "determinismo",
        ] * 3
        h_high = zen.compute_shannon_entropy(rich_corpus)
        self.assertGreater(h_high, 4.0)

        # 2. Texto repetitivo (colapso léxico en IA estresada) -> Baja entropía
        collapsed_corpus = ["disculpas", "error", "reintentar", "error"] * 25
        h_low = zen.compute_shannon_entropy(collapsed_corpus)
        self.assertLess(h_low, 2.5)

    def test_direct_reads_warning_hook(self):
        """Valida que tras >=8 lecturas directas se alerte sobre sobrecarga de working memory."""
        metrics = cognitive_hooks.load_metrics("test_conv_reads")
        metrics["direct_reads_count"] = 8
        cognitive_hooks.save_metrics(metrics)

        payload = {
            "conversationId": "test_conv_reads",
            "modelName": "gemini-3.8-flash",
            "invocationNum": 2,
            "lastUserInput": "¿Qué hace el archivo 9?",
        }
        out = cognitive_hooks.handle_pre_invocation(payload)
        self.assertIn("injectSteps", out)
        eph = out["injectSteps"][0]["ephemeralMessage"]
        self.assertIn("SUGERENCIA DE EFICIENCIA", eph)
        self.assertIn("zen-explorer", eph)


if __name__ == "__main__":
    unittest.main()
