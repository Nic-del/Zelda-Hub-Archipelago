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
    public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);

    [DllImport("user32.dll")]
    public static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);

    [DllImport("user32.dll")]
    public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);

    [StructLayout(LayoutKind.Sequential)]
    public struct RECT {
        public int Left;
        public int Top;
        public int Right;
        public int Bottom;
    }

    public const int SW_SHOWNORMAL = 1;
    public static readonly IntPtr HWND_BOTTOM = new IntPtr(1);
    public const uint SWP_NOSIZE = 0x0001;
    public const uint SWP_NOACTIVATE = 0x0010;
}
"@

$timeout = 30
$start = Get-Date
$found = $false

# Charger les infos de l'écran
Add-Type -AssemblyName System.Windows.Forms
$screen = [System.Windows.Forms.Screen]::PrimaryScreen
$screenWidth = $screen.Bounds.Width
$screenHeight = $screen.Bounds.Height

Write-Host "Recherche de la fenêtre de Broadcast PopTracker pour centrage..."

# Petit délai initial
Start-Sleep -Seconds 2

while (-not $found -and ((Get-Date) - $start).TotalSeconds -lt $timeout) {
    [Win32]::EnumWindows({
        param($hwnd, $lparam)
        $sb = New-Object System.Text.StringBuilder 256
        [Win32]::GetWindowText($hwnd, $sb, $sb.Capacity) | Out-Null
        $title = $sb.ToString()

        # Match uniquement si le titre COMMENCE par Broadcast
        if ($title -like "Broadcast*") {
            # Vérifier si c'est bien le processus PopTracker
            $processId = 0
            [Win32]::GetWindowThreadProcessId($hwnd, [ref]$processId) | Out-Null
            $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
            
            if ($process -and ($process.Name -like "*PopTracker*" -or $title -like "*PopTracker*" -or $title -like "*Zelda Hub - Web Tracker*")) {
                
                # Action de centrage répétée
                for ($i = 0; $i -lt 5; $i++) {
                    [Win32]::ShowWindow($hwnd, 1) # SW_SHOWNORMAL

                    $rect = New-Object Win32+RECT
                    [Win32]::GetWindowRect($hwnd, [ref]$rect) | Out-Null
                    $w = $rect.Right - $rect.Left
                    $h = $rect.Bottom - $rect.Top

                    if ($w -gt 50) { # S'assurer que la fenêtre a une taille réelle
                        $x = [int](($screenWidth - $w) / 2)
                        $y = [int](($screenHeight - $h) / 2)
                        
                        [Win32]::SetWindowPos($hwnd, [Win32]::HWND_BOTTOM, $x, $y, 0, 0, 0x0001 -bor 0x0010)
                    }
                    Start-Sleep -Milliseconds 600
                }

                $script:found = $true
                return $false 
            }
        }
        return $true
    }, [IntPtr]::Zero) | Out-Null

    if (-not $found) {
        Start-Sleep -Seconds 1
    }
}
