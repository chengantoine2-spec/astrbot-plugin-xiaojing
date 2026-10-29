param(
  [string]$PythonExe = "",
  [string]$AstrBotData = "$env:USERPROFILE\.astrbot\data"
)

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$target = Join-Path $AstrBotData "plugins\astrbot_plugin_xiaojing"

if (-not $PythonExe) {
  $candidates = @(
    "$env:USERPROFILE\AstrBot\backend\python\python.exe"
  )
  foreach ($c in $candidates) { if (Test-Path $c) { $PythonExe = $c; break } }
}
if (-not $PythonExe -or -not (Test-Path $PythonExe)) {
  throw "找不到 AstrBot 的 python.exe，请用 -PythonExe 指定"
}

Write-Host "安装到 $target"
New-Item -ItemType Directory -Path $target -Force | Out-Null
Copy-Item "$here\*.py" $target -Force
Copy-Item "$here\metadata.yaml" $target -Force
Copy-Item "$here\config.example.json" $target -Force
New-Item -ItemType Directory -Path "$target\data\assets" -Force | Out-Null
Copy-Item "$here\data\assets\*" "$target\data\assets" -Force
if (-not (Test-Path "$target\data\config.json")) {
  Copy-Item "$here\config.example.json" "$target\data\config.json"
  Write-Host "已生成 data/config.json，请填写 owner_ids / report_groups / onebot.token"
}

& $PythonExe -m pip install -r "$here\requirements.txt" --disable-pip-version-check
Write-Host "依赖安装完成。重启 AstrBot，并在新机器上重新绑定网易云 Cookie。"
