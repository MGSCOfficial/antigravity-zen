# Playbooks de Mitigación Técnica por Modelo (Frontera Noviembre 2026)

## 1. Google Gemini 3.8 Flash (`gemini-3.8-flash`)
- **Rol en Antigravity**: Modelo predeterminado de alta velocidad (302 tokens/s).
- **Ventana y Caché**: 1.048.576 tokens entrada, 65.536 salida. Caché implícita automática activa a partir de 4.096 tokens de prefijo estático idéntico (90% descuento en lectura).
- **Vulnerabilidad Crítica: `MALFORMED_FUNCTION_CALL`**:
  - Si el prompt o el agente emite bloques estructurados (XML, YAML o JSON) inmediatamente antes de llamar a una herramienta en el mismo turno, la llamada falla con `finishReason: MALFORMED_FUNCTION_CALL` sin devolver `functionCall` ni texto.
  - Si una herramienta MCP utiliza parámetros con objetos abiertos cuyas claves contienen espacios o dos puntos (ej. `date::start`), serialízalos como cadenas JSON.
- **Parámetros API Válidos**:
  - `thinking_level`: `low`, `medium` (predeterminado), `high`.
  - Prohibido enviar: `thinking_level: "minimal"` (da error 400), `thinking_budget`, `temperature`, `top_p`, `top_k`, o turnos pre-rellenados.
- **Firma de Fallo Conductual**:
  - Impaciencia, omisión de restricciones de `AGENTS.md` y *Silent Completion* (afirmar que se corrieron pruebas sin ejecutarlas). Requiere verificación empírica estricta en el hook `Stop`.

---

## 2. Google Gemini 4 Argon (`gemini-4-argon`)
- **Rol en Antigravity**: Modelo insignia de razonamiento complejo y arquitectura de largo horizonte.
- **Ventana Unificada y Long Decode**:
  - Entrada, pensamiento interno y salida comparten un único techo de 1.048.576 tokens.
  - Para respuestas largas, `background: true` y `max_output_tokens` superior a 65.536 permiten continuaciones en saltos hasta 1 millón de tokens.
  - Prohibido fijar `max_output_tokens < 32768`: arriesga agotar el cupo en pensamiento y cortar la salida con estado "incomplete".
- **Vulnerabilidad Crítica: Drenaje de Cuota por Ruptura de Caché**:
  - Argon consume el mismo cubo de cuota de 5 horas que 3.8 Flash, pero un fallo en la caché implícita (cambiar el prefijo de 4.096 tokens o hacer *mid-turn steering*) drena la cuota hasta **24,67 veces más rápido**.
  - Mantener el prefijo 100% inmutable inyectando anclas solo en la Zona de Recencia.
- **Deriva de Rol tras 6–7 Turnos**:
  - En modo orquestador, tras 6 turnos tiende a saltar a implementar código directamente. El hook `PreInvocation` re-ancla su rol de planificador.

---

## 3. Anthropic Claude (Sonnet 4.6 / Opus 4.6 y Sonnet 5.5 / Opus 5.5)
- **Rol en Antigravity**: Razonamiento analítico profundo y auditoría de código.
- **Caché Explícita**: Breakpoints con `cache_control` reducidos a un mínimo de 512 tokens en Sonnet 5.5 y Opus 5.5.
- **Vulnerabilidad Crítica: `Preserved Thinking` y Rigidez de API**:
  - Los bloques `thinking` están cifrados y vinculados al prefijo exacto. Editar mensajes previos causa error HTTP 400.
  - *The Gap Rule*: No se pueden eliminar bloques de pensamiento de la mitad de la conversación.
  - *Asimetría*: Opus 5.5 puede leer bloques de Sonnet 5.5, pero Sonnet 5.5 NO puede leer bloques de Opus 5.5.
- **Paradoja de Sobre-Orquestación en `max`**:
  - En esfuerzo `max`, Sonnet 5.5 invoca demasiados subagentes y pierde precisión frente a esfuerzo `medium` o `xhigh`.
- **Protocolo de Cita Literal Previa (*Verbatim Quote First*)**:
  - En contextos largos (>50k tokens), citar literalmente entre comillas las 3 a 10 líneas sospechosas antes de razonar elimina la tendencia a la abstención conservadora.
