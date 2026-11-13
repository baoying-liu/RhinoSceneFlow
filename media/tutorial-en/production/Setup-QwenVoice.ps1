param([switch]$Status)
$ErrorActionPreference = 'Stop'
$credentialDir = Join-Path $env:LOCALAPPDATA 'RhinoSceneFlow\credentials'
$credentialFile = Join-Path $credentialDir 'qwen.json'
if ($Status) {
    if (Test-Path -LiteralPath $credentialFile) {
        $saved = Get-Content -LiteralPath $credentialFile -Raw | ConvertFrom-Json
        [pscustomobject]@{ Configured = $true; Region = $saved.region; Protection = 'Windows CurrentUser DPAPI' }
    } else { [pscustomobject]@{ Configured = $false } }
    return
}
Add-Type -AssemblyName System.Windows.Forms, System.Drawing, System.Security
[System.Windows.Forms.Application]::EnableVisualStyles()
$form = New-Object System.Windows.Forms.Form
$form.Text = 'SceneFlow - Qwen voice credentials'
$form.ClientSize = New-Object System.Drawing.Size(560, 330)
$form.StartPosition = 'CenterScreen'
$form.FormBorderStyle = 'FixedDialog'
$form.MaximizeBox = $false
$form.Font = New-Object System.Drawing.Font('Segoe UI', 10)
function Add-Label($text, $x, $y, $w, $h) {
    $c = New-Object System.Windows.Forms.Label
    $c.Text = $text; $c.SetBounds($x,$y,$w,$h); $form.Controls.Add($c)
}
Add-Label 'Qwen API Key (stored encrypted for this Windows user)' 20 18 520 25
$keyBox = New-Object System.Windows.Forms.TextBox
$keyBox.SetBounds(20,50,520,30); $keyBox.UseSystemPasswordChar = $true
$form.Controls.Add($keyBox)
Add-Label 'API Key region - must match the console where you created it' 20 94 520 25
$regions = New-Object System.Windows.Forms.ComboBox
$regions.SetBounds(20,124,520,30); $regions.DropDownStyle = 'DropDownList'
[void]$regions.Items.Add('China (Beijing) / 中国内地（北京）')
[void]$regions.Items.Add('International (Singapore) / 国际（新加坡）')
$regions.SelectedIndex = 0
if (Test-Path -LiteralPath $credentialFile) {
    try { if ((Get-Content -LiteralPath $credentialFile -Raw | ConvertFrom-Json).region -eq 'singapore') { $regions.SelectedIndex=1 } } catch {}
}
$form.Controls.Add($regions)
Add-Label 'Saving does not upload your recording or call a paid API. The key is never shown again. Existing saved credentials remain unchanged if you cancel.' 20 169 520 60
$statusLabel = New-Object System.Windows.Forms.Label
$statusLabel.SetBounds(20,230,520,32); $form.Controls.Add($statusLabel)
$save = New-Object System.Windows.Forms.Button
$save.Text = 'Save encrypted / 加密保存'; $save.SetBounds(20,274,245,36)
$form.Controls.Add($save)
$close = New-Object System.Windows.Forms.Button
$close.Text = 'Close / 关闭'; $close.SetBounds(295,274,245,36)
$form.Controls.Add($close); $close.Add_Click({$form.Close()})
$save.Add_Click({
    $plainBytes = $null
    try {
        $key = $keyBox.Text.Trim()
        if ($key.Length -lt 16 -or $key -match '\s') {
            $statusLabel.Text = 'Please enter the complete API Key (no spaces).'; return
        }
        $plainBytes = [System.Text.Encoding]::UTF8.GetBytes($key)
        $encrypted = [System.Security.Cryptography.ProtectedData]::Protect($plainBytes, $null, [System.Security.Cryptography.DataProtectionScope]::CurrentUser)
        $region = if ($regions.SelectedIndex -eq 0) { 'beijing' } else { 'singapore' }
        New-Item -ItemType Directory -Force -Path $credentialDir | Out-Null
        $payload = @{ version=1; region=$region; protectedKey=[Convert]::ToBase64String($encrypted) } | ConvertTo-Json
        $temp = Join-Path $credentialDir ([Guid]::NewGuid().ToString('N') + '.tmp')
        try {
            [IO.File]::WriteAllText($temp,$payload,(New-Object System.Text.UTF8Encoding($false)))
            if ([IO.File]::Exists($credentialFile)) { [IO.File]::Replace($temp,$credentialFile,$null) }
            else { [IO.File]::Move($temp,$credentialFile) }
        } finally { if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp } }
        $keyBox.Clear(); $key=$null
        $statusLabel.ForeColor = [Drawing.Color]::DarkGreen
        $statusLabel.Text = 'Saved encrypted. You can close this window. / 已加密保存'
    } catch {
        $statusLabel.ForeColor = [Drawing.Color]::DarkRed
        $statusLabel.Text = 'Could not save. Existing credentials were preserved.'
    } finally {
        if ($null -ne $plainBytes) { [Array]::Clear($plainBytes,0,$plainBytes.Length) }
    }
})
$form.Add_FormClosed({$keyBox.Clear()})
[void]$form.ShowDialog()
$form.Dispose()
