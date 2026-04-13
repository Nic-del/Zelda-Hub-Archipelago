param(
    [string]$slotname = ""
)

# --- CONFIGURATION (Méthode 1 uniquement, sans pause) ---
$vk_key = 0x52  # R
$sc_key = 0x13  # ScanCode R

Write-Host "--- UNPAUSE AUTOMATIQUE BIZHAWK (Méthode 1) ---" -ForegroundColor Cyan
if ($slotname) { Write-Host "Cible spécifique : $slotname" -ForegroundColor Yellow }

# Définition des APIs Win32
$signature = @'
using System;
using System.Runtime.InteropServices;
using System.Text;

public class Win32 {
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, int dwExtraInfo);
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll", CharSet = CharSet.Auto)] public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
}
'@
try { Add-Type -TypeDefinition $signature -ErrorAction SilentlyContinue } catch {}

# Recherche BizHawk
$foundWindows = New-Object System.Collections.Generic.List[PSObject]
[Win32]::EnumWindows({ param($hwnd, $lparam)
    if ([Win32]::IsWindowVisible($hwnd)) {
        $sb = New-Object System.Text.StringBuilder 256
        [Win32]::GetWindowText($hwnd, $sb, $sb.Capacity) | Out-Null
        $title = $sb.ToString()
        $is_hawk = ($title -like "*Hawk*" -or $title -like "*Biz*")
        
        if ($is_hawk) {
             # Si on a un slotname, on vérifie qu'il est présent dans le titre
             if ($slotname) {
                 if ($title -like "*$slotname*") {
                    $foundWindows.Add([PSCustomObject]@{ HWND = $hwnd; Title = $title })
                 }
             } else {
                 # Pas de contrainte de slot : n'importe quel BizHawk fera l'affaire
                 $foundWindows.Add([PSCustomObject]@{ HWND = $hwnd; Title = $title })
             }
        }
    }
    return $true
}, [IntPtr]::Zero) | Out-Null

if ($foundWindows.Count -eq 0) { Write-Host "BizHawk non trouvé !" -ForegroundColor Red; exit }

$target = $foundWindows[0]
$hwnd = $target.HWND
Write-Host "Cible : $($target.Title) (Handle: $hwnd)" -ForegroundColor Green

# --- EXECUTION MÉTHODE 1 ( keybd_event ) ---
Write-Host "Envoi du signal Unpause (R)..." -ForegroundColor Gray
[Win32]::SetForegroundWindow($hwnd) | Out-Null
Start-Sleep -m 200
[Win32]::keybd_event($vk_key, $sc_key, 0, 0); Start-Sleep -m 50; [Win32]::keybd_event($vk_key, $sc_key, 2, 0)
Write-Host "Signal envoyé avec succès (Méthode 1)." -ForegroundColor Green
