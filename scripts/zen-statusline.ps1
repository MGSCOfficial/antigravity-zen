# zen-statusline.ps1 - Telemetría de Estrés Cognitivo en Vivo para Antigravity CLI (PowerShell / Windows)
param()

$rawInput = [Console]::In.ReadToEnd()
if ([string]::IsNullOrWhiteSpace($rawInput)) {
    Write-Host -NoNewline "Zen: Inicializando..."
    exit 0
}

try {
    $data = $rawInput | ConvertFrom-Json
} catch {
    Write-Host -NoNewline "Zen: Activo"
    exit 0
}

$totalIn = 0
$usedPct = 0.0
if ($data.context_window) {
    if ($data.context_window.total_input_tokens) { $totalIn = [int]$data.context_window.total_input_tokens }
    if ($data.context_window.used_percentage) { $usedPct = [double]$data.context_window.used_percentage }
}

$modelName = "Model"
$effort = "default"
if ($data.model) {
    if ($data.model.display_name) { $modelName = $data.model.display_name }
    elseif ($data.model.id) { $modelName = $data.model.id }
    if ($data.model.effort) { $effort = $data.model.effort }
}

$state = "idle"
if ($data.agent_state) { $state = $data.agent_state }

$runningSubs = 0
if ($data.subagents) {
    foreach ($sub in $data.subagents) {
        if ($sub.status -eq "running") { $runningSubs++ }
    }
}

$errors = 0
$turns = 0
$metricsFile = ".zen/runtime_metrics.json"
if (Test-Path $metricsFile) {
    try {
        $m = Get-Content $metricsFile -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($m.consecutive_errors) { $errors = [int]$m.consecutive_errors }
        if ($m.invocation_count -and $m.last_checkpoint_turn) {
            $turns = [int]$m.invocation_count - [int]$m.last_checkpoint_turn
        } elseif ($m.invocation_count) {
            $turns = [int]$m.invocation_count
        }
    } catch {}
}

$ESC = [char]27
$GREEN = "$ESC[38;5;114m"
$YELLOW = "$ESC[38;5;221m"
$ORANGE = "$ESC[38;5;209m"
$RED = "$ESC[38;5;203m"
$CYAN = "$ESC[38;5;117m"
$RESET = "$ESC[0m"

$tokK = "0k"
if ($totalIn -gt 0) {
    $tokK = "{0:N1}k" -f ($totalIn / 1000)
}

if ($totalIn -ge 75000 -or $turns -ge 15 -or $errors -ge 2) {
    $badge = "$RED[!] ESTRES CRITICO (/zen-reset + /clear)$RESET"
} elseif ($totalIn -ge 32000 -or $turns -ge 10 -or $errors -eq 1) {
    $badge = "$ORANGE[*] CONTEXT ROT (Usa /zen-reset o /btw)$RESET"
} elseif ($totalIn -ge 12000 -or $turns -ge 6) {
    $badge = "$YELLOW[-] DRIFT LEVE (Valle U)$RESET"
} else {
    $badge = "$GREEN[+] ZEN OPTIMO$RESET"
}

$errStr = ""
if ($errors -gt 0) {
    $errStr = " | $RED! Err:$errors$RESET"
}

$subStr = ""
if ($runningSubs -gt 0) {
    $subStr = " | Subs:$runningSubs"
}

$pctStr = "{0:N1}%" -f $usedPct
$line = $badge + " | " + $CYAN + $modelName + " (" + $effort + ")" + $RESET + " | Tok:" + $tokK + " (" + $pctStr + ") | Turnos:" + $turns + $errStr + $subStr + " | [" + $state + "]"
Write-Host -NoNewline $line
