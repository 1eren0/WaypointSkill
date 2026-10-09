import importlib.util
import re
import shutil
import tempfile
import time
import unittest
from unittest import mock
from pathlib import Path


WAYPOINT = Path(__file__).resolve().parents[1] / "template" / ".waypoint"
MODULE_PATH = WAYPOINT / "hooks" / "kontrol.py"
SPEC = importlib.util.spec_from_file_location("kontrol", MODULE_PATH)
kontrol = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(kontrol)


class GizliDosyaTestleri(unittest.TestCase):
    def test_env_example_serbest(self):
        self.assertEqual(kontrol.gizli_dosyalar([".env.example"]), ([], []))

    def test_env_engellenir(self):
        errors, _ = kontrol.gizli_dosyalar(["config/.env"])
        self.assertEqual(len(errors), 1)
        self.assertIn(".gitignore", errors[0])

    def test_key_ve_rsa_engellenir(self):
        errors, _ = kontrol.gizli_dosyalar(["secret.pem", "id_rsa_work"])
        self.assertEqual(len(errors), 2)


class BozukMetinTestleri(unittest.TestCase):
    def test_temiz_turkce_ve_emoji_gecer(self):
        self.assertEqual(kontrol.bozuk_metin("x.py", "Türkçe metin ✅ 🧭"), ([], []))

    def test_cp1252_mojibake_satiri_bildirilir(self):
        bad = "çalışıyor".encode("utf-8").decode("cp1252", errors="ignore")
        errors, _ = kontrol.bozuk_metin("x.py", "temiz\n" + bad)
        self.assertEqual(len(errors), 1)
        self.assertIn("2. satır", errors[0])

    def test_cp1254_mojibake_engellenir(self):
        bad = "ğüşi".encode("utf-8").decode("cp1254", errors="ignore")
        self.assertEqual(len(kontrol.bozuk_metin("x.py", bad)[0]), 1)

    def test_yerine_koyma_isareti_engellenir(self):
        self.assertEqual(len(kontrol.bozuk_metin("x.py", "a\ufffdb")[0]), 1)


class BozukDosyaTestleri(unittest.TestCase):
    def test_gecersiz_utf8_bayt_engellenir(self):
        self.assertIn("UTF-8 değil", kontrol.bozuk_dosya("x.py", b"\xff")[0][0])

    def test_bom_ve_temiz_utf8_gecer(self):
        data = b"\xef\xbb\xbf" + "Türkçe".encode("utf-8")
        self.assertEqual(kontrol.bozuk_dosya("x.py", data), ([], []))

    def test_png_ve_nul_icerik_atlanir(self):
        self.assertEqual(kontrol.bozuk_dosya("x.png", b"junk\xff"), ([], []))
        self.assertEqual(kontrol.bozuk_dosya("x.txt", b"junk\x00\xff"), ([], []))

    def test_hooks_altindaki_dosya_atlanir(self):
        self.assertEqual(kontrol.bozuk_dosya(".waypoint/hooks/x.py", b"\xff"), ([], []))

    def test_hook_kaynagi_taramadan_gecer(self):
        source = MODULE_PATH.read_bytes()
        self.assertEqual(kontrol.bozuk_dosya("kontrol_kopya.py", source), ([], []))


class HaritaTestleri(unittest.TestCase):
    def test_bos_kit_sablonu_gecer(self):
        text = (WAYPOINT / "HARITA.md").read_text(encoding="utf-8")
        self.assertEqual(kontrol.harita(text)[0], [])

    def test_bozuk_baslik_sessizce_gecmez(self):
        # Gerçek olay: dosya UTF-8 dışı yazılınca "Şema" → "?ema" oldu, denetim hiçbir şey bulamadan geçti.
        text = (WAYPOINT / "HARITA.md").read_text(encoding="utf-8").replace("## Şema", "## ?ema")
        errors, _ = kontrol.harita(text)
        self.assertEqual(len(errors), 1)
        self.assertIn("'Şema' başlığı eksik", errors[0])

    def test_dosya_kutulu_genel_sema_gecer(self):
        text = '''## Şema
```mermaid
flowchart LR
  app["app.py"]
```
## Key functions / components
### app.py — app.py
'''
        self.assertEqual(kontrol.harita(text)[0], [])

    def test_yaygin_kutu_bicimleri_taninir(self):
        text = '''## Şema
```mermaid
flowchart LR
  subgraph auth["Giriş — auth.js"]
    a["girisYap()<br>kullanıcıyı içeri alır"]
    b[cikisYap()]
    c("sifreKontrol()")
    d(oturumAc)
    e{"yetkiVar()"}
  end
  a --> b
  a -->|kontrol| c
  click a call goster()
```
## Key functions / components
### girisYap() — auth.js
### cikisYap() — auth.js
### sifreKontrol() — auth.js
### oturumAc — auth.js
### yetkiVar() — auth.js
'''
        self.assertEqual(kontrol.harita(text)[0], [])

    def test_on_alti_dugum_hata(self):
        nodes = "\n".join(f'  n{i}["dosya{i}.py"]' for i in range(16))
        text = f"## Şema\n```mermaid\nflowchart LR\n{nodes}\n```\n## Key functions / components\n"
        errors, _ = kontrol.harita(text)
        self.assertTrue(any("16" in error and "şemayı böl" in error for error in errors))

    def test_diyagramda_olmayan_girdi_hata(self):
        text = '''## Şema
```mermaid
flowchart LR
```
## Key functions / components
### kaydet() — store.py
'''
        errors, _ = kontrol.harita(text)
        self.assertTrue(any("listede var, şemada yok" in error for error in errors))

    def test_girdisiz_bagimsiz_dugum_hata(self):
        text = '''## Şema
```mermaid
flowchart LR
  extra["fazla()"]
```
## Key functions / components
'''
        errors, _ = kontrol.harita(text)
        self.assertTrue(any("şemada var, listede yok" in error for error in errors))


class DerslerTestleri(unittest.TestCase):
    def test_bos_kit_sablonu_gecer(self):
        text = (WAYPOINT / "DERSLER.md").read_text(encoding="utf-8")
        self.assertEqual(kontrol.dersler(text)[0], [])

    def test_eksik_baslik_hata(self):
        errors, _ = kontrol.dersler("## Kurallar\n- kural\n")
        self.assertEqual(len(errors), 1)
        self.assertIn("'Kayıtlar' başlığı eksik", errors[0])

    def test_yirmi_bir_kural_hata(self):
        text = "## Kurallar\n" + "\n".join(f"- kural {i}" for i in range(21)) + "\n## Kayıtlar\n"
        self.assertEqual(len(kontrol.dersler(text)[0]), 1)

    def test_kayit_limitleri_ve_yer_tutucular(self):
        for count, expected in ((20, "none"), (21, "warning"), (31, "error")):
            with self.subTest(count=count):
                records = "\n".join(f"### Ders {i}" for i in range(count))
                errors, warnings = kontrol.dersler("## Kurallar\n## Kayıtlar\n### YYYY-AA-GG\n" + records)
                self.assertEqual((len(errors), len(warnings)), {
                    "none": (0, 0), "warning": (0, 1), "error": (1, 0)
                }[expected])


class IlerlemeTestleri(unittest.TestCase):
    def test_bos_kit_sablonu_gecer(self):
        text = (WAYPOINT / "ILERLEME.md").read_text(encoding="utf-8")
        self.assertEqual(kontrol.ilerleme(text)[0], [])

    def test_eksik_baslik_hata(self):
        errors, _ = kontrol.ilerleme("## Proje hedefi\n")
        self.assertEqual(len(errors), 9)

    def test_gunluk_uyari(self):
        headings = "\n".join(f"## {name}" for name in kontrol._REQUIRED_HEADINGS)
        daily = "\n".join(f"- kayıt {i}" for i in range(11))
        errors, warnings = kontrol.ilerleme(headings + "\n" + daily)
        self.assertEqual(errors, [])
        self.assertEqual(len(warnings), 1)
        self.assertIn(".waypoint/ILERLEME_ARSIV.md", warnings[0])

    def test_bolum_limitleri_uyari_ve_hata(self):
        headings = "\n".join(f"## {name}" for name in kontrol._REQUIRED_HEADINGS)
        cases = (
            ("Günlük", 10, 20, lambda i: f"- kayıt {i}"),
            ("Plan", 10, 20, lambda i: f"- [x] görev {i}"),
            ("Kararlar", 20, 30, lambda i: f"- karar {i}"),
            ("Sonra yapılacaklar", 15, 25, lambda i: f"- fikir {i}"),
        )
        for section, warn_limit, error_limit, item in cases:
            for count, expected in ((warn_limit, (0, 0)), (warn_limit + 1, (0, 1)), (error_limit + 1, (1, 0))):
                with self.subTest(section=section, count=count):
                    lines = "\n".join(item(i) for i in range(count))
                    document = headings.replace(f"## {section}", f"## {section}\n{lines}")
                    errors, warnings = kontrol.ilerleme(document)
                    self.assertEqual((len(errors), len(warnings)), expected)

    def test_yer_tutucular_ve_bitmemis_plan_gorevleri_sayilmaz(self):
        headings = "\n".join(f"## {name}" for name in kontrol._REQUIRED_HEADINGS)
        text = headings + "\n## Günlük\n- YYYY-AA-GG: şablon\n- ...\n## Plan\n" + "\n".join(
            f"- [ ] görev {i}" for i in range(25)
        )
        self.assertEqual(kontrol.ilerleme(text), ([], []))


class FikirlerTestleri(unittest.TestCase):
    PARKED = "## Sonra yapılacaklar\n- Karanlık mod → ayrıntı: FIKIRLER.md › Karanlık mod\n- kısa fikir\n## Günlük\n"

    def test_bos_kit_ve_dosyasiz_gecer(self):
        text = (WAYPOINT / "ILERLEME.md").read_text(encoding="utf-8")
        self.assertEqual(kontrol.fikirler(text, None), ([], []))

    def test_eslesen_baslik_gecer(self):
        self.assertEqual(kontrol.fikirler(self.PARKED, "# Fikirler\n\n## Karanlık mod\nayrıntı\n"), ([], []))

    def test_baslik_yoksa_hata(self):
        for ideas in (None, "## Başka fikir\n"):
            with self.subTest(ideas=ideas):
                errors, _ = kontrol.fikirler(self.PARKED, ideas)
                self.assertTrue(any("'Karanlık mod' için ayrıntı başlığı yok" in e for e in errors))

    def test_artik_bolum_hata(self):
        errors, _ = kontrol.fikirler("## Sonra yapılacaklar\n- ...\n", "## Eski fikir\nayrıntı\n")
        self.assertEqual(len(errors), 1)
        self.assertIn("Eski fikir", errors[0])


class WaypointDuzeniTestleri(unittest.TestCase):
    def test_waypoint_dosyalari_ve_raporlar_gecer(self):
        names = [
            ".waypoint/ILERLEME.md", ".waypoint/FIKIRLER.md", ".waypoint/DERS_ARSIV.md", ".waypoint/WAYPOINT_GUNLUGU.md", ".waypoint/hooks/kontrol.py",
            ".waypoint/guncelle.bat", ".waypoint/guncelle.command",
            ".waypoint/raporlar/2026-10-04-hiz-olcumu.md",
            ".waypoint/raporlar/2026-10-06-guvenlik/ozet.md", ".waypoint/raporlar/2026-10-06-guvenlik/ekran.png",
            "rapor.md", "src/app.js",
        ]
        self.assertEqual(kontrol.waypoint_duzeni(names), ([], []))

    def test_komut_tarifleri_gecer(self):
        names = [f".waypoint/komutlar/{path.name}" for path in (WAYPOINT / "komutlar").glob("*.md")]
        self.assertTrue(names)
        self.assertEqual(kontrol.waypoint_duzeni(names), ([], []))
        self.assertEqual(len(kontrol.waypoint_duzeni([".waypoint/komutlar/alt/x.md"])[0]), 1)

    def test_kurallardaki_komut_dosyalari_var(self):
        rules = (WAYPOINT / "KURALLAR.md").read_text(encoding="utf-8")
        referenced = set(re.findall(r"komutlar/([\w-]+\.md)", rules))
        self.assertTrue(referenced)
        for name in referenced:
            with self.subTest(name=name):
                self.assertTrue((WAYPOINT / "komutlar" / name).is_file())

    def test_koke_rapor_hata(self):
        errors, _ = kontrol.waypoint_duzeni([".waypoint/rapor.md", ".waypoint/notlar/x.md"])
        self.assertEqual(len(errors), 2)
        self.assertIn("raporlar/", errors[0])

    def test_tarihsiz_rapor_hata(self):
        for name in (".waypoint/raporlar/hiz.md", ".waypoint/raporlar/guvenlik/ozet.md", ".waypoint/raporlar/2026-10-04-hiz.png"):
            with self.subTest(name=name):
                errors, _ = kontrol.waypoint_duzeni([name])
                self.assertEqual(len(errors), 1)
                self.assertIn("tarihle", errors[0])


class TekrarlayanUyariTestleri(unittest.TestCase):
    UYARI = ".waypoint/DERSLER.md: Kayıtlar bölümünde 22 ders var; kuralı 'Kurallar' bölümünde duran eski dersleri .waypoint/DERS_ARSIV.md dosyasına taşıyın."
    DUNKU = "2026-10-04 14:38  UYARI  .waypoint/DERSLER.md: Kayıtlar bölümünde 21 ders var; kuralı …\n"

    def test_dun_de_cikan_boyut_uyarisi_engel_olur(self):
        errors, warnings = kontrol.tekrarlayan_uyarilar([self.UYARI], self.DUNKU, "2026-10-05")
        self.assertEqual(warnings, [])
        self.assertEqual(len(errors), 1)
        self.assertIn("önceki bir günde de çıktı", errors[0])

    def test_ayni_gun_eski_ya_da_baska_uyari_engel_olmaz(self):
        for log, today in ((self.DUNKU, "2026-10-04"), (self.DUNKU, "2026-10-20"), ("", "2026-10-05")):
            with self.subTest(log=log, today=today):
                self.assertEqual(kontrol.tekrarlayan_uyarilar([self.UYARI], log, today), ([], [self.UYARI]))
        harita = "Haritadaki 2 fonksiyon değişti: a.js::f(), a.js::g(). HARITA.md'de …"
        log = f"2026-10-04 10:00  UYARI  {harita}\n"
        self.assertEqual(kontrol.tekrarlayan_uyarilar([harita], log, "2026-10-05"), ([], [harita]))


class SurumKontroluTestleri(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / ".waypoint").mkdir()
        (self.root / ".waypoint" / "VERSION").write_text("1.9\n", encoding="utf-8")
        self.calls = 0

    def tearDown(self):
        self.temp.cleanup()

    def fetch(self, value):
        def inner():
            self.calls += 1
            if isinstance(value, Exception):
                raise value
            return value
        return inner

    def test_yeni_surum_mesaj_verir(self):
        message = kontrol.surum_kontrolu(self.root, "2026-10-04", self.fetch("1.10\n"))
        self.assertIn("1.9 → 1.10", message)

    def test_ayni_ya_da_eski_surum_sessiz(self):
        for latest in ("1.9", "1.2"):
            with self.subTest(latest=latest):
                (self.root / ".waypoint" / ".son-surum").unlink(missing_ok=True)
                self.assertIsNone(kontrol.surum_kontrolu(self.root, "2026-10-04", self.fetch(latest)))

    def test_gunde_bir_kez_bakar(self):
        kontrol.surum_kontrolu(self.root, "2026-10-04", self.fetch("2.0"))
        self.assertIsNotNone(kontrol.surum_kontrolu(self.root, "2026-10-04", self.fetch("2.0")))
        self.assertEqual(self.calls, 1)
        kontrol.surum_kontrolu(self.root, "2026-10-05", self.fetch("2.0"))
        self.assertEqual(self.calls, 2)

    def test_internet_yoksa_sessiz_ve_gun_boyu_denemez(self):
        self.assertIsNone(kontrol.surum_kontrolu(self.root, "2026-10-04", self.fetch(OSError("gh yok"))))
        self.assertIsNone(kontrol.surum_kontrolu(self.root, "2026-10-04", self.fetch("2.0")))
        self.assertEqual(self.calls, 1)

    def test_bozuk_cevap_da_sessiz(self):
        import http.client
        self.assertIsNone(kontrol.surum_kontrolu(self.root, "2026-10-04", self.fetch(http.client.IncompleteRead(b""))))

    def test_surum_github_cli_olmadan_okunur(self):
        class Cevap:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self, size):
                return b"1.10\n"
        urls = []
        def urlopen(url, timeout):
            urls.append(url)
            return Cevap()
        with mock.patch.object(kontrol.urllib.request, "urlopen", urlopen):
            self.assertEqual(kontrol._github_surumu(), "1.10\n")
        self.assertEqual(urls, ["https://raw.githubusercontent.com/1eren0/WaypointSkill/main/template/.waypoint/VERSION"])

    def test_guncelleme_github_cli_istemez(self):
        root = WAYPOINT.parent.parent
        for path in (WAYPOINT / "guncelle.bat", WAYPOINT / "guncelle.command",
                     WAYPOINT / "komutlar" / "guncelleme.md", root / "README.md", root / "README.tr.md"):
            with self.subTest(path=path.name):
                self.assertNotIn("gh api", path.read_text(encoding="utf-8"))

    def test_sablonda_surum_var(self):
        self.assertTrue(kontrol._surum((WAYPOINT / "VERSION").read_text(encoding="utf-8")))


class DilTestleri(unittest.TestCase):
    def test_cevap_dili_tek_kuraldan_gelir(self):
        # Only the language rule picks Turkish or English; other rules must not force Turkish replies.
        for path in [WAYPOINT / "KURALLAR.md", *sorted((WAYPOINT / "komutlar").glob("*.md"))]:
            for line in path.read_text(encoding="utf-8").splitlines():
                if "plain English if I write in English" in line:
                    continue
                with self.subTest(path=path.name, line=line[:60]):
                    self.assertNotRegex(line, r"(?i)in plain Turkish|Turkish (line|sentences)")


class TestKomutuTestleri(unittest.TestCase):
    def test_komut_yoksa_kod_degisince_uyarir(self):
        bos = "## Testleri çalıştırma\n`...`\n"
        self.assertIn("Testler çalışmadı", kontrol.test_komutu_uyarisi(bos, ["app.py"])[0])
        self.assertEqual(kontrol.test_komutu_uyarisi(bos, ["NOTLAR.md", ".waypoint/ILERLEME.md"]), [])
        self.assertEqual(kontrol.test_komutu_uyarisi("## Testleri çalıştırma\n`pytest`\n", ["app.py"]), [])

    def test_komut_bulunur_ve_yer_tutucu_yok_sayilir(self):
        self.assertEqual(kontrol.test_komutunu_bul("## Testleri çalıştırma\n`npm test`\n## Kararlar\n"), "npm test")
        self.assertIsNone(kontrol.test_komutunu_bul((WAYPOINT / "ILERLEME.md").read_text(encoding="utf-8")))
        self.assertIsNone(kontrol.test_komutunu_bul("## Kararlar\n`npm test`\n"))

    def test_kayitta_hizli_komut_calisir(self):
        text = "## Testleri çalıştırma\n`npm run test:fast`\nTüm testler: `npm test`\n"
        self.assertEqual(kontrol.test_komutunu_bul(text), "npm run test:fast")


@unittest.skipUnless(shutil.which("sh"), "sh is required")
class TestCalistirmaTestleri(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_gecen_ve_kalan_testler(self):
        self.assertEqual(kontrol.testleri_calistir(self.root, "echo tamam", 30), ([], "tamam\n"))
        errors, output = kontrol.testleri_calistir(self.root, "echo bozuk; exit 3", 30)
        self.assertIn("Testler geçmedi", errors[0])
        self.assertIn("bozuk", output)

    def test_ci_ayari_verilir(self):
        self.assertEqual(kontrol.testleri_calistir(self.root, 'test "$CI" = true', 30)[0], [])

    def test_kapanmayan_test_sure_dolunca_durdurulur(self):
        started = time.monotonic()
        errors, _ = kontrol.testleri_calistir(self.root, "sleep 60", 1)
        self.assertLess(time.monotonic() - started, 30)
        self.assertIn("1 saniyede bitmedi", errors[0])


class BugunKontrolTestleri(unittest.TestCase):
    def test_bugunun_satiri_varsa_gecer(self):
        self.assertEqual(kontrol.ilerleme_bugun("## Günlük\n- 2026-10-01: iş\n", "2026-10-01", ["app.js"]), ([], []))

    def test_kod_var_gunluk_satiri_yoksa_hata(self):
        errors, _ = kontrol.ilerleme_bugun("## Günlük\n", "2026-10-01", ["app.js"])
        self.assertEqual(len(errors), 1)
        self.assertIn("2026-10-01", errors[0])

    def test_kod_asamasi_yoksa_gecer(self):
        self.assertEqual(kontrol.ilerleme_bugun("## Günlük\n", "2026-10-01", [".waypoint/HARITA.md", ".waypoint/hooks/x.py", "README.md"]), ([], []))


class YeniFonksiyonTestleri(unittest.TestCase):
    def test_js_python_fonksiyon_ve_sinif(self):
        diff = """diff --git a/app.js b/app.js
+++ b/app.js
+function calistir() {}
+const ok = (x) => x;
+def hesapla(x):
+class Ornek:
"""
        self.assertEqual(kontrol.yeni_fonksiyonlar(diff), ["Ornek", "calistir", "hesapla", "ok"])

    def test_ic_fonksiyon_ve_metotlar_zorunlu_degil(self):
        diff = """+++ b/src/selection.js
+export function createSelectionScheduler() {
+  return {
+    schedule(selection) {
+    cancel() {
+  };
+  const emit = (state) => {
+class Kutu:
+    def ac(self):
+\tfunction ic() {}
"""
        self.assertEqual(kontrol.yeni_fonksiyonlar(diff), ["Kutu", "createSelectionScheduler"])

    def test_silinen_satir_ve_baslik_yok_sayilir(self):
        diff = "+++ b/file.js\n-function eski() {}\n+const yeni = x => x\n"
        self.assertEqual(kontrol.yeni_fonksiyonlar(diff), ["yeni"])

    def test_dosyali_yeni_fonksiyonlar(self):
        diff = "+++ b/auth/login.py\n+def validate(x):\n+++ b/payments/pay.py\n+def validate(y):\n+def ode():\n"
        self.assertEqual(kontrol.yeni_fonksiyonlar_dosyali(diff),
                         [("auth/login.py", "validate"), ("payments/pay.py", "ode"), ("payments/pay.py", "validate")])

    def test_haritada_not_mapped_satiri_yeterli(self):
        self.assertEqual(kontrol.harita_kapsami("## Not mapped (small helpers)\nfoo, bar\n", [("a.js", "foo")]), ([], []))

    def test_not_mapped_files_yeterli(self):
        text = "## Not mapped files\n- src/utils.js\n## External dependencies\n"
        self.assertEqual(kontrol.harita_kapsami(text, [("src/utils.js", "kucuk")]), ([], []))
        self.assertEqual(len(kontrol.harita_kapsami(text, [("src/app.js", "kucuk")])[1]), 1)

    def test_haritada_yoksa_tek_uyari_kayit_durmaz(self):
        errors, warnings = kontrol.harita_kapsami("## Not mapped (small helpers)\n", [("a.js", "foo"), ("b.js", "bar")])
        self.assertEqual(errors, [])
        self.assertEqual(len(warnings), 1)
        self.assertIn("a.js::foo", warnings[0])
        self.assertIn("b.js::bar", warnings[0])

    def test_test_klasoru_test_dosyasi_sayilir(self):
        self.assertTrue(kontrol._is_test_file("tests/smoke_management_https.py"))
        self.assertTrue(kontrol._is_test_file("src/__tests__/app.js"))
        self.assertFalse(kontrol._is_test_file("src/app.js"))

    def test_ad_baska_yerde_gecmesi_yetmez(self):
        text = "## Key functions / components\n### validate() — auth/login.py\n- uses: foo()\n"
        self.assertEqual(kontrol.harita_kapsami(text, [("auth/login.py", "validate")]), ([], []))
        self.assertEqual(len(kontrol.harita_kapsami(text, [("payments/pay.py", "validate")])[1]), 1)
        self.assertEqual(len(kontrol.harita_kapsami(text, [("auth/login.py", "foo")])[1]), 1)


class DegisenFonksiyonTestleri(unittest.TestCase):
    MAP = "## Key functions / components\n### girisYap() — auth.js\n### odemeAl() — pay.js\n### app.js — app.js\n"

    def test_degisen_fonksiyon_uyari_verir(self):
        diff = "--- a/auth.js\n+++ b/auth.js\n@@ -3 +3 @@ export function girisYap() {\n-  eskiServis()\n+  yeniServis()\n"
        errors, warnings = kontrol.degisen_harita_fonksiyonlari(self.MAP, diff)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, ["Haritadaki 1 fonksiyon değişti: auth.js::girisYap(). HARITA.md'de uses / used by bağlantılarının hâlâ doğru olduğunu kontrol edin."])

    def test_cok_degisiklik_tek_satir(self):
        entries = "".join(f"### f{i}() — a.js\n" for i in range(10))
        diff = "+++ b/a.js\n" + "".join(f"+  f{i}()\n" for i in range(10))
        _, warnings = kontrol.degisen_harita_fonksiyonlari("## Key functions / components\n" + entries, diff)
        self.assertEqual(len(warnings), 1)
        self.assertIn("Haritadaki 10 fonksiyon değişti", warnings[0])
        self.assertIn("ve 2 tane daha", warnings[0])

    def test_diff_okunamazsa_kayit_durur(self):
        def broken():
            raise OSError("git yok")
        errors, _ = kontrol.harita_diff_denetimi(self.MAP, broken)
        self.assertEqual(len(errors), 1)
        self.assertIn("okunamadı", errors[0])

    def test_ilgisiz_degisiklik_uyari_vermez(self):
        diff = "--- a/auth.js\n+++ b/auth.js\n@@ -9 +9 @@ function baska() {\n-  a()\n+  b()\n"
        self.assertEqual(kontrol.degisen_harita_fonksiyonlari(self.MAP, diff), ([], []))


class HaritaGercekTestleri(unittest.TestCase):
    FILES = {"auth.js": "export function girisYap() {}\n", "app.py": "print(1)\n"}

    def check(self, entries):
        text = "## Key functions / components\n" + entries
        return kontrol.harita_gercek(text, self.FILES.get)[0]

    def test_var_olan_fonksiyon_ve_dosya_kutusu_gecer(self):
        self.assertEqual(self.check("### girisYap() — auth.js\n### app.py — app.py\n"), [])

    def test_silinen_fonksiyon_hata(self):
        errors = self.check("### cikisYap() — auth.js\n")
        self.assertEqual(len(errors), 1)
        self.assertIn("artık auth.js içinde yok", errors[0])

    def test_olmayan_dosya_hata(self):
        errors = self.check("### girisYap() — src/auth.js\n")
        self.assertEqual(len(errors), 1)
        self.assertIn("dosyası yok", errors[0])

    def test_sablon_gecer(self):
        text = (WAYPOINT / "HARITA.md").read_text(encoding="utf-8")
        self.assertEqual(kontrol.harita_gercek(text, self.FILES.get), ([], []))

    def test_gercek_harita_sablonu_gecer(self):
        text = (WAYPOINT / "HARITA.md").read_text(encoding="utf-8")
        self.assertEqual(kontrol.harita(text)[0], [])


class KayitTuruTestleri(unittest.TestCase):
    def test_gecerli_turler(self):
        for kind in ("feat", "fix", "docs", "refactor", "test", "chore", "style", "perf"):
            with self.subTest(kind=kind):
                self.assertEqual(kontrol.kayit_turu(f"{kind}: add example", [], False), ([], []))

    def test_kapsamli_tur_gecer(self):
        self.assertEqual(kontrol.kayit_turu("feat(auth): add login", [], False), ([], []))

    def test_eski_parantezli_bicim_hata(self):
        self.assertEqual(len(kontrol.kayit_turu("(Create) Add example", [], False)[0]), 1)

    def test_tur_yoksa_hata(self):
        self.assertEqual(len(kontrol.kayit_turu("Bir de\u011fi\u015fiklik", [], False)[0]), 1)

    def test_merge_serbest(self):
        self.assertEqual(kontrol.kayit_turu("Merge branch 'deney/x'", [], False), ([], []))

    def test_yorum_satirlari_atlanir(self):
        self.assertEqual(kontrol.kayit_turu("# yorum\n\nfeat: Added", [], False), ([], []))

    def test_eski_turkce_on_ek_hata(self):
        self.assertEqual(len(kontrol.kayit_turu("Özellik: X", [], False)[0]), 1)

    def test_belge_kodla_hata(self):
        self.assertEqual(len(kontrol.kayit_turu("docs: Explain", ["app.js"], False)[0]), 1)

    def test_belge_waypoint_serbest(self):
        self.assertEqual(kontrol.kayit_turu("docs: Explain", [".waypoint/ILERLEME.md"], False), ([], []))

    def test_test_turu_yalniz_test_dosyasi(self):
        self.assertEqual(kontrol.kayit_turu("test: Add coverage", ["tests/test_a.py"], False), ([], []))
        self.assertEqual(len(kontrol.kayit_turu("test: Add coverage", ["app.py"], False)[0]), 1)

    def test_duzeltme_test_gerekir(self):
        self.assertEqual(len(kontrol.kayit_turu("fix: Prevent crash", ["app.js"], True)[0]), 1)

    def test_duzeltme_test_dosyasi_ile_serbest(self):
        self.assertEqual(kontrol.kayit_turu("fix: Prevent crash", ["app.js", "test_app.js"], True), ([], []))

    def test_duzeltme_test_yok_aciklamasi_ile_serbest(self):
        self.assertEqual(kontrol.kayit_turu("fix: Prevent crash\n\n(no test: CSS only)", ["app.js"], True), ([], []))

    def test_test_komutu_yoksa_serbest(self):
        self.assertEqual(kontrol.kayit_turu("fix: Prevent crash", ["app.js"], False), ([], []))

    def test_turkce_harfler_aciklamada_hata(self):
        self.assertEqual(len(kontrol.kayit_turu("feat: Add ışık", [], False)[0]), 1)

    def test_test_komutu_okunur(self):
        self.assertTrue(kontrol.test_komutu("## Testleri \u00e7al\u0131\u015ft\u0131rma\n`node --test`"))
        self.assertFalse(kontrol.test_komutu("## Testleri \u00e7al\u0131\u015ft\u0131rma\n`...`"))

class YorumSatiriTestleri(unittest.TestCase):
    def test_yorumdaki_function_kelimesi_sayilmaz(self):
        diff = "+// this function handles clicks\n+  return value; // helper function x\n"
        self.assertEqual(kontrol.yeni_fonksiyonlar(diff), [])

    def test_export_function_bulunur(self):
        self.assertEqual(kontrol.yeni_fonksiyonlar("+export async function girisYap() {}"), ["girisYap"])


class TestDosyasiSifreTestleri(unittest.TestCase):
    def test_test_dosyasinda_sahte_sifre_serbest(self):
        self.assertEqual(kontrol.gizli_icerik("tests/test_login.py", 'password = "deneme123"\n')[0], [])

    def test_test_dosyasinda_gercek_anahtar_yakalanir(self):
        key = "gh" + "p_" + "a" * 36
        self.assertEqual(len(kontrol.gizli_icerik("tests/test_api.py", f'TOKEN = "{key}"\n')[0]), 1)


if __name__ == "__main__":
    unittest.main()
