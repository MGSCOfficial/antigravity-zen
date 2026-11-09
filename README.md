# Antigravity Zen 🧘

> **Dynamic Blackboard & Cognitive Hygiene Engine for Google Antigravity**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Compatibility](https://img.shields.io/badge/Antigravity-2.0+-emerald.svg)](https://github.com/MGSCOfficial/openbridge)

**Antigravity Zen** es un sistema agéntico avanzado diseñado para auditar, mitigar y erradicar el estrés cognitivo, la saturación de memoria de trabajo, los bucles de error (*looping hallucinations*) y la degradación progresiva de contexto (*Context Rot*) en **Google Antigravity**

Provee una arquitectura de **Pizarra Dinámica persistente fuera de contexto** (`.zen/blackboard.md`), consolidación de memoria CONCAT, hooks cognitivos automatizados y una interfaz CLI de alta velocidad (`zen.py`).

---

## ⚡ Sinergia con OpenBridge

Antigravity Zen es el complemento cognitivo ideal para [OpenBridge MCP](https://github.com/MGSCOfficial/openbridge):
* **OpenBridge** desvía las tareas mecánicas y pesadas de código hacia modelos satélites gratuitos ($0 cost).
* **Antigravity Zen** mantiene la ventana de contexto del agente principal limpia y protegida de la saturación, registrando el progreso de los workers en la Pizarra Dinámica sin contaminar la memoria conversacional.

---

## 🚀 Características Clave

1. **Pizarra Dinámica Fuera de Contexto (`.zen/blackboard.md`)**:
   - Persistencia determinista en disco que sobrevive al reinicio de sesiones y resúmenes de contexto.
   - Puntero de estado activo, objetivos inmediatos y registro de lecciones aprendidas.
2. **Mitigación de Bucles de Error (Regla de Oro de los 2 Fallos)**:
   - Detección inmediata de fallos consecutivos de herramientas para forzar pausas reflexivas y auditoría antes de continuar editando código a ciegas.
3. **Consolidación de Memoria CONCAT**:
   - Algoritmo de compactación estructurada que extrae decisiones arquitectónicas y descarta texto conversacional efímero.
4. **Motor CLI `zen.py`**:
   - Interfaz de comandos ultrarrápida en Python:
     ```bash
     python scripts/zen.py init       # Inicializa la pizarra .zen/ en el workspace
     python scripts/zen.py status     # Auditoría de estado cognitivo y métricas
     python scripts/zen.py post "..." # Publica un hito o cambio de estado
     python scripts/zen.py audit      # Inspección adversaria de estabilidad
     ```
5. **Statuslines Reactivas**:
   - Integración nativa para consolas PowerShell (`zen-statusline.ps1`) y Bash (`zen-statusline.sh`).

---

## 📦 Estructura del Repositorio

```
antigravity-zen/
├── SKILL.md                          # Instrucciones y directrices operativas
├── plugin.json                       # Manifiesto de integración para Antigravity
├── scripts/
│   ├── zen.py                        # CLI de gestión de pizarra dinámica
│   ├── cognitive_hooks.py            # Ganchos de análisis de deriva cognitiva
│   ├── test_zen.py                   # Suite de pruebas unitarias
│   ├── zen-statusline.ps1            # Indicador de estado en terminal PowerShell
│   └── zen-statusline.sh             # Indicador de estado en terminal Bash
├── templates/
│   ├── blackboard_template.md        # Plantilla inicial de pizarra de trabajo
│   └── handoff_template.md           # Plantilla de transferencia entre agentes
└── references/
    ├── model_playbooks.md            # Guías de comportamiento por modelo
    └── multi_model_satellite_architecture.md
```

---

## 🛠️ Instalación y Uso

### 1. Como Skill Global de Agente
Copia la carpeta `antigravity-zen` dentro de tu directorio de skills agénticas:
* **Windows**: `C:\Users\<USUARIO>\.agents\skills\antigravity-zen\`

### 2. Uso en Turno Agéntico
Invoca `/antigravity-zen` o el comando `/zen-reset` en el chat cuando una sesión supere los 8-10 turnos o tras detectar divergencias técnicas.

---

## 👤 Autor y Licencia

* **Desarrollo y Arquitectura**: **MGSC** ([@MGSCOfficial](https://github.com/MGSCOfficial))
* **Licencia**: Código abierto bajo la licencia [MIT](LICENSE).
