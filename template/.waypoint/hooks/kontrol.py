"""Pre-commit denetimleri için saf doğrulama fonksiyonları."""

from __future__ import annotations

import http.client
import os
import re
import signal
import subprocess
import sys
import tempfile
import urllib.request
from datetime import date, datetime, timedelta
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


def _eksik_basliklar(text: str, file_name: str, required: tuple[str, ...]) -> list[str]:
    """Zorunlu '## ' başlıklarını arar; başlık bozulursa (ör. 'Şema' → '?ema') denetim boşuna geçmesin."""
    headings = [line[3:].strip() for line in text.splitlines() if line.startswith("## ")]
    return [
        f".waypoint/{file_name}: '{heading}' başlığı eksik; bu başlığı ekleyin (Türkçe harfler bozulduysa dosyayı UTF-8 olarak düzeltin)."
        for heading in required
        if not any(found.startswith(heading) for found in headings)
    ]


def _without_html_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


def _harita_girdileri(text: str) -> list[tuple[str, str]]:
    """'### fonksiyon() — dosya' girdilerini (ad, dosya) olarak döndürür."""
    section = _without_html_comments(_section(text, "Key functions / components"))
    return [
        (name.strip(), path.strip())
        for name, path in re.findall(r"^###\s+(.+?)\s+—\s+(.+?)\s*$", section, flags=re.MULTILINE)
    ]


def _kimlik(name: str) -> str:
    """'Kullanici.kaydet()' gibi bir girdi adından koddaki çıplak adı çıkarır: 'kaydet'."""
    return re.split(r"[.:]+", name.split("(", 1)[0].strip())[-1]


def _kelime_var(name: str, text: str) -> bool:
    return bool(re.search(rf"(?<![\w$]){re.escape(name)}(?![\w$])", text))


# Desteklenen kutu biçimleri: id["etiket"], id[etiket], id("etiket"), id(etiket), id{"etiket"}, id{etiket}
_MERMAID_NODE = re.compile(
    r'\b([A-Za-z_]\w*)(?:\["([^"]*)"\]|\[([^\]"]+)\]|\("([^"]*)"\)|\(([^)"]+)\)|\{"([^"]*)"\}|\{([^}"]+)\})'
)


def harita(text: str) -> tuple[list[str], list[str]]:
    """Karşılaştırır: önemli işlev listesi ve Mermaid şemalarındaki düğümler."""
    hatalar = _eksik_basliklar(text, "HARITA.md", ("Şema", "Key functions / components"))
    entries = _harita_girdileri(text)
    entry_names = {name for name, _ in entries}
    entry_files = {path for _, path in entries}

    schema_section = _section(text, "Şema")
    blocks = re.findall(r"```mermaid\s*\n(.*?)```", schema_section, flags=re.DOTALL)
    node_names: set[str] = set()
    for block_number, block in enumerate(blocks, start=1):
        ids: dict[str, str] = {}
        for line in block.splitlines():
            if re.match(r"^\s*(?:subgraph|click|style|classDef|class|linkStyle)\b", line):
                continue
            for match in _MERMAID_NODE.finditer(line):
                label = next(group for group in match.groups()[1:] if group is not None)
                ids[match.group(1)] = label.split("<br", 1)[0].strip()
        node_names.update(ids.values())
        if len(ids) > 15:
            hatalar.append(
                f".waypoint/HARITA.md: {block_number}. Mermaid şemasında {len(ids)} düğüm var; "
                "şemayı böl: önce dosyalar, sonra dosya başına küçük şema."
            )

    for name, _ in entries:
        if name not in node_names:
            hatalar.append(f".waypoint/HARITA.md: '{name}' listede var, şemada yok; işlevi şemaya ekleyin.")
    for node_name in sorted(node_names):
        if node_name not in entry_names and node_name not in entry_files:
            hatalar.append(f".waypoint/HARITA.md: '{node_name}' şemada var, listede yok; listeye ekleyin veya düğümü kaldırın.")
    return hatalar, []


def harita_gercek(text: str, read_file) -> tuple[list[str], list[str]]:
    """Haritadaki her 'fonksiyon — dosya' girdisinin o dosyada hâlâ bulunduğunu doğrular."""
    hatalar: list[str] = []
    for name, path in _harita_girdileri(text):
        if name == path:  # genel şemadaki dosya kutusu
            continue
        source = read_file(path)
        if source is None:
            hatalar.append(
                f".waypoint/HARITA.md: '{name}' için yazılan '{path}' dosyası yok; yolu proje köküne göre düzeltin "
                "ya da fonksiyon kaldırıldıysa girdiyi listeden ve şemadan silin."
            )
        elif not _kelime_var(_kimlik(name), source):
            hatalar.append(
                f".waypoint/HARITA.md: '{name}' artık {path} içinde yok; fonksiyon silindiyse ya da adı veya dosyası "
                "değiştiyse haritayı (listeyi ve şemayı) düzeltin."
            )
    return hatalar, []


def dersler(text: str) -> tuple[list[str], list[str]]:
    """Kurallar bölümündeki etkin kural sayısını sınırlar."""
    hatalar = _eksik_basliklar(text, "DERSLER.md", ("Kurallar", "Kayıtlar"))
    rules = _section(text, "Kurallar")
    count = sum(1 for line in rules.splitlines() if line.startswith("- ") and line != "- ...")
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
    hatalar = _eksik_basliklar(text, "ILERLEME.md", _REQUIRED_HEADINGS)

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


_WAYPOINT_FILES = {
    "KURALLAR.md", "ILERLEME.md", "ILERLEME_ARSIV.md", "DERSLER.md", "DERS_ARSIV.md",
    "HARITA.md", "FIKIRLER.md", "WAYPOINT_GUNLUGU.md", "VERSION", ".gitattributes", ".gitignore",
    "guncelle.bat", "guncelle.command",
}


def waypoint_duzeni(staged_names: list[str]) -> tuple[list[str], list[str]]:
    """.waypoint/ içine yalnız Waypoint dosyalarının ve tarihli raporların girmesini sağlar."""
    hatalar: list[str] = []
    for name in staged_names:
        parts = name.replace("\\", "/").split("/")
        if parts[0] != ".waypoint" or len(parts) < 2 or parts[1] == "hooks":
            continue
        if len(parts) == 2 and parts[1] in _WAYPOINT_FILES:
            continue
        if len(parts) == 3 and parts[1] == "komutlar" and parts[2].endswith(".md"):  # Waypoint'in komut tarifleri
            continue
        if parts[1] == "raporlar" and len(parts) >= 3:
            if re.match(r"^\d{4}-\d{2}-\d{2}-.+", parts[2]) and (len(parts) > 3 or parts[2].endswith(".md")):
                continue
            hatalar.append(
                f"{name}: rapor adı tarihle başlamalı. Tek dosya için .waypoint/raporlar/YYYY-AA-GG-<konu>.md, "
                "çok dosya için .waypoint/raporlar/YYYY-AA-GG-<konu>/ klasörünü kullanın."
            )
            continue
        hatalar.append(
            f"{name}: .waypoint/ içinde Waypoint'e ait olmayan dosya. Raporsa .waypoint/raporlar/YYYY-AA-GG-<konu>.md "
            "(çok dosyaysa YYYY-AA-GG-<konu>/ klasörü) olarak taşıyın; değilse proje klasörüne taşıyın."
        )
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
    normalized = name.replace("\\", "/")
    return _is_code_file(name) and bool(
        re.search(r"test|spec", normalized.rsplit("/", 1)[-1], re.IGNORECASE)
        or re.search(r"(^|/)(tests?|__tests__|specs?)/", normalized, re.IGNORECASE)
    )


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


def test_komutunu_bul(ilerleme_text: str) -> str | None:
    """'Testleri çalıştırma' altındaki ilk `komut`; yoksa ya da hâlâ '...' ise None."""
    match = re.search(r"`([^`\n]+)`", _section(ilerleme_text, "Testleri çalıştırma"))
    command = match.group(1).strip() if match else ""
    return None if command in {"", "...", "…"} else command


def test_komutu_uyarisi(ilerleme_text: str, staged_names: list[str]) -> list[str]:
    """Kod değişti ama test komutu yoksa testler hiç çalışmaz; bu sessizce geçmesin."""
    if test_komutunu_bul(ilerleme_text) is not None or not any(_is_code_file(name) for name in staged_names):
        return []
    return [
        "Testler çalışmadı: .waypoint/ILERLEME.md › 'Testleri çalıştırma' altında test komutu yok. Önemli özellikler "
        "için test yazın ve komutu oraya ekleyin; o zamana kadar bozulan eski özellikler kayıtta yakalanmaz."
    ]


TEST_SURESI = 300  # saniye; WAYPOINT_TEST_TIMEOUT ile değişir

# Git, hook'a kaydı alınan deponun yerini bu ayarlarla verir (`git rev-parse --local-env-vars`).
# Testlere geçerse, testlerin geçici depolarda çalıştırdığı git komutları gerçek depoyu değiştirir.
_GIT_DEPO_AYARLARI = frozenset({
    "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_CONFIG", "GIT_CONFIG_PARAMETERS", "GIT_CONFIG_COUNT",
    "GIT_OBJECT_DIRECTORY", "GIT_DIR", "GIT_WORK_TREE", "GIT_IMPLICIT_WORK_TREE", "GIT_GRAFT_FILE",
    "GIT_INDEX_FILE", "GIT_NO_REPLACE_OBJECTS", "GIT_REPLACE_REF_BASE", "GIT_PREFIX", "GIT_SHALLOW_FILE",
    "GIT_COMMON_DIR", "GIT_NAMESPACE",
})


def _sureci_kapat(process: subprocess.Popen) -> None:
    """Test komutunu, başlattığı alt süreçlerle (node, python…) birlikte kapatır."""
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], capture_output=True, timeout=30)
        else:
            os.killpg(process.pid, signal.SIGKILL)
    except (OSError, subprocess.SubprocessError):
        pass
    try:
        process.kill()
        process.wait(timeout=10)
    except (OSError, subprocess.SubprocessError):
        pass


def testleri_calistir(root: Path, command: str, timeout: float) -> tuple[list[str], str]:
    """Test komutunu süre sınırıyla çalıştırır; (hatalar, çıktı) döndürür."""
    env = {name: value for name, value in os.environ.items() if name not in _GIT_DEPO_AYARLARI}
    env.setdefault("CI", "true")  # izleme modunda açılan test araçları (vitest, jest) bir kez çalışıp kapansın
    group = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    with tempfile.TemporaryFile() as output:  # boru değil dosya: kapanmayan alt süreç beklemeyi kilitlemesin
        process = subprocess.Popen(["sh", "-c", command], cwd=root, env=env, stdout=output, stderr=subprocess.STDOUT, **group)
        try:
            process.wait(timeout=timeout)
            timed_out = False
        except subprocess.TimeoutExpired:
            _sureci_kapat(process)
            timed_out = True
        output.seek(0)
        text = output.read().decode("utf-8", errors="replace")
    if timed_out:
        minutes = f"{timeout / 60:g} dakikada" if timeout >= 60 else f"{timeout:g} saniyede"
        return [
            f"Testler {minutes} bitmedi, kayıt engellendi. Komut: {command}. Test komutu kendiliğinden kapanmıyor olabilir "
            "(izleme modu); ILERLEME.md'deki komutu bir kez çalışıp kapanacak hale getirin (örn. 'vitest run')."
        ], text
    if process.returncode != 0:
        return [f"Testler geçmedi, kayıt engellendi. Komut: {command}"], text
    return [], text


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
)


def yeni_fonksiyonlar(diff_text: str) -> list[str]:
    """Eklenen en dış düzey fonksiyon ve sınıflar. Girintili tanımlar (iç fonksiyonlar, nesne ve sınıf
    metotları) zorunlu tutulmaz: haritada üst fonksiyonu ya da sınıfı temsil eder."""
    names: set[str] = set()
    added_lines = []
    for line in diff_text.splitlines():
        if not line.startswith("+") or line.startswith("+++") or line[1:2] in (" ", "\t"):
            continue
        added_lines.append(line)
    added_text = "\n".join(added_lines)
    for pattern in _FUNCTION_PATTERNS:
        names.update(pattern.findall(added_text))
    names.difference_update({"if", "for", "while", "switch", "catch", "function", "return", "else", "do", "try", "with", "constructor"})
    return sorted(names)


def yeni_fonksiyonlar_dosyali(diff_text: str) -> list[tuple[str, str]]:
    """Diff'te eklenen fonksiyonları (dosya, ad) olarak döndürür."""
    added: dict[str, list[str]] = {}
    current = None
    for line in diff_text.splitlines():
        if line.startswith("+++ "):
            target = line[4:].strip()
            current = target[2:] if target.startswith("b/") else None
        elif line.startswith("+") and current:
            added.setdefault(current, []).append(line)
    return sorted({(path, name) for path, lines in added.items() for name in yeni_fonksiyonlar("\n".join(lines))})


def degisen_harita_fonksiyonlari(harita_text: str, diff_text: str) -> tuple[list[str], list[str]]:
    """Haritadaki bir fonksiyonun değişen satırlarda ya da hunk başlığında geçtiğini görünce uyarır (yaklaşık)."""
    changed: dict[str, list[str]] = {}
    current = None
    for line in diff_text.splitlines():
        if line.startswith("+++ "):
            target = line[4:].strip()
            current = target[2:] if target.startswith("b/") else None
        elif current and not line.startswith("--- ") and line.startswith(("+", "-", "@@")):
            changed.setdefault(current, []).append(line)
    names = [
        f"{path}::{name}"
        for name, path in _harita_girdileri(harita_text)
        if path in changed and name != path and _kelime_var(_kimlik(name), "\n".join(changed[path]))
    ]
    if not names:
        return [], []
    shown = ", ".join(names[:8]) + (f" ve {len(names) - 8} tane daha" if len(names) > 8 else "")
    return [], [f"Haritadaki {len(names)} fonksiyon değişti: {shown}. HARITA.md'de uses / used by bağlantılarının hâlâ doğru olduğunu kontrol edin."]


def harita_kapsami(harita_text: str, pairs: list[tuple[str, str]]) -> tuple[list[str], list[str]]:
    """Haritada, yardımcı listesinde ya da yardımcı dosyada olmayan yeni fonksiyonlar için tek bir uyarı verir; kaydı durdurmaz."""
    mapped = {(path, _kimlik(name)) for name, path in _harita_girdileri(harita_text)}
    helpers = set(re.findall(r"[A-Za-z_$][\w$]*", _without_html_comments(_section(harita_text, "Not mapped ("))))
    helper_files = {
        line.strip().lstrip("-* ").strip("`").strip()
        for line in _without_html_comments(_section(harita_text, "Not mapped files")).splitlines()
        if line.strip()
    }
    missing = [
        f"{path}::{name}"
        for path, name in pairs
        if (path, name) not in mapped and name not in helpers and path not in helper_files
    ]
    if not missing:
        return [], []
    shown = ", ".join(missing[:8]) + (f" ve {len(missing) - 8} tane daha" if len(missing) > 8 else "")
    return [], [
        f".waypoint/HARITA.md: haritada olmayan {len(missing)} yeni fonksiyon: {shown}. Önemli olanları ('### ad() — dosya' "
        "girdisi ve şema kutusuyla) haritaya ekleyin; küçük yardımcılar için bir şey yapmanız gerekmez."
    ]


def harita_diff_denetimi(harita_text: str, read_diff) -> tuple[list[str], list[str]]:
    """Kod diff'ine göre haritada olmayan yeni fonksiyon ve değişen fonksiyon uyarılarını üretir; diff okunamazsa kaydı durdurur."""
    try:
        diff_text = read_diff()
    except (subprocess.CalledProcessError, OSError) as exc:
        return [f".waypoint/hooks/kontrol.py: kod değişiklikleri okunamadı, harita denetlenemediği için kayıt engellendi; tekrar deneyin. ({exc})"], []
    _, warnings = harita_kapsami(harita_text, yeni_fonksiyonlar_dosyali(diff_text))
    return [], warnings + degisen_harita_fonksiyonlari(harita_text, diff_text)[1]


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


def _oku(root: Path, relative: str) -> str | None:
    path = root / relative
    try:
        return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else None
    except OSError:
        return None


def _kayittaki(root: Path, relative: str) -> str | None:
    """Dosyanın kayda girecek (stage edilmiş) hali; git'te hiç yoksa diskteki hali."""
    try:
        return _git_bytes(root, "show", f":{relative}").decode("utf-8", errors="ignore")
    except (subprocess.CalledProcessError, OSError):
        return _oku(root, relative)


WAYPOINT_REPO = "erenuzman/WaypointSkill"


def _surum(text: str) -> tuple[int, ...]:
    """'1.10' -> (1, 10); sürüm yoksa boş."""
    return tuple(int(part) for part in re.findall(r"\d+", text or "")[:3])


WAYPOINT_RAW = f"https://raw.githubusercontent.com/{WAYPOINT_REPO}/main"


def _github_surumu() -> str:
    with urllib.request.urlopen(f"{WAYPOINT_RAW}/template/.waypoint/VERSION", timeout=5) as response:
        return response.read(100).decode("utf-8", errors="replace")


def surum_kontrolu(root: Path, today: str, fetch) -> str | None:
    """Günde en fazla bir kez en yeni Waypoint sürümüne bakar; daha yeniyse yapay zekâya mesaj döndürür. Kendisi kurmaz."""
    local = (_oku(root, ".waypoint/VERSION") or "").strip()
    if not _surum(local):
        return None
    cache = root / ".waypoint/.son-surum"
    cached = (_oku(root, ".waypoint/.son-surum") or "").split()
    if len(cached) == 2 and cached[0] == today:
        latest = cached[1]
    else:
        try:
            latest = fetch().strip() or "-"
        except (subprocess.SubprocessError, OSError, ValueError, http.client.HTTPException):
            latest = "-"  # internet yok: yarın tekrar denenir
        try:
            cache.write_text(f"{today} {latest}\n", encoding="utf-8")
        except OSError:
            pass
    if _surum(latest) > _surum(local):
        return (
            f"Waypoint güncellemesi var: {local} → {latest}. Kullanıcıya yenilikleri (CHANGELOG.md) sade Türkçe özetleyin "
            "ve kurmak isteyip istemediğini sorun; kendiliğinden kurmayın."
        )
    return None


OTO_KAYIT = ".waypoint/oto-kayit.log"


def oto_kayit(root: Path, durum: str, satirlar: list[str]) -> None:
    """Kontrol sonuçlarını git'e girmeyen yerel bir dosyaya ekler; Waypoint'in işe yarayıp yaramadığını değerlendirmek için."""
    path = root / OTO_KAYIT
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    try:
        with path.open("a", encoding="utf-8") as log:
            for satir in satirlar:
                first_line = (satir.strip().splitlines() or [""])[0]
                log.write(f"{stamp}  {durum}  {first_line[:200]}\n")
        if path.stat().st_size > 200_000:  # en yeni yarısı kalsın
            lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
            path.write_text("".join(lines[len(lines) // 2:]), encoding="utf-8")
    except OSError:
        pass


_BOYUT_UYARISI = re.compile(r"^(\.waypoint/\w+\.md: .+? bölümünde) \d+ ")


def tekrarlayan_uyarilar(uyarilar: list[str], log_text: str, today: str) -> tuple[list[str], list[str]]:
    """Son 7 günde önceki bir günde de çıkmış boyut uyarısını kayıt engeline çevirir: uyarı görmezden gelinmesin."""
    since = (date.fromisoformat(today) - timedelta(days=7)).isoformat()
    earlier = [line for line in log_text.splitlines() if since <= line[:10] < today and "  UYARI  " in line]
    hatalar: list[str] = []
    kalan: list[str] = []
    for uyari in uyarilar:
        match = _BOYUT_UYARISI.match(uyari)
        if match and any(match.group(1) in line for line in earlier):
            hatalar.append(uyari + " Bu uyarı önceki bir günde de çıktı; bu yapılmadan kayıt alınamaz.")
        else:
            kalan.append(uyari)
    return hatalar, kalan


def main() -> int:
    # Windows konsolu emoji ve Türkçe karakterleri bozmasın
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    root = Path(__file__).resolve().parents[2]  # <proje>/.waypoint/hooks/kontrol.py
    if sys.argv[1:] == ["--surum"]:
        message = surum_kontrolu(root, date.today().isoformat(), _github_surumu)
        if message:
            print(f"⬆️ {message}")
        return 0
    if sys.argv[1:] == ["--test"]:
        command = test_komutunu_bul(_kayittaki(root, ".waypoint/ILERLEME.md") or "")
        if command is None:
            return 0
        try:
            timeout = float(os.environ.get("WAYPOINT_TEST_TIMEOUT") or TEST_SURESI)
        except ValueError:
            timeout = TEST_SURESI
        errors, output = testleri_calistir(root, command, timeout)
        if not errors:
            return 0
        print(f"❌ {errors[0]}")
        print("\n".join(output.splitlines()[-30:]))
        oto_kayit(root, "ENGEL", errors)
        return 1
    if len(sys.argv) == 3 and sys.argv[1] == "--mesaj":
        try:
            message = Path(sys.argv[2]).read_text(encoding="utf-8")
        except OSError:
            return 0
        try:
            staged_names = _git_output(root, "diff", "--cached", "--name-only", "--diff-filter=ACMR")
        except (subprocess.CalledProcessError, OSError):
            staged_names = []
        progress_text = _kayittaki(root, ".waypoint/ILERLEME.md") or ""
        errors, warnings = kayit_turu(message, staged_names, test_komutu(progress_text))
        text_errors, _ = bozuk_metin("Kayıt mesajı", message)
        errors.extend(text_errors)
        for error in errors:
            print(f"❌ {error}")
        for warning in warnings:
            print(f"⚠️ {warning}")
        oto_kayit(root, "UYARI", warnings)
        if errors:
            oto_kayit(root, "ENGEL", errors)
            return 1
        subject = next((line for line in message.splitlines() if line.strip() and not line.startswith("#")), "")
        oto_kayit(root, "KAYIT", [f"{subject} ({len(staged_names)} dosya)"])
        return 0
    try:
        staged = _git_output(root, "diff", "--cached", "--name-only", "--diff-filter=ACMR")
    except (subprocess.CalledProcessError, OSError) as exc:
        print(f"❌ .waypoint/hooks/kontrol.py: Git deposu okunamadı; hook'u depo içinden çalıştırın. ({exc})")
        return 1

    hatalar, uyarilar = gizli_dosyalar(staged)
    hatalar.extend(waypoint_duzeni(staged)[0])
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
    # Belgeler kayda girecek halleriyle denetlenir: diskte düzeltilip 'git add' edilmemiş satır kontrolü geçirmesin.
    for path, check in ((".waypoint/HARITA.md", harita), (".waypoint/DERSLER.md", dersler), (".waypoint/ILERLEME.md", ilerleme)):
        file_text = _kayittaki(root, path)
        if file_text is not None:
            errors, warnings = check(file_text)
            hatalar.extend(errors)
            uyarilar.extend(warnings)
            if path == ".waypoint/ILERLEME.md":
                errors, warnings = ilerleme_bugun(file_text, today, staged)
                hatalar.extend(errors)
                uyarilar.extend(warnings)
                errors, _ = fikirler(file_text, _kayittaki(root, ".waypoint/FIKIRLER.md"))
                hatalar.extend(errors)
                uyarilar.extend(test_komutu_uyarisi(file_text, staged))
    map_text = _kayittaki(root, ".waypoint/HARITA.md")
    if map_text is not None:
        errors, _ = harita_gercek(map_text, lambda path: _oku(root, path))
        hatalar.extend(errors)
        code_paths = [name for name in staged if _is_code_file(name) and not _is_test_file(name)]
        if code_paths:
            errors, warnings = harita_diff_denetimi(
                map_text,
                lambda: "\n".join(_git_output(root, "diff", "--cached", "-U0", "--diff-filter=ACMR", "--", *code_paths)),
            )
            hatalar.extend(errors)
            uyarilar.extend(warnings)
    errors, uyarilar = tekrarlayan_uyarilar(uyarilar, _oku(root, OTO_KAYIT) or "", today)
    hatalar.extend(errors)
    for hata in hatalar:
        print(f"❌ {hata}")
    for uyari in uyarilar:
        print(f"⚠️ {uyari}")
    oto_kayit(root, "UYARI", uyarilar)
    if hatalar:
        oto_kayit(root, "ENGEL", hatalar)
        return 1
    print("✅ .waypoint/hooks/kontrol.py: Belgeler ve gizli dosya denetimleri geçti.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
