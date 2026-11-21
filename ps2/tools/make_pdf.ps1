# Turns results\report.html into results\Flatland_PS2_Report.pdf using Edge (headless). Run from Windows PowerShell:
#   powershell -File tools\make_pdf.ps1
$root = Split-Path -Parent $PSScriptRoot
$html = Join-Path $root "results\report.html"
$pdf  = Join-Path $root "results\Flatland_PS2_Report.pdf"
$edge = @("C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", "C:\Program Files\Microsoft\Edge\Application\msedge.exe",
          "C:\Program Files\Google\Chrome\Application\chrome.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $edge) { Write-Error "Edge or Chrome not found"; exit 1 }
if (Test-Path $pdf) { Remove-Item $pdf -Force }
$uri = ([System.Uri]$html).AbsoluteUri
& $edge --headless=new --disable-gpu --no-pdf-header-footer "--print-to-pdf=$pdf" $uri | Out-Null
Start-Sleep -Seconds 3
if (Test-Path $pdf) { "wrote $pdf ($([math]::Round((Get-Item $pdf).Length/1KB)) KB)" } else { Write-Error "PDF was not created"; exit 1 }
