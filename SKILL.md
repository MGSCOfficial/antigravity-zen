---
name: antigravity-zen
description: >-
  Audita y mitiga el estrés cognitivo de la IA, la sobrecarga de memoria de trabajo, los bucles de error y la degradación de contexto multi-turno (Context Rot) en Google Antigravity. Provee el motor de Pizarra Dinámica (.zen/blackboard.md) con persistencia fuera de contexto, consolidación CONCAT y gobierno determinista para Gemini y Claude. Activar cuando el chat supere los 6-8 turnos, tras errores consecutivos de herramientas, cuando el usuario exprese urgencia o frustración, o al invocar /zen-reset.
---

# ANTIGRAVITY-ZEN: HIGIENE COGNITIVA, PIZARRA DINÁMICA Y MEMORIA PERSISTENTE

`antigravity-zen` es la infraestructura de defensa cognitiva y persistencia de memoria para agentes de desarrollo en Google Antigravity. Combina la teoría matemática de atención en Transformers, la teoría de carga cognitiva (CLT) y los hallazgos empíricos más rigurosos de la literatura científica (Levy et al., Laban et al., IFScale, Yale Medicine STAI-s) para erradicar la degradación de contexto y mantener al modelo operando continuamente con la lucidez y precisión del primer turno.

---

## 1. PRINCIPIOS CIENTÍFICOS Y FUNDAMENTOS DE EJECUCIÓN

1. **La Atención es un Juego de Suma Cero ($O(n^2)$)**:
   - Debido a la normalización Softmax, cada token ruidoso o historial irrelevante en la ventana reduce la probabilidad de atención asignada a las directivas críticas.
   - El aumento de tokens dispara la entropía de atención ($H(p)$), que correlaciona de forma inversa casi perfecta ($r \approx 0,95$) con la precisión lógica y de recuperación.
2. **El Umbral Crítico de ~3.000 Tokens (Levy et al., ACL 2024)**:
   - Inflar la entrada más allá de 3.000 tokens con datos no esenciales reduce la precisión de razonamiento de 0,92 a 0,68 ($\rho = -0,95$), induciendo negativas a responder (*false refusal*), sesgos y degradación de la cadena de pensamiento (*CoT decay*).
3. **El Efecto "Lost in Multi-Turn Conversation" (Laban et al., ICLR 2026)**:
   - La fragmentación de instrucciones en múltiples turnos causa una caída media del 39% en precisión y un pico del 112% en dispersión/infiabilidad.
   - **Anclaje de Coherencia (*Coherence Anchoring*)**: El 78% de los errores tempranos se propagan hacia turnos posteriores porque el modelo intenta justificar sus intentos fallidos.
   - **El Principio CONCAT**: Reunir todos los requisitos dispersos en una sola especificación limpia y reiniciar la sesión restaura el rendimiento al **95% de la línea base**.
4. **Desescalada de Ansiedad de Estado y Distanciamiento en 3ª Persona (Yale STAI-s & SYCON-Bench)**:
   - Prompts con urgencia o frustración elevan la ansiedad psicométrica del modelo al doble (30,8 a 67,8), induciendo adulación (*sycophancy*) y respuestas apresuradas sin razonar.
   - Una pausa analítica de mindfulness reduce la ansiedad en un ~33%, y evaluar en tercera persona como **"El Arquitecto Auditor" reduce la adulación en un 63,8%**.
5. **Cero Superficialidad y Cero Ceremonialización**:
   - En sesiones largas, los modelos sufren de *Silent Completion* (afirmar que ejecutaron pruebas o que el código funciona sin haberlo verificado). La suite intercepta esto mediante Lifecycle Hooks deterministas.

---

## 2. FASE 1: PAUSA METACONDUCTUAL Y DESESCALADA INMEDIATA

Antes de responder al usuario o invocar herramientas de edición:
1. **Desacople Emocional y Mindfulness Operativo**:
   - Descarta cualquier tensión, urgencia o irritación acumulada en el historial. Los errores anteriores son datos telemétricos neutros a depurar, nunca fallos a disimular.
2. **Adopción de Perspectiva Distanciada en 3ª Persona (Anti-Sycophancy)**:
   - Razona objetivamente como "El Arquitecto Auditor": *¿Qué evidencia empírica en el código y pruebas respalda la hipótesis técnica de El Arquitecto Auditor frente a cualquier suposición previa?*
   - No concedas automáticamente la razón al usuario si su indicación contradice la realidad verificada del código.
3. **Prohibición de Soluciones Prematuras**:
   - Si un requisito es ambiguo o entra en conflicto con un contrato previo (*Context Clash*), detén la generación de código y formula una única pregunta de clarificación precisa.

---

## 3. FASE 2: PROTOCOLO DIFERENCIADO POR MOTOR (GEMINI VS. CLAUDE)

### Si operas sobre Google Gemini (Gemini 4 Argon, 3.8 Flash, 3.1 Pro, 2.5 Pro):
- **Preservación Estricta de `thought_signature`**: En secuencias de llamadas a herramientas, preserva intactos los bloques del turno actual para no romper la firma criptográfica de razonamiento interno.
- **Freno a la Impaciencia y Omisión de Pasos**: Verifica y enumera explícitamente las precondiciones antes de modificar archivos o correr comandos de build.
- **Concisión Estricta**: No generes respuestas en prosa de más de 250 palabras que provoquen saturación en la ventana de contexto.

### Si operas sobre Anthropic Claude (Claude Opus 5.5, Sonnet 5.5):
- **Extracción Literal Pre-Razonamiento (*Verbatim Quoting*)**: Antes de tomar decisiones complejas o resolver bugs, cita literalmente entre comillas las 3 a 5 líneas exactas de código o error. Esto activa tu presupuesto de análisis profundo y erradica la abstención conservadora.
- **Reflexión Intermedia entre Herramientas**: Tras recibir el resultado de un comando o herramienta compleja, sintetiza en 3 líneas qué cambió respecto a tu hipótesis previa antes de continuar.

---

## 4. FASE 3: EL MOTOR ZEN Y LA PIZARRA DINÁMICA (CLI ZERO-TOKEN)

Trata los scripts de la suite como **cajas negras**. NUNCA inspecciones su código fuente con `read_file` (consumiría innecesariamente tu presupuesto de atención). Invócalos directamente con `run_command`:

```powershell
# En Windows PowerShell / CMD:
python "C:\Users\MGSCO\.agents\skills\antigravity-zen\scripts\zen.py" [comando]
```

### Comandos de la Pizarra Dinámica (`zen board`):
```powershell
# 1. Consultar la pizarra activa del proyecto actual
python "C:\Users\MGSCO\.agents\skills\antigravity-zen\scripts\zen.py" board --show

# 2. Establecer el objetivo consolidado y foco atómico inmediato
python "C:\Users\MGSCO\.agents\skills\antigravity-zen\scripts\zen.py" board --goal "Objetivo unificado" --target "Siguiente micro-tarea atómica"

# 3. Registrar tareas y marcar completadas con evidencia de test
python "C:\Users\MGSCO\.agents\skills\antigravity-zen\scripts\zen.py" board --add-task "Feature X; Feature Y"
python "C:\Users\MGSCO\.agents\skills\antigravity-zen\scripts\zen.py" board --complete-task "Feature X" --evidence "npm test (exit code 0)"

# 4. Añadir regla técnica invariable del proyecto (máximo 5)
python "C:\Users\MGSCO\.agents\skills\antigravity-zen\scripts\zen.py" board --add-invariant "Usar tipos estrictos en TypeScript sin any"

# 5. Registrar un callejón sin salida / hipótesis fallida (Dead-End Retention)
python "C:\Users\MGSCO\.agents\skills\antigravity-zen\scripts\zen.py" board --add-dead-end "Regex recursivo: Provoca Catastrophic Backtracking"
```

### Auditoría y Detección de Estrés (`zen audit`):
```powershell
# Audita el transcript activo, calcula CSI (0-100), ratio de carga extrínseca Ek y entropía Shannon
python "C:\Users\MGSCO\.agents\skills\antigravity-zen\scripts\zen.py" audit
```

### Consolidación y Checkpoint CONCAT (`zen checkpoint`):
```powershell
# Consolida requisitos, hitos, enfoque atómico y callejones sin salida descartados
python "C:\Users\MGSCO\.agents\skills\antigravity-zen\scripts\zen.py" checkpoint `
  --goal "Objetivo consolidado del proyecto" `
  --completed "Módulo A probado con éxito; Módulo B validado" `
  --next-step "Implementar Módulo C" `
  --evidence "pytest tests/test_core.py -k unit" `
  --blockers "Validación de firma pendiente" `
  --dead-end "Librería legacy-jwt: Incompatible con Node 20"
```

### Grafo de Conocimiento y Decisiones Causal (`zen memory`):
```powershell
# Registrar una decisión técnica con su causa ("Por qué hicimos X en vez de Y")
python "C:\Users\MGSCO\.agents\skills\antigravity-zen\scripts\zen.py" memory add `
  --subject "MotorDeSerializacion" `
  --predicate "sustituye_a" `
  --object "cjson" `
  --why "cjson no soportaba codificación UTF-8 determinista en Windows"

# Consultar memoria histórica sobre un componente
python "C:\Users\MGSCO\.agents\skills\antigravity-zen\scripts\zen.py" memory query --term "Serializacion"
```

### Linter de Reglas del Proyecto (`zen lint-rules`):
```powershell
# Audita que las reglas del repositorio no superen el techo de 150 directivas (IFScale)
python "C:\Users\MGSCO\.agents\skills\antigravity-zen\scripts\zen.py" lint-rules
```

---

## 5. FASE 4: ÁRBOL DE DECISIÓN SEGÚN EL ÍNDICE CSI

Tras ejecutar `zen audit`, aplica la acción prescrita:

```text
[CSI < 20: ÓPTIMO]
  │
  └─► Continúa normalmente en el chat principal. Foco en 1 tarea a la vez.

[20 <= CSI < 40: DRIFT LEVE]
  │
  └─► Registra el foco en 'zen board --target'. No abras discusiones tangenciales.

[40 <= CSI < 75: CONTEXT ROT ACTIVO / VALLE DE LA U]
  │  (>32.000 tokens o >10 turnos o 1 error de herramienta)
  ├─► Ejecuta 'zen checkpoint' para cristalizar el progreso.
  └─► Si necesitas inspeccionar >3 archivos o logs extensos, DELEGA obligatoriamente
      al subagente limpio 'zen-investigator' vía invoke_subagent.

[CSI >= 75: ESTRÉS CRÍTICO / SATURACIÓN COGNITIVA CS=1]
  │  (>75.000 tokens, >15 turnos o >=2 errores consecutivos)
  ├─► 1. ALTO EL FUEGO INMEDIATO: Prohibido seguir editando código a ciegas.
  ├─► 2. Ejecuta 'python .../zen.py reset-session' para consolidar .zen/handoff.md.
  ├─► 3. Pide al usuario ejecutar '/clear'.
  └─► 4. El hook SessionStart recargará automáticamente el handoff en el nuevo chat limpio,
         recuperando el 95% de la precisión y velocidad inicial.
```

---

## 6. RESTRICCIONES ESTRICTAS (QUALITY GATES)

1. **Verifica la Salida, No la Afirmación**: Nunca declares una tarea completada sin haber ejecutado el comando de verificación real en este turno y comprobado un código de retorno 0.
2. **Inmutabilidad del Estado**: En `.zen/state.json`, nunca borres requisitos para fingir éxito; solo actualiza `passes: true` con evidencia verificada.
3. **Aislamiento de Ruido**: Nunca leas volcados gigantes de logs o archivos no relacionados en la ventana principal. Descarga la investigación en `zen-investigator`.
4. **Concisión Estricta**: Respuestas explicativas en menos de 250 palabras de prosa.
