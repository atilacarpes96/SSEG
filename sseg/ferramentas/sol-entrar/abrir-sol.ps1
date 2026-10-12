# Abre o SOL no Chrome e dá um clique numa área vazia da tela de login do SOE.
# O clique libera a senha que o Chrome preencheu; o script do Tampermonkey
# (sol-entrar.user.js) faz a contagem e clica em Entrar.
# Só clica se a janela da frente for a do login ("Acesso - Google Chrome").

$URL = "https://solcbm.rs.gov.br/solcbm/adm/"
$ESPERA = 25   # segundos esperando a tela de login aparecer

Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Tela {
    [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
    [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr h);
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
    [DllImport("user32.dll")] public static extern bool GetCursorPos(out POINT p);
    [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
    [DllImport("user32.dll")] public static extern void mouse_event(uint f, uint x, uint y, uint d, UIntPtr e);
    public struct RECT { public int L, T, R, B; }
    public struct POINT { public int X, Y; }
}
"@
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
# Coordenadas em pixels reais (com escala de tela do Windows em 125%/150% o clique ia para o lugar errado).
[Tela]::SetProcessDPIAware() | Out-Null

Start-Process "chrome.exe" $URL

# Espera a aba do login do SOE ficar na frente.
$janela = [IntPtr]::Zero
for ($i = 0; $i -lt $ESPERA * 5; $i++) {
    Start-Sleep -Milliseconds 200
    $p = Get-Process chrome -ErrorAction SilentlyContinue |
         Where-Object { $_.MainWindowTitle -like "Acesso*" } | Select-Object -First 1
    if ($p) { $janela = $p.MainWindowHandle; break }
}
if ($janela -eq [IntPtr]::Zero) { exit 1 }   # não achou a tela de login: não clica em nada

if ([Tela]::IsIconic($janela)) { [Tela]::ShowWindow($janela, 9) | Out-Null }
[Tela]::SetForegroundWindow($janela) | Out-Null
Start-Sleep -Milliseconds 700   # tempo para o Chrome preencher os campos

if ([Tela]::GetForegroundWindow() -ne $janela) { exit 2 }   # outra janela na frente: não clica

# Acha a área da página (o "documento") pela acessibilidade do Windows, para não
# clicar na barra de abas (abas na vertical ficam do lado esquerdo) nem na de endereço.
$raiz = [System.Windows.Automation.AutomationElement]::FromHandle($janela)
$cond = New-Object System.Windows.Automation.PropertyCondition(
    [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
    [System.Windows.Automation.ControlType]::Document)
$doc = $null
for ($i = 0; $i -lt 25 -and -not $doc; $i++) {
    $doc = $raiz.FindAll([System.Windows.Automation.TreeScope]::Descendants, $cond) |
           Where-Object { $_.Current.Name -like "Acesso*" -or $_.Current.BoundingRectangle.Width -gt 300 } |
           Sort-Object { $_.Current.BoundingRectangle.Width * $_.Current.BoundingRectangle.Height } -Descending |
           Select-Object -First 1
    if (-not $doc) { Start-Sleep -Milliseconds 200 }
}
if (-not $doc) { exit 3 }   # não achou a página: não clica em nada

# Área vazia: faixa esquerda da página, a 70% da altura (o formulário fica no centro).
$b = $doc.Current.BoundingRectangle
$x = [int]($b.Left + 30)
$y = [int]($b.Top + $b.Height * 0.7)

$antes = New-Object Tela+POINT
[Tela]::GetCursorPos([ref]$antes) | Out-Null
[Tela]::SetCursorPos($x, $y) | Out-Null
[Tela]::mouse_event(0x0002, 0, 0, 0, [UIntPtr]::Zero)   # botão esquerdo para baixo
[Tela]::mouse_event(0x0004, 0, 0, 0, [UIntPtr]::Zero)   # botão esquerdo para cima
[Tela]::SetCursorPos($antes.X, $antes.Y) | Out-Null
