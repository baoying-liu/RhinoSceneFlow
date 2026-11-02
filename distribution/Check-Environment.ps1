$ErrorActionPreference='Continue'
Write-Output 'RhinoSceneFlow environment check (no credentials printed)'
$python=Join-Path $env:LOCALAPPDATA 'RhinoSceneFlow/chatkit-runtime/Scripts/python.exe'
if(Test-Path -LiteralPath $python){& $python -I -X utf8 -c "import chatkit,fastapi,uvicorn; print('ChatKit: OK')"}else{Write-Output 'ChatKit: missing; run Install.cmd.'}
$candidates=@()
if($env:RHINOSCENEFLOW_CODEX){$candidates+=$env:RHINOSCENEFLOW_CODEX}
$candidates+=@(Get-Command codex.exe -ErrorAction SilentlyContinue | ForEach-Object {$_.Source})
$candidates+=(Join-Path $env:USERPROFILE '.codex/bin/codex.exe')
$extensions=Join-Path $env:USERPROFILE '.vscode/extensions'
if(Test-Path -LiteralPath $extensions){$candidates+=@(Get-ChildItem -LiteralPath $extensions -Directory -Filter 'openai.chatgpt-*' | Sort-Object LastWriteTime -Descending | ForEach-Object {Join-Path $_.FullName 'bin/windows-x86_64/codex.exe'})}
$codex=$candidates | Where-Object {Test-Path -LiteralPath $_ -PathType Leaf} | Select-Object -First 1
if($codex){
    $status=(& $codex login status 2>&1 | Out-String)
    if($LASTEXITCODE -eq 0 -and $status -match 'ChatGPT'){Write-Output 'Codex: signed in with ChatGPT (image access is checked when generating).'}else{Write-Output 'Codex: found; sign in with your own ChatGPT account in Codex.'}
}else{Write-Output 'Codex: not found. Install the OpenAI Codex extension for VS Code and sign in, or install codex.exe on PATH.'}
Write-Output 'WebView2 is required. If the chat is blank, install Microsoft WebView2 Evergreen Runtime.'
Write-Output 'Rhino command: RhinoSceneFlow'
