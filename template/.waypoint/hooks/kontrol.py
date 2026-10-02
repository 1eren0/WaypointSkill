"""Pre-commit denetimleri için saf doğrulama fonksiyonları."""

from __future__ import annotations

import re
import subprocess
import sys
from datetime import date
from pathlib import Path


_MOJIBAKE_SOURCE = "\u00e7\u011f\u0131\u00f6\u015f\u00fc\u00c7\u011e\u0130\u00d6\u015e\u00dc\u00e2\u00ee\u00fb\u00c2\u00ce\u00db\u2019\u2018\u201c\u201d\u2013\u2014\u2026\u20ac"
_EMOJI_PREFIX = "\U0001f600".encode("utf-8").decode("cp1252", errors="ignore")[:2]
_MOJIBAKE = tuple(
    dict.fromkeys(
        corrupted
        for char in _MOJIBAKE_SOURCE + _EMOJI_PREFIX
        for encoding in ("cp1252", "cp1254", "latin-1")
        if len(corrupted := char.encode("utf-8").decode(encoding, errors="ignore")) >= 2
        and corrupted != char
    )
)
_BAD_REPLACEMENT = "\ufffd"
_BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".webp", ".bmp", ".pdf", ".zip", ".gz",
    ".tar", ".7z", ".db", ".sqlite", ".sqlite3", ".woff", ".woff2", ".ttf", ".otf",
    ".eot", ".exe", ".dll", ".so", ".pyc", ".mp3", ".mp4", ".wav", ".mov",
}


def _bad_at(line: str) -> tuple[int, str] | None:
    candidates = [(line.find(_BAD_REPLACEMENT), _BAD_REPLACEMENT)] if _BAD_REPLACEMENT in line else []
    candidates.extend((line.find(pattern), pattern) for pattern in _MOJIBAKE if pattern in line)
    return min(candidates, key=lambda item: item[0]) if candidates else None


def bozuk_metin(name: str, text: str) -> tuple[list[str], list[str]]:
    for line_no, line in enumerate(text.splitlines(), start=1):
        found = _bad_at(line)
        if found is None:
            continue
        position, bad = found
        start, end = max(0, position - 12), min(len(line), position + len(bad) + 12)
        snippet = line[start:position] + repr(line[position:position + len(bad)]) + line[position + len(bad):end]
        return [f"{name}: {line_no}. satırda bozuk karakter var ({snippet}). Dosyayı UTF-8 olarak yeniden yazın; Türkçe harfleri düzeltin."], []
    return [], []


def bozuk_dosya(name: str, data: bytes) -> tuple[list[str], list[str]]:
    normalized = name.replace("\\", "/")
    if ".waypoint/hooks/" in f"/{normalized}/":
        return [], []
    if Path(name).suffix.lower() in _BINARY_EXTENSIONS or b"\x00" in data[:8000]:
        return [], []
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    try:
        decoded = data.decode("utf-8")
    except UnicodeDecodeError:
        return [f"{name}: dosya UTF-8 değil (bozuk bayt). Dosyayı UTF-8 olarak kaydedin."], []
    return bozuk_metin(name, decoded)


def gizli_dosyalar(staged_names: list[str]) -> tuple[list[str], list[str]]:
    """Commit'e eklenen gizli anahtar ve ortam dosyalarını bulur."""
    hatalar: list[str] = []
    for name in staged_names:
        basename = name.replace("\\", "/").rsplit("/", 1)[-1]
        lower = basename.lower()
        sample = lower.endswith((".example", ".sample", ".template"))
        blocked = not sample and (
            (basename.startswith(".env") and basename != ".env.example")
            or basename.endswith((".pem", ".key"))
            or lower.startswith(("id_rsa", "id_ed25519", "id_ecdsa", "id_dsa"))
            or lower in {"credentials.json", "secrets.json", "secrets.yml", "secrets.yaml", ".npmrc", ".pypirc", ".netrc", ".htpasswd"}
            or lower.endswith((".p12", ".pfx", ".jks", ".keystore", ".ppk", ".asc", ".ovpn"))
            or bool(re.fullmatch(r"client_secret.*\.json", lower))
            or bool(re.fullmatch(r"service-account.*\.json", lower))
            or bool(re.fullmatch(r"serviceaccount.*\.json", lower))
            or lower.endswith("-service-account.json")
        )
        if blocked:
            hatalar.append(
                f"{name}: gizli dosyayı commit'ten çıkarın ve .gitignore dosyasına ekleyin."
            )
    return hatalar, []


_SECRET_PATTERNS = (
    (re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP |ENCRYPTED )?PRIVATE KEY"), "\u00f6zel anahtar"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS anahtar\u0131"),
    (re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{60,}"), "GitHub anahtar\u0131"),
    (re.compile(r"sk-(?:ant-)?[A-Za-z0-9_-]{32,}"), "yapay zek\u00e2 API anahtar\u0131"),
    (re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"), "Slack anahtar\u0131"),
    (re.compile(r"AIza[0-9A-Za-z_-]{35}"), "Google API anahtar\u0131"),
)
_ASSIGNMENT_SECRET = re.compile(r"(?i)(password|passwd|secret|api_key|apikey|token)\s*[:=]\s*([\"'][^\"'\s]{8,}[\"'])")


def gizli_icerik(name: str, text: str) -> tuple[list[str], list[str]]:
    normalized = name.replace("\\", "/")
    basename = normalized.rsplit("/", 1)[-1].lower()
    if "/.waypoint/hooks/" in f"/{normalized}/" or basename.endswith((".example", ".sample", ".template", ".md")):
        return [], []
    placeholders = ("xxx", "<", "your", "example", "changeme", "***", "${", "process.env", "os.environ")
    for line_no, line in enumerate(text.splitlines(), 1):
        for pattern, kind in _SECRET_PATTERNS:
            if pattern.search(line):
                return [f"{name}: {line_no}. sat\u0131rda gizli anahtar/\u015fifre olabilir ({kind}). Bu de\u011feri dosyadan \u00e7\u0131kar\u0131n, .env gibi kayda girmeyen bir dosyaya ta\u015f\u0131y\u0131n."], []
        match = None if _is_test_file(normalized) else _ASSIGNMENT_SECRET.search(line)  # testlerde sahte şifreler olağan
        if match and not any(value in match.group(2).lower() for value in placeholders):
            return [f"{name}: {line_no}. sat\u0131rda gizli anahtar/\u015fifre olabilir (\u015fifre/anahtar atamas\u0131). Bu de\u011feri dosyadan \u00e7\u0131kar\u0131n, .env gibi kayda girmeyen bir dosyaya ta\u015f\u0131y\u0131n."], []
    return [], []


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
    hatalar = []
    if count > 20:
        hatalar.append(f".waypoint/DERSLER.md: Kurallar bölümünde {count} kural var; 20'yi aşan kuralları azaltın veya birleştirin.")
    records = _section(text, "Kayıtlar")
    lessons = sum(
        1 for line in records.splitlines()
        if line.startswith("### ") and "YYYY" not in line
    )
    message = (
        f".waypoint/DERSLER.md: Kayıtlar bölümünde {lessons} ders var; "
        "kuralı 'Kurallar' bölümünde duran eski dersleri .waypoint/DERS_ARSIV.md dosyasına taşıyın."
    )
    if lessons > 30:
        hatalar.append(message + " Bu yapılmadan kayıt alınamaz.")
        return hatalar, []
    if lessons > 20:
        return hatalar, [message]
    return hatalar, []


_REQUIRED_HEADINGS = (
    "Proje hedefi", "Aşama", "Nasıl açılır", "Testleri çalıştırma", "Kararlar",
    "Plan", "Şu anki görev", "Sıradaki adım", "Sonra yapılacaklar", "Günlük",
)


def ilerleme(text: str) -> tuple[list[str], list[str]]:
    """İlerleme belgesindeki zorunlu başlıkları ve bölüm uzunluklarını denetler."""
    hatalar: list[str] = []
    headings = [line[3:].strip() for line in text.splitlines() if line.startswith("## ")]
    for required in _REQUIRED_HEADINGS:
        if not any(heading.startswith(required) for heading in headings):
            hatalar.append(f".waypoint/ILERLEME.md: '{required}' başlığı eksik; bu başlığı ekleyin.")

    uyarilar = []
    limits = (
        ("Günlük", 10, 20, "Günlük", "kayıt", "en yeni 10 satır kalsın, eskileri .waypoint/ILERLEME_ARSIV.md dosyasının '## Günlük' bölümüne taşıyın."),
        ("Plan", 10, 20, "Plan", "biten görev", "biten görevleri .waypoint/ILERLEME_ARSIV.md dosyasının '## Biten görevler' bölümüne taşıyın."),
        ("Kararlar", 20, 30, "Kararlar", "karar", "en eski kararları .waypoint/ILERLEME_ARSIV.md dosyasının '## Kararlar' bölümüne taşıyın (arşivdeki kararlar geçerliliğini korur)."),
        ("Sonra yapılacaklar", 15, 25, "'Sonra yapılacaklar'", "madde", "kullanıcıya hangilerinden vazgeçildiğini sorun ve onları .waypoint/ILERLEME_ARSIV.md dosyasının '## Vazgeçilen fikirler' bölümüne taşıyın."),
    )
    for heading, warning_limit, error_limit, label, noun, action in limits:
        section = _section(text, heading)
        if heading == "Plan":
            count = sum(
                1 for line in section.splitlines()
                if line.startswith(("- [x]", "- [X]")) and "YYYY" not in line and line != "- ..."
            )
        else:
            count = sum(
                1 for line in section.splitlines()
                if line.startswith("- ") and "YYYY" not in line and line != "- ..."
            )
        if count > warning_limit:
            message = f".waypoint/ILERLEME.md: {label} bölümünde {count} {noun} var; {action}"
            if count > error_limit:
                hatalar.append(message + " Bu yapılmadan kayıt alınamaz.")
            else:
                uyarilar.append(message)
    return hatalar, uyarilar


def fikirler(ilerleme_text: str, fikirler_text: str | None) -> tuple[list[str], list[str]]:
    """'Sonra yapılacaklar' yer tutucuları ile FIKIRLER.md başlıklarını eşleştirir."""
    parked = _without_html_comments(_section(ilerleme_text, "Sonra yapılacaklar"))
    refs = {name.strip() for name in re.findall(r"FIKIRLER\.md\s*[›>]\s*(.+?)\s*$", parked, flags=re.MULTILINE)}
    sections = set() if fikirler_text is None else {
        line[3:].strip() for line in _without_html_comments(fikirler_text).splitlines() if line.startswith("## ")
    }
    hatalar = [
        f".waypoint/FIKIRLER.md: '{name}' için ayrıntı başlığı yok; '## {name}' başlığını ekleyin veya ILERLEME.md'deki yer tutucuyu düzeltin."
        for name in sorted(refs - sections)
    ]
    hatalar += [
        f".waypoint/FIKIRLER.md: '## {name}' bölümü 'Sonra yapılacaklar'da yok; fikir yapıldıysa veya vazgeçildiyse bu bölümü silin."
        for name in sorted(sections - refs)
    ]
    return hatalar, []


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


def kayit_turu(message_text: str, staged_names: list[str], test_komutu_var: bool) -> tuple[list[str], list[str]]:
    lines = [line for line in message_text.splitlines() if line.strip() and not line.startswith("#")]
    if not lines:
        return ["Kayıt mesajı İngilizce olmalı ve Conventional Commits biçiminde başlamalı: 'feat:', 'fix:', 'docs:', 'refactor:', 'test:', 'chore:', 'style:' veya 'perf:'. Örnek: 'feat: add login button', 'fix: prevent empty tasks'"], []
    subject = lines[0]
    if subject.startswith(("Merge ", 'Revert "', "fixup!", "squash!")):
        return [], []
    match = re.match(r"^(feat|fix|docs|refactor|test|chore|style|perf)(?:\([\w./-]+\))?!?: (\S.*)", subject)
    if not match:
        return ["Kayıt mesajı İngilizce olmalı ve Conventional Commits biçiminde başlamalı: 'feat:', 'fix:', 'docs:', 'refactor:', 'test:', 'chore:', 'style:' veya 'perf:'. Örnek: 'feat: add login button', 'fix: prevent empty tasks'"], []
    kind = match.group(1)
    code_names = [name for name in staged_names if _is_code_file(name)]
    description = match.group(2)
    if any(char in description for char in "ğĞışŞİ"):
        return ["Kayıt mesajı İngilizce olmalı; Türkçe açıklamayı İngilizceye çevirin."], []
    test_names = [name for name in code_names if _is_test_file(name)]
    if kind == "docs" and code_names:
        return ["'docs:' türü yalnız .waypoint/ ve .md dosyaları içindir; türü düzeltin ya da kod değişikliğini ayrı kayda alın."], []
    if kind == "test" and any(not _is_test_file(name) for name in code_names):
        return ["'test:' türü yalnız test dosyaları içindir; diğer kod değişikliklerini ayrı kayda alın."], []
    if (kind == "fix" and test_komutu_var and code_names
            and not test_names
            and "no test:" not in message_text.lower() and "test yok:" not in message_text.lower()):
        return ["'fix:' kaydında bu hatayı yakalayan bir test olmalı. Test ekleyin; test yazılamıyorsa mesaja '(no test: <reason>)' ekleyin."], []
    return [], []


def test_komutu(ilerleme_text: str) -> bool:
    section = _section(ilerleme_text, "Testleri çalıştırma")
    return any(command.strip() not in {"...", "…"} for command in re.findall(r"`([^`]+)`", section))


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
    re.compile(r"^\+\s*func\s+(?:\([^)]*\)\s*)?([A-Za-z_]\w*)\s*\(", re.MULTILINE),
    re.compile(r"^\+\s*(?:(?:pub(?:\(crate\))?|async)\s+)*fn\s+([A-Za-z_]\w*)\s*\(", re.MULTILINE),
    re.compile(r"^\+\s*(?:(?:private|public|internal|override|suspend|static)\s+)*(?:fun|func)\s+([A-Za-z_]\w*)\s*\(", re.MULTILINE),
    re.compile(r"^\+\s*(?:(?:public|private|protected|internal|static|final|abstract|override|virtual|async|synchronized|readonly)\s+)+[\w<>\[\],.?]+\s+(\w+)\s*\(", re.MULTILINE),
    re.compile(r"^\+\s*(?:(?:public|private|protected|static|async|readonly)\s+)+(\w+)\s*\(", re.MULTILINE),
    re.compile(r"^\+\s{2,}(?:async\s+)?(\w+)\s*\([^)]*\)\s*\{\s*$", re.MULTILINE),
    re.compile(r"^\+\s*def\s+(?:self\.)?([A-Za-z_]\w*)\b", re.MULTILINE),
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
    names.difference_update({"if", "for", "while", "switch", "catch", "function", "return", "else", "do", "try", "with", "constructor"})
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


def _git_bytes(root: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "-c", "core.quotepath=false", *args],
        cwd=root, check=True, capture_output=True,
    )
    return result.stdout


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
        try:
            staged_names = _git_output(root, "diff", "--cached", "--name-only", "--diff-filter=ACMR")
        except (subprocess.CalledProcessError, OSError):
            staged_names = []
        progress_path = root / ".waypoint" / "ILERLEME.md"
        try:
            progress_text = progress_path.read_text(encoding="utf-8")
        except OSError:
            progress_text = ""
        errors, warnings = kayit_turu(message, staged_names, test_komutu(progress_text))
        text_errors, _ = bozuk_metin("Kayıt mesajı", message)
        errors.extend(text_errors)
        _, lesson_warnings = ders_hatirlatma(message)
        warnings.extend(lesson_warnings)
        for error in errors:
            print(f"❌ {error}")
        for warning in warnings:
            print(f"⚠️ {warning}")
        return 1 if errors else 0
    try:
        staged = _git_output(root, "diff", "--cached", "--name-only", "--diff-filter=ACMR")
    except (subprocess.CalledProcessError, OSError) as exc:
        print(f"❌ .waypoint/hooks/kontrol.py: Git deposu okunamadı; hook'u depo içinden çalıştırın. ({exc})")
        return 1

    hatalar, uyarilar = gizli_dosyalar(staged)
    for name in staged:
        try:
            data = _git_bytes(root, "show", f":{name}")
        except (subprocess.CalledProcessError, OSError):
            continue
        errors, _ = bozuk_dosya(name, data)
        hatalar.extend(errors)
        if Path(name).suffix.lower() not in _BINARY_EXTENSIONS and b"\x00" not in data[:8000]:
            secrets, _ = gizli_icerik(name, data.decode("utf-8", errors="ignore"))
            hatalar.extend(secrets)
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
                ideas_path = root / ".waypoint/FIKIRLER.md"
                ideas_text = ideas_path.read_text(encoding="utf-8") if ideas_path.is_file() else None
                errors, _ = fikirler(file_text, ideas_text)
                hatalar.extend(errors)
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
