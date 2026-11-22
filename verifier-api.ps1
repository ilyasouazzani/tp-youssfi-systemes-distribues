$ErrorActionPreference = 'Stop'
$gateway = 'http://127.0.0.1:8080'
$customers = Invoke-RestMethod "$gateway/customers" -TimeoutSec 5
if (-not ($customers.id -contains 1)) { throw 'Client de démonstration introuvable.' }
$account = Invoke-RestMethod "$gateway/accounts/ACC-001" -TimeoutSec 5
if (-not $account.customerAvailable -or $account.customer.id -ne 1) { throw 'Client du compte introuvable.' }
if ($account.account.balance -ne 1200) { throw 'Solde inattendu.' }
$missing = Invoke-WebRequest "$gateway/accounts/INCONNU" -SkipHttpErrorCheck -TimeoutSec 5
if ($missing.StatusCode -ne 404) { throw "HTTP $($missing.StatusCode), attendu 404." }
Write-Output 'API clients, compte enrichi et HTTP 404 vérifiés.'
