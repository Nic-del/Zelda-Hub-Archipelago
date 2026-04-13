param (
    [Parameter(Mandatory=$true)]
    [string]$ip,
    [Parameter(Mandatory=$true)]
    [string]$port,
    [Parameter(Mandatory=$true)]
    [string]$slot,
    [string]$mdp
)

$url = "http://localhost:5173/#/?ip=$ip&port=$port&slot=$slot&autolaunch=true&layout=grid"
if ($mdp) {
    $url += "&mdp=$mdp"
}

Write-Host "Opening tracker at $url"
Start-Process $url
