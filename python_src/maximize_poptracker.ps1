param(
    [int]$MonitorIndex = 0
)

Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
using System.Text;

public class Win32 {
    [DllImport("user32.dll")]
    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);

    [DllImport("user32.dll")]
    public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);

    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    [DllImport("user32.dll", CharSet = CharSet.Auto)]
    public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);

    [DllImport("user32.dll")]
    public static extern bool IsWindowVisible(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);

    public const int SW_MAXIMIZE = 3;
    public const int SW_RESTORE = 9;
    public static readonly IntPtr HWND_TOP = new IntPtr(0);
}
"@

# On a besoin de Windows Forms pour les écrans
Add-Type -AssemblyName System.Windows.Forms

$timeout = 30 # Temps d'attente maximum en secondes
$start = Get-Date
$found = $false

Write-Host "Recherche de la fenêtre PopTracker ou Web Tracker sur l'écran $MonitorIndex..."

# Récupérer les infos de l'écran cible
$screens = [System.Windows.Forms.Screen]::AllScreens
if ($MonitorIndex -ge $screens.Count) {
    Write-Host "Index d'écran $MonitorIndex invalide (Total: $($screens.Count)). Utilisation de l'écran principal."
    $MonitorIndex = 0
}
$targetScreen = $screens[$MonitorIndex]
$targetX = $targetScreen.Bounds.X
$targetY = $targetScreen.Bounds.Y

while (-not $found -and ((Get-Date) - $start).TotalSeconds -lt $timeout) {
    [Win32]::EnumWindows({
        param($hwnd, $lparam)
        $sb = New-Object System.Text.StringBuilder 256
        [Win32]::GetWindowText($hwnd, $sb, $sb.Capacity) | Out-Null
        $title = $sb.ToString()

        if ([Win32]::IsWindowVisible($hwnd) -and (($title -like "*PopTracker*" -and $title -notlike "*Broadcast*") -or ($title -like "*Magpie*" -and $title -notlike "*Broadcast*") -or $title -like "*Zelda Hub - Web Tracker*")) {
            
            Write-Host "Fenêtre '$title' trouvée !"
            
            # 1. On restaure si minimisé pour pouvoir la bouger
            [Win32]::ShowWindow($hwnd, 9) # 9 = Restorer

            # 2. On déplace la fenêtre sur l'écran cible (X, Y)
            # 0x0040 = SHOWWINDOW, 0x0001 = NOSIZE
            [Win32]::SetWindowPos($hwnd, [Win32]::HWND_TOP, $targetX, $targetY, 0, 0, 0x0001)
            
            # 3. On maximise sur cet écran
            [Win32]::ShowWindow($hwnd, 3) # 3 = Maximiser
            [Win32]::SetForegroundWindow($hwnd)
            
            $script:found = $true
            Write-Host "Fenêtre '$title' déplacée sur l'écran $MonitorIndex et maximisée !"
            return $false 
        }
        return $true
    }, [IntPtr]::Zero) | Out-Null

    if (-not $found) {
        Start-Sleep -Milliseconds 500
    }
}
