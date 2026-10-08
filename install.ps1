& {

$ErrorActionPreference = 'Stop'

$waypointFailed = $false



function Fail([string]$Message) { throw [System.Exception]::new("WAYPOINT: $Message") }



$tempDir = $null

try {

    if (-not (Get-Command git -ErrorAction SilentlyContinue)) { Fail 'Git kurulu değil. https://git-scm.com adresinden Git kurun.' }

    $target = (Get-Location).ProviderPath

    $homePath = [System.IO.Path]::GetFullPath($env:USERPROFILE).TrimEnd('\', '/')

    $fullTarget = [System.IO.Path]::GetFullPath($target).TrimEnd('\', '/')

    if ($fullTarget -ieq $homePath) { Fail 'Ev klasörüne kurulum yapılamaz.' }

    $root = [System.IO.Path]::GetPathRoot([System.IO.Path]::GetFullPath($target)).TrimEnd('\', '/')

    if (-not $root -or $fullTarget -ieq $root) { Fail 'Sürücü köküne kurulum yapılamaz.' }



    if ($env:WAYPOINT_SOURCE) {

        $sourceDir = Join-Path $env:WAYPOINT_SOURCE 'template'

        if (-not (Test-Path -LiteralPath $sourceDir -PathType Container)) { Fail 'WAYPOINT_SOURCE içinde template klasörü bulunamadı.' }

    } else {

        $tempDir = Join-Path ([System.IO.Path]::GetTempPath()) ([guid]::NewGuid().ToString())

        New-Item -ItemType Directory -Path $tempDir | Out-Null

        $repo = if ($env:WAYPOINT_REPO) { $env:WAYPOINT_REPO } else { 'erenuzman/WaypointSkill' }

        $ref = if ($env:WAYPOINT_REF) { $env:WAYPOINT_REF } else { 'main' }

        $sourceDir = $null

        try {

            $zip = Join-Path $tempDir 'waypoint.zip'

            Invoke-WebRequest -Uri "https://github.com/$repo/archive/refs/heads/$ref.zip" -OutFile $zip -UseBasicParsing

            $expanded = Join-Path $tempDir 'expanded'

            Expand-Archive -LiteralPath $zip -DestinationPath $expanded

            $sourceDir = Get-ChildItem -LiteralPath $expanded -Directory | Select-Object -First 1 | ForEach-Object { Join-Path $_.FullName 'template' }

        } catch { $sourceDir = $null }

        if (-not $sourceDir -or -not (Test-Path -LiteralPath $sourceDir -PathType Container)) {

            # Gizli repo: GitHub CLI girişiyle indir

            if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { Fail "Waypoint indirilemedi. Repo gizliyse GitHub CLI kurup 'gh auth login' ile giriş yapın: https://cli.github.com" }

            $clone = Join-Path $tempDir 'src'

            & gh repo clone $repo $clone -- --depth 1 --branch $ref -q 2>$null

            if ($LASTEXITCODE -ne 0) { Fail "Waypoint indirilemedi. 'gh auth login' ile giriş yaptığınızdan ve repoya erişiminiz olduğundan emin olun." }

            $sourceDir = Join-Path $clone 'template'

        }

        if (-not (Test-Path -LiteralPath $sourceDir -PathType Container)) { Fail 'Arşivde template klasörü bulunamadı.' }

    }



    $waypoint = Join-Path $target '.waypoint'

    if (Test-Path -LiteralPath $waypoint -PathType Container) {

        foreach ($name in @('KURALLAR.md', 'VERSION', '.gitattributes', '.gitignore', 'guncelle.bat', 'guncelle.command')) {

            Copy-Item -LiteralPath (Join-Path $sourceDir ".waypoint/$name") -Destination (Join-Path $waypoint $name) -Force

        }

        $hooks = Join-Path $waypoint 'hooks'

        New-Item -ItemType Directory -Path $hooks -Force | Out-Null

        Get-ChildItem -LiteralPath $hooks -File -Force | Remove-Item -Force

        Get-ChildItem -LiteralPath (Join-Path $sourceDir '.waypoint/hooks') -File -Recurse -Force |

            Where-Object { $_.FullName -notmatch '[\\/]__pycache__([\\/]|$)' } |

            ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $hooks $_.Name) -Force }

        $commands = Join-Path $waypoint 'komutlar'

        if (Test-Path -LiteralPath $commands) { Remove-Item -LiteralPath $commands -Recurse -Force }

        Copy-Item -LiteralPath (Join-Path $sourceDir '.waypoint/komutlar') -Destination $commands -Recurse -Force

        foreach ($name in @('ILERLEME.md', 'DERSLER.md', 'HARITA.md')) {

            $path = Join-Path $waypoint $name

            if (-not (Test-Path -LiteralPath $path)) { Copy-Item -LiteralPath (Join-Path $sourceDir ".waypoint/$name") -Destination $path }

        }

        $result = 'güncellendi'

    } else {

        Copy-Item -LiteralPath (Join-Path $sourceDir '.waypoint') -Destination $target -Recurse -Force

        Get-ChildItem -LiteralPath $waypoint -Directory -Recurse -Force | Where-Object Name -eq '__pycache__' | Remove-Item -Recurse -Force

        $result = 'kuruldu'

    }



    foreach ($name in @('AGENTS.md', 'CLAUDE.md')) {

        $path = Join-Path $target $name

        $pointer = '.waypoint/KURALLAR.md'

        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {

            Copy-Item -LiteralPath (Join-Path $sourceDir $name) -Destination $path

        } elseif (-not (Select-String -LiteralPath $path -SimpleMatch -Pattern $pointer -Quiet)) {

            $old = [System.IO.File]::ReadAllText($path)

            $addition = [System.IO.File]::ReadAllText((Join-Path $sourceDir $name))

            $utf8 = New-Object System.Text.UTF8Encoding($false)

            [System.IO.File]::WriteAllText($path, $old + "`r`n`r`n" + $addition, $utf8)

        } elseif ($name -eq 'AGENTS.md') {

            # Older versions told the agent to follow the rules "exactly"; swap in the current pointer line.

            $legacy = 'Before doing anything in this project, read `.waypoint/KURALLAR.md` and follow it exactly. It overrides your defaults.'

            $old = [System.IO.File]::ReadAllText($path)

            if ($old.Contains($legacy)) {

                $current = 'Before working in this project, read `.waypoint/KURALLAR.md`.'

                $utf8 = New-Object System.Text.UTF8Encoding($false)

                [System.IO.File]::WriteAllText($path, $old.Replace($legacy, $current), $utf8)

            }

        }

    }



    $inside = $null

    try { $inside = & git -C $target rev-parse --is-inside-work-tree 2>$null | Select-Object -Last 1 } catch { $inside = $null }

    if ($LASTEXITCODE -ne 0 -or $inside -ne 'true') {

        & git -C $target init 2>$null | Out-Null

        if ($LASTEXITCODE -ne 0) { Fail 'Git deposu başlatılamadı.' }

        Write-Output 'Kayıt noktası alabilmek için git kurdum.'

    }

    # The project's own hooks keep running: Waypoint's hooks call them first (see .waypoint/hooks/onceki-hook).
    $oldHooks = (& git -C $target config --get core.hooksPath 2>$null | Select-Object -First 1)
    $gitHookDir = Join-Path $target '.git/hooks'
    if ($oldHooks -and $oldHooks -ne '.waypoint/hooks') {
        & git -C $target config waypoint.oncekiHooks $oldHooks 2>$null
        Write-Output "Not: Bu projede önceden başka kayıt kontrolleri vardı ($oldHooks). Waypoint onları da çalıştırmaya devam edecek."
    } elseif ((-not $oldHooks -or $oldHooks -eq '.waypoint/hooks') -and -not (& git -C $target config --get waypoint.oncekiHooks 2>$null) -and (Test-Path -LiteralPath $gitHookDir) -and (Get-ChildItem -LiteralPath $gitHookDir -File -ErrorAction SilentlyContinue | Where-Object { $_.Extension -ne '.sample' })) {
        $hookPath = (& git -C $target rev-parse --git-common-dir 2>$null | Select-Object -First 1) + '/hooks'
        & git -C $target config waypoint.oncekiHooks $hookPath 2>$null
        Write-Output 'Not: Bu projenin .git/hooks klasöründe önceden kayıt kontrolleri vardı. Waypoint onları da çalıştırmaya devam edecek.'
    }
    & git -C $target config core.hooksPath .waypoint/hooks 2>$null

    if ($LASTEXITCODE -ne 0) { Fail 'Git hook yolu ayarlanamadı.' }



    $pythonOk = $false

    foreach ($candidate in @('python3', 'python')) {

        $cmd = Get-Command $candidate -ErrorAction SilentlyContinue

        if ($cmd) {

            try { & $cmd.Source --version *> $null; if ($LASTEXITCODE -eq 0) { $pythonOk = $true; break } } catch { }

        }

    }

    if (-not $pythonOk) {

        $py = Get-Command py -ErrorAction SilentlyContinue

        if ($py) { try { & $py.Source -3 --version *> $null; if ($LASTEXITCODE -eq 0) { $pythonOk = $true } } catch { } }

    }

    if (-not $pythonOk) { Write-Output 'Uyarı: Python 3 bulunamadı. Python kurulana kadar kayıt alınamaz (Waypoint kuralları Python ile denetlenir). Kurulum: https://www.python.org/downloads/' }

    Write-Output "Waypoint $result."

    Write-Output 'Bu klasörde yapay zekâ aracını (Claude Code, Codex, Antigravity…) aç ve ne yapmak istediğini anlat.'

} catch {

    $msg = $_.Exception.Message

    if ($msg.StartsWith('WAYPOINT: ')) { $msg = $msg.Substring(10) } else { $msg = "Kurulum tamamlanamadı: $msg" }

    Write-Host "Hata: $msg" -ForegroundColor Red

    $waypointFailed = $true

} finally {

    if ($tempDir -and (Test-Path -LiteralPath $tempDir)) { Remove-Item -LiteralPath $tempDir -Recurse -Force }

}

if ($waypointFailed -and $MyInvocation.ScriptName) { exit 1 }

}

