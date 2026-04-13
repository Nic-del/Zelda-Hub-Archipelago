param (
    [string]$Name = "Linkww",
    [string]$Password = "None",
    [string]$Port = "63802",
    [string]$Server = "archipelago.gg",
    [string]$Title = "Archipelago The Wind Waker Client*"
)

Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class Win32 {
    [DllImport("user32.dll", CharSet = CharSet.Auto)]
    public static extern bool PostMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);
    public const uint WM_KEYDOWN = 0x0100;
    public const uint WM_KEYUP = 0x0101;
    public const uint WM_CHAR = 0x0102;
    public const int VK_RETURN = 0x0D;
    public const int VK_BACK = 0x08;
    [DllImport("user32.dll")]
    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    public const int SW_MINIMIZE = 6;
    public const int SW_SHOWMINNOACTIVE = 7;
}
"@

$titlePartial = $Title
$found = $false

Write-Host "En attente du lancement du client contenant '$titlePartial'..."

$timeoutSeconds = 60
$startTime = Get-Date

# Boucle de polling : on vérifie toutes les 5 secondes
while (-not $found) {
    if (((Get-Date) - $startTime).TotalSeconds -gt $timeoutSeconds) {
        Write-Error "Timeout: Client non trouvé après $timeoutSeconds secondes. Arrêt de l'automatisation."
        exit 1
    }

    $process = Get-Process Archipelago* -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -like $titlePartial } | Select-Object -First 1
    
    if ($process) {
        $hwnd = $process.MainWindowHandle
        if ($hwnd -and $hwnd -ne [IntPtr]::Zero) {
            $found = $true
            Write-Host "Client trouvé ! Réduction en arrière-plan..."
            # On réduit la fenêtre (SW_MINIMIZE = 6)
            [Win32]::ShowWindow($hwnd, [Win32]::SW_MINIMIZE)
            Write-Host "Client minimisé. (HWND: $hwnd)"
        }
    }
    
    if (-not $found) {
        Write-Host "Client non trouvé, nouvelle tentative dans 5 secondes..."
        Start-Sleep -Seconds 5
    }
}

# Une fois trouvé, on procède à l'automatisation
$command = "/connect ${Name}:${Password}@${Server}:${Port}"

Write-Host "Nettoyage du champ d'entrée..."
for ($i = 0; $i -lt 100; $i++) {
    [Win32]::PostMessage($hwnd, [Win32]::WM_KEYDOWN, [IntPtr][Win32]::VK_BACK, [IntPtr]0)
    [Win32]::PostMessage($hwnd, [Win32]::WM_KEYUP, [IntPtr][Win32]::VK_BACK, [IntPtr]0)
}

Start-Sleep -Milliseconds 100

Write-Host "Envoi de la commande : $command"
foreach ($char in $command.ToCharArray()) {
    [Win32]::PostMessage($hwnd, [Win32]::WM_CHAR, [IntPtr][int]$char, [IntPtr]0)
}

Start-Sleep -Milliseconds 100

# Validation (Enter)
[Win32]::PostMessage($hwnd, [Win32]::WM_CHAR, [IntPtr]13, [IntPtr]0)
[Win32]::PostMessage($hwnd, [Win32]::WM_KEYDOWN, [IntPtr]13, [IntPtr]0x001C0001)
[Win32]::PostMessage($hwnd, [Win32]::WM_KEYUP, [IntPtr]13, [IntPtr]0xC01C0001)

Write-Host "Success: Commande envoyée avec succès."
