"""Pre-commit denetimleri için saf doğrulama fonksiyonları."""

from __future__ import annotations

import re
import subprocess
import sys
from datetime import date
from pathlib import Path


def gizli_dosyalar(staged_names: list[str]) -> tuple[list[str], list[str]]:
    """Commit'e eklenen gizli anahtar ve ortam dosyalarını bulur."""
    hatalar: list[str] = []
    for name in staged_names:
        basename = name.replace("\\", "/").rsplit("/", 1)[-1]
        blocked = (
            (basename.startswith(".env") and basename != ".env.example")
            or basename.endswith((".pem", ".key"))
            or basename.startswith("id_rsa")
        )
        if blocked:
            hatalar.append(
                f"{name}: gizli dosyayı commit'ten çıkarın ve .gitignore dosyasına ekleyin."
            )
    return hatalar, []


def _section(text: str, heading: str) -> str:
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if line.startswith("## ") and line[3:].startswith(heading)), None)
    if start is None:
        return ""
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    return "\n".join(lines[start + 1 : end])


def _without_html_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


def harita(text: str) -> tuple[list[str], list[str]]:
    """Karşılaştırır: önemli işlev listesi ve Mermaid şemalarındaki düğümler."""
    hatalar: list[str] = []
    entries_section = _without_html_comments(_section(text, "Key functions / components"))
    entries = re.findall(r"^###\s+(.+?)\s+—\s+(.+?)\s*$", entries_section, flags=re.MULTILINE)
    entry_names = {name.strip() for name, _ in entries}
    entry_files = {filename.strip() for _, filename in entries}

    schema_section = _section(text, "Şema")
    blocks = re.findall(r"```mermaid\s*\n(.*?)```", schema_section, flags=re.DOTALL)
    node_names: set[str] = set()
    for block_number, block in enumerate(blocks, start=1):
        ids: dict[str, str] = {}
        for line in block.splitlines():
            if re.match(r"^\s*subgraph\b", line):
                continue
            for match in re.finditer(r'\b([A-Za-z_][\w]*)\["([^"]*)"\]', line):
                ids[match.group(1)] = match.group(2).split("<br", 1)[0].strip()
        node_names.update(ids.values())
        if len(ids) > 15:
            hatalar.append(
                f".waypoint/HARITA.md: {block_number}. Mermaid şemasında {len(ids)} düğüm var; "
                "şemayı böl: önce dosyalar, sonra dosya başına küçük şema."
            )

    for name, _ in entries:
        name = name.strip()
        if name not in node_names:
            hatalar.append(f".waypoint/HARITA.md: '{name}' listede var, şemada yok; işlevi şemaya ekleyin.")
    for node_name in sorted(node_names):
        if node_name not in entry_names and node_name not in entry_files:
            hatalar.append(f".waypoint/HARITA.md: '{node_name}' şemada var, listede yok; listeye ekleyin veya düğümü kaldırın.")
    return hatalar, []


def dersler(text: str) -> tuple[list[str], list[str]]:
    """Kurallar bölümündeki etkin kural sayısını sınırlar."""
    rules = _section(text, "Kurallar")
    count = sum(1 for line in rules.splitlines() if line.startswith("- ") and line != "- ...")
    if count > 20:
        return [f".waypoint/DERSLER.md: Kurallar bölümünde {count} kural var; 20'yi aşan kuralları azaltın veya birleştirin."], []
    return [], []


_REQUIRED_HEADINGS = (
    "Proje hedefi", "Aşama", "Nasıl açılır", "Testleri çalıştırma", "Kararlar",
    "Plan", "Şu anki görev", "Sıradaki adım", "Sonra yapılacaklar", "Günlük",
)


def ilerleme(text: str) -> tuple[list[str], list[str]]:
    """İlerleme belgesindeki zorunlu başlıkları ve günlük uzunluğunu denetler."""
    hatalar: list[str] = []
    headings = [line[3:].strip() for line in text.splitlines() if line.startswith("## ")]
    for required in _REQUIRED_HEADINGS:
        if not any(heading.startswith(required) for heading in headings):
            hatalar.append(f".waypoint/ILERLEME.md: '{required}' başlığı eksik; bu başlığı ekleyin.")

    daily = _section(text, "Günlük")
    count = sum(
        1 for line in daily.splitlines()
        if line.startswith("- ") and "YYYY" not in line
    )
    uyarilar = []
    if count > 10:
        uyarilar.append(
            f".waypoint/ILERLEME.md: Günlük bölümünde {count} kayıt var; eski kayıtları .waypoint/GUNLUK_ARSIV.md dosyasına taşı."
        )
    return hatalar, uyarilar


def _is_code_file(name: str) -> bool:
    normalized = name.replace("\\", "/")
    basename = normalized.rsplit("/", 1)[-1]
    return (
        not normalized.startswith(".waypoint/")
        and not basename.endswith(".md")
        and basename not in {".gitignore", ".gitattributes"}
    )


def _is_test_file(name: str) -> bool:
    return _is_code_file(name) and bool(re.search(r"test|spec", name.rsplit("/", 1)[-1], re.IGNORECASE))


def ilerleme_bugun(ilerleme_text: str, today: str, staged_names: list[str]) -> tuple[list[str], list[str]]:
    if any(_is_code_file(name) for name in staged_names):
        daily = _section(ilerleme_text, "Günlük")
        if not any(line.startswith(f"- {today}") for line in daily.splitlines()):
            return [
                f".waypoint/ILERLEME.md: kod değişti ama Günlük bölümünde bugünün ({today}) satırı yok; '- {today}: ne yapıldı' satırını ekleyip aynı kayda dahil edin."
            ], []
    return [], []


_FUNCTION_PATTERNS = (
    re.compile(r"^\+\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s*\*?\s*([A-Za-z_$][\w$]*)", re.MULTILINE),
    re.compile(r"^\+\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s+)?(?:function\b|\([^)]*\)\s*=>|[A-Za-z_$][\w$]*\s*=>)", re.MULTILINE),
    re.compile(r"^\+\s*(?:async\s+)?def\s+([A-Za-z_]\w*)", re.MULTILINE),
    re.compile(r"^\+\s*(?:export\s+)?class\s+([A-Za-z_$][\w$]*)", re.MULTILINE),
)


def yeni_fonksiyonlar(diff_text: str) -> list[str]:
    names: set[str] = set()
    added_lines = []
    for line in diff_text.splitlines():
        if not line.startswith("+") or line.startswith("+++"):
            continue
        added_lines.append(line)
    added_text = "\n".join(added_lines)
    for pattern in _FUNCTION_PATTERNS:
        names.update(pattern.findall(added_text))
    return sorted(names)


def harita_kapsami(harita_text: str, names: list[str]) -> tuple[list[str], list[str]]:
    missing = [
        name for name in names
        if not re.search(rf"(?<![\w$]){re.escape(name)}(?![\w$])", harita_text)
    ]
    return [
        f".waypoint/HARITA.md: yeni fonksiyon '{name}' haritada yok. Önemliyse listeye ve şemaya ekleyin; küçük bir yardımcıysa '## Not mapped (small helpers)' satırına adını yazın."
        for name in missing
    ], []


def ders_hatirlatma(message_text: str) -> tuple[list[str], list[str]]:
    normalized = message_text.replace("İ", "i").replace("I", "ı").lower()
    if any(word in normalized for word in ("düzelt", "hata", "fix", "bug", "onar")):
        return [], [
            "Bu bir düzeltme kaydı. Hata 2 denemeden uzun sürdüyse ya da kullanıcı sizi düzelttiyse .waypoint/DERSLER.md dosyasına ders yazın."
        ]
    return [], []


def _git_output(root: Path, *args: str) -> list[str]:
    result = subprocess.run(
        ["git", "-c", "core.quotepath=false", *args],
        cwd=root, check=True, capture_output=True, encoding="utf-8", errors="replace",
    )
    return result.stdout.splitlines()


def main() -> int:
    # Windows konsolu emoji ve Türkçe karakterleri bozmasın
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    root = Path(__file__).resolve().parents[2]  # <proje>/.waypoint/hooks/kontrol.py
    if len(sys.argv) == 3 and sys.argv[1] == "--mesaj":
        try:
            message = Path(sys.argv[2]).read_text(encoding="utf-8")
        except OSError:
            return 0
        _, warnings = ders_hatirlatma(message)
        for warning in warnings:
            print(f"⚠️ {warning}")
        return 0
    try:
        staged = _git_output(root, "diff", "--cached", "--name-only", "--diff-filter=ACMR")
    except (subprocess.CalledProcessError, OSError) as exc:
        print(f"❌ .waypoint/hooks/kontrol.py: Git deposu okunamadı; hook'u depo içinden çalıştırın. ({exc})")
        return 1

    hatalar, uyarilar = gizli_dosyalar(staged)
    today = date.today().isoformat()
    for path, check in ((".waypoint/HARITA.md", harita), (".waypoint/DERSLER.md", dersler), (".waypoint/ILERLEME.md", ilerleme)):
        file_path = root / path
        if file_path.is_file():
            file_text = file_path.read_text(encoding="utf-8")
            errors, warnings = check(file_text)
            hatalar.extend(errors)
            uyarilar.extend(warnings)
            if path == ".waypoint/ILERLEME.md":
                errors, warnings = ilerleme_bugun(file_text, today, staged)
                hatalar.extend(errors)
                uyarilar.extend(warnings)
    map_path = root / ".waypoint/HARITA.md"
    if map_path.is_file():
        code_paths = [name for name in staged if _is_code_file(name) and not _is_test_file(name)]
        if code_paths:
            try:
                diff_text = "\n".join(_git_output(root, "diff", "--cached", "-U0", "--diff-filter=ACMR", "--", *code_paths))
            except (subprocess.CalledProcessError, OSError):
                diff_text = ""
            errors, warnings = harita_kapsami(map_path.read_text(encoding="utf-8"), yeni_fonksiyonlar(diff_text))
            hatalar.extend(errors)
            uyarilar.extend(warnings)
    for hata in hatalar:
        print(f"❌ {hata}")
    for uyari in uyarilar:
        print(f"⚠️ {uyari}")
    if hatalar:
        return 1
    print("✅ .waypoint/hooks/kontrol.py: Belgeler ve gizli dosya denetimleri geçti.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
