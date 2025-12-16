# PowerShell script to fix Hebrew display in terminal
# Run this before running Python scripts

# Set console code page to UTF-8
chcp 65001 | Out-Null

# Set output encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "Hebrew display fix applied!" -ForegroundColor Green
Write-Host "Test: אלינור בדיקה" -ForegroundColor Yellow
Write-Host ""
Write-Host "If Hebrew displays correctly above, the fix worked!"
Write-Host "This fix applies to this terminal session only."
Write-Host ""
Write-Host "To make it permanent:"
Write-Host "  1. Add to PowerShell profile: notepad `$PROFILE"
Write-Host "  2. Or use Windows Terminal (better support)"
Write-Host ""

