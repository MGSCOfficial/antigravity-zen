# ARQUITECTURA SATÉLITE MULTI-MODELO PARA ANTIGRAVITY-ZEN (PIZARRAS FEDERADAS)

**Fecha de Especificación:** 2026-11-08  
**Autor:** `AGENT-SYSTEM-ARCHITECT`  
**Compatibilidad:** Antigravity Zen v1.0 & v1.1 Standalone + OpenBridge Multi-Agent

---

## 1. El Principio de Invarianza: Independencia Absoluta de Zen

Antigravity Zen fue diseñada como una suite de higiene cognitiva universal sustentada en la literatura de atención de Transformers y Carga Cognitiva (Levy et al., Laban et al.).

> [!IMPORTANT]
> **Regla de Oro de Desacoplamiento**:  
> `antigravity-zen` **NUNCA** debe depender de OpenBridge, OpenCode ni ningún proveedor externo. Si un usuario descarga o clona la carpeta `antigravity-zen`, debe funcionar de forma autónoma, limpia y completa en cualquier proyecto utilizando únicamente su motor CLI nativo (`zen.py`).

---

## 2. El Desafío del Multi-Modelo: Por qué una sola pizarra colapsa

En una sesión mono-modelo (Gemini 3.8 o Claude 3.7):
* Una única Pizarra Dinámica (`.zen/blackboard.md`) almacena:
  - Objetivo consolidado
  - Foco atómico inmediato (`active_target`)
  - Tareas pendientes y completadas con evidencia
  - Invariantes técnicas (máximo 5)
  - Callejones sin salida (*dead-ends*) descartados

Si 3 modelos externos (ej. Nemotron 3.5 en tests, DeepSeek en scaffolding y Gemma en validación) intentan leer y escribir en esa misma pizarra:
1. **Colisión de Foco (*Target Clash*)**: El campo `active_target` cambiaría erráticamente entre lo que hace el worker A y el worker B.
2. **Contaminación de Contexto (*Context Pollution*)**: Los logs de error temporales de un worker invadirían la memoria del agente principal, elevando artificialmente el índice de estrés cognitivo (CSI).
3. **Desalineación de Directivas**: Modelos de diferente tamaño de ventana interpretarían los invariantes globales de formas divergentes.

---

## 3. La Solución: Pizarras Federadas (Maestra y Satélites)

Para preservar la lucidez de la IA principal sin sobrecargar el sistema, se implementa el modelo de **Pizarras Satélite**:

```
                         ┌────────────────────────────────────────┐
                         │      PIZARRA MAESTRA (Project Root)    │
                         │          .zen/blackboard.md            │
                         │    (Gobernada solo por Gemini 3.8)     │
                         └───────────────────┬────────────────────┘
                                             │
                       ┌─────────────────────┴─────────────────────┐
                       │                                           │
          (Despacho Worker A)                         (Despacho Worker B)
                       │                                           │
         ┌─────────────▼───────────────┐             ┌─────────────▼───────────────┐
         │     PIZARRA SATÉLITE A      │             │     PIZARRA SATÉLITE B      │
         │  .zen/workers/job_01.md     │             │  .zen/workers/job_02.md     │
         │ (Nemotron 3.5 - Tests P01)  │             │ (DeepSeek - DTOs P02)       │
         └─────────────┬───────────────┘             └─────────────┬───────────────┘
                       │                                           │
                       └─────────────────────┬─────────────────────┘
                                             │ (Consolidación CONCAT al concluir)
                                             ▼
                         ┌────────────────────────────────────────┐
                         │   Actualización de Tarea Verificada    │
                         │   en Pizarra Maestra (.zen/state.json) │
                         └────────────────────────────────────────┘
```

### Estructura de una Pizarra Satélite (`.zen/workers/{job_id}.md`):
Una sub-pizarra satélite es ultra-compacta (<100 tokens de directivas) y solo contiene:
```markdown
# WORKER BOARD: [job_id]
* **Modelo Asignado:** opencode/nemotron-3.5-lightning-free
* **Micro-Problema:** P01 - Generación de Tests de Autenticación
* **Entorno Aislado:** .scratch/sandbox_job_01/
* **Invariantes del Worker:** 100% PASS en 'npm test', cero dependencias no autorizadas.
* **Estado:** RUNNING | COMPLETED
```

### Protocolo de Consolidación (Zero-Leakage):
1. El Agente Principal despacha el job asíncrono con `openbridge_start_task`.
2. Se genera la sub-pizarra efímera en `.zen/workers/{job_id}.md`.
3. El worker en OpenCode trabaja en su sandbox aislado.
4. Al completarse exitosamente con código de retorno 0, el mediador:
   - Extrae el entregable y el diff verificado.
   - Invoca: `zen.py board --complete-task "P01" --evidence "Worker Nemotron 3.5 exit code 0"`.
   - Elimina o archiva `.zen/workers/{job_id}.md`.
5. La Pizarra Maestra de Antigravity permanece limpia, pura y sin residuos de atención.
