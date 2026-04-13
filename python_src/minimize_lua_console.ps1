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
    public static extern bool IsIconic(IntPtr hWnd);

    public const int SW_MINIMIZE = 6;
}
"@

$timeout = 20 # Réduit à 20s
$start = Get-Date
$found = $false

while (((Get-Date) - $start).TotalSeconds -lt $timeout) {
    [Win32]::EnumWindows({
        param($hwnd, $lparam)
        $sb = New-Object System.Text.StringBuilder 256
        [Win32]::GetWindowText($hwnd, $sb, $sb.Capacity) | Out-Null
        $title = $sb.ToString()

        if ($title -like "*Lua Console*") {
            if (-not [Win32]::IsIconic($hwnd)) {
                [Win32]::ShowWindow($hwnd, 6) # 6 = Minimiser
                Write-Host "Console Lua trouvee et minimisee ! (Handle: $hwnd)"
            }
            $script:found = $true
        }
        return $true # Continue pour en trouver d'autres
    }, [IntPtr]::Zero) | Out-Null

    # On attend un peu avant de re-balayer, mais on ne s'arrête pas au premier succès
    # pour être sûr de capturer les consoles asynchrones
    Start-Sleep -Milliseconds 800
}
