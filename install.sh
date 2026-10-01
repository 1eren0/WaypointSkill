#!/bin/sh
set -eu

fail() { printf '%s\n' "Hata: $1" >&2; exit 1; }
info() { printf '%s\n' "$1"; }

command -v git >/dev/null 2>&1 || fail 'Git kurulu değil. https://git-scm.com adresinden Git kurun.'

target=$(pwd -P)
home=${HOME:-}
if [ -n "$home" ] && [ "$target" = "$(cd "$home" 2>/dev/null && pwd -P || printf '%s' "$home")" ]; then fail 'Ev klasörüne kurulum yapılamaz.'; fi
case "$target" in /) fail 'Dosya sistemi köküne kurulum yapılamaz.';; esac

if [ -n "${WAYPOINT_SOURCE:-}" ]; then
    source_dir=$WAYPOINT_SOURCE/template
    [ -d "$source_dir" ] || fail 'WAYPOINT_SOURCE içinde template klasörü bulunamadı.'
    temp_dir=
else
    command -v curl >/dev/null 2>&1 || fail 'İndirme için curl gerekli.'
    command -v tar >/dev/null 2>&1 || fail 'Arşivi açmak için tar gerekli.'
    temp_dir=$(mktemp -d "${TMPDIR:-/tmp}/waypoint.XXXXXX") || fail 'Geçici klasör oluşturulamadı.'
    trap 'rm -rf "$temp_dir"' EXIT HUP INT TERM
    repo=${WAYPOINT_REPO:-erenuzman/WaypointSkill}
    ref=${WAYPOINT_REF:-main}
    source_dir=
    if curl -fsSL "https://codeload.github.com/$repo/tar.gz/refs/heads/$ref" 2>/dev/null | tar -xz -C "$temp_dir" 2>/dev/null; then
        source_dir=$(find "$temp_dir" -type d -name template -print 2>/dev/null | head -n 1)
    fi
    if [ -z "$source_dir" ]; then
        # Gizli repo: GitHub CLI girişiyle indir
        command -v gh >/dev/null 2>&1 || fail "Waypoint indirilemedi. Repo gizliyse GitHub CLI kurup 'gh auth login' ile giriş yapın: https://cli.github.com"
        gh repo clone "$repo" "$temp_dir/src" -- --depth 1 --branch "$ref" -q 2>/dev/null || fail "Waypoint indirilemedi. 'gh auth login' ile giriş yaptığınızdan ve repoya erişiminiz olduğundan emin olun."
        source_dir="$temp_dir/src/template"
    fi
    [ -d "$source_dir" ] || fail 'Arşivde template klasörü bulunamadı.'
fi

waypoint="$target/.waypoint"
if [ -d "$waypoint" ]; then
    for file in KURALLAR.md .gitattributes .gitignore; do cp "$source_dir/.waypoint/$file" "$waypoint/$file"; done
    mkdir -p "$waypoint/hooks"
    find "$waypoint/hooks" -mindepth 1 -maxdepth 1 -type f -exec rm -f {} \;
    find "$source_dir/.waypoint/hooks" -type f ! -path '*/__pycache__/*' -exec cp {} "$waypoint/hooks/" \;
    for file in ILERLEME.md DERSLER.md HARITA.md; do [ -e "$waypoint/$file" ] || cp "$source_dir/.waypoint/$file" "$waypoint/$file"; done
    result='güncellendi'
else
    cp -R "$source_dir/.waypoint" "$waypoint"
    find "$waypoint" -type d -name __pycache__ -prune -exec rm -rf {} \;
    result='kuruldu'
fi

for file in AGENTS.md CLAUDE.md; do
    pointer='.waypoint/KURALLAR.md'
    [ "$file" = CLAUDE.md ] && pointer='.waypoint/KURALLAR.md'
    if [ ! -f "$target/$file" ]; then cp "$source_dir/$file" "$target/$file"
    elif ! grep -Fq "$pointer" "$target/$file"; then printf '\n' >> "$target/$file"; cat "$source_dir/$file" >> "$target/$file"; fi
done

if ! git -C "$target" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git -C "$target" init >/dev/null || fail 'Git deposu başlatılamadı.'
    info 'Kayıt noktası alabilmek için git kurdum.'
fi
old_hooks=$(git -C "$target" config --get core.hooksPath 2>/dev/null || true)
if [ -n "$old_hooks" ] && [ "$old_hooks" != ".waypoint/hooks" ]; then
    info "Uyarı: Bu projede önceden başka bir kayıt kontrolü klasörü vardı ($old_hooks). Waypoint onun yerine geçti; eski kontroller artık çalışmayacak."
elif [ -z "$old_hooks" ] && [ -n "$(find "$target/.git/hooks" -maxdepth 1 -type f ! -name '*.sample' 2>/dev/null | head -n 1)" ]; then
    info "Uyarı: Bu projenin .git/hooks klasöründe önceden kayıt kontrolleri vardı. Waypoint onların yerine geçti; eski kontroller artık çalışmayacak."
fi
git -C "$target" config core.hooksPath .waypoint/hooks || fail 'Git hook yolu ayarlanamadı.'
chmod +x "$waypoint/hooks"/* 2>/dev/null || true

python_ok=
for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 && "$candidate" --version >/dev/null 2>&1; then python_ok=1; break; fi
done
if [ -z "$python_ok" ] && command -v py >/dev/null 2>&1 && py -3 --version >/dev/null 2>&1; then python_ok=1; fi
[ -n "$python_ok" ] || info 'Uyarı: Python 3 kurulana kadar kural kontrolleri atlanacak. https://www.python.org/downloads/'
info "Waypoint $result."
info 'Bu klasörde yapay zekâ aracını (Claude Code, Codex, Antigravity…) aç ve ne yapmak istediğini anlat.'
