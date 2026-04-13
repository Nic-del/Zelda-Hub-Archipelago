$command = "/connect archipelago.gg:63802 Linkww"
Set-Clipboard -Value $command

$wshell = New-Object -ComObject WScript.Shell;
$title = "Archipelago The Wind Waker Client 0.6.6"

if ($wshell.AppActivate($title)) {
    Start-Sleep -Milliseconds 500
    # Envoyer Ctrl+V (Paste)
    $wshell.SendKeys("^v")
    Start-Sleep -Milliseconds 200
    # Envoyer Enter
    $wshell.SendKeys("{ENTER}")
    Write-Host "Success: Commande collee et validée via Clipboard Paste dans $title"
} else {
    Write-Host "Error: Fenetre '$title' non trouvée."
}
