Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; using System.Text; public class Win32 { [DllImport("user32.dll")] public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam); public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam); [DllImport("user32.dll", CharSet = CharSet.Auto)] public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount); [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd); }'; 
[Win32]::EnumWindows({ 
    param($hwnd, $lparam) 
    if ([Win32]::IsWindowVisible($hwnd)) { 
        $sb = New-Object System.Text.StringBuilder 256; 
        [Win32]::GetWindowText($hwnd, $sb, $sb.Capacity) | Out-Null; 
        $title = $sb.ToString(); 
        if ($title -like '*Zelda*' -or $title -like '*Tracker*') { 
            Write-Host "Window: $title (Handle: $hwnd)" 
        } 
    }; 
    return $true 
}, [IntPtr]::Zero)
