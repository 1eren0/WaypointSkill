import importlib.util
import unittest
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

    def test_yirmi_bir_kural_hata(self):
        text = "## Kurallar\n" + "\n".join(f"- kural {i}" for i in range(21)) + "\n## Kayıtlar\n"
        self.assertEqual(len(kontrol.dersler(text)[0]), 1)


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
        self.assertIn(".waypoint/GUNLUK_ARSIV.md", warnings[0])


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

    def test_silinen_satir_ve_baslik_yok_sayilir(self):
        diff = "+++ b/file.js\n-function eski() {}\n+const yeni = x => x\n"
        self.assertEqual(kontrol.yeni_fonksiyonlar(diff), ["yeni"])

    def test_haritada_not_mapped_satiri_yeterli(self):
        self.assertEqual(kontrol.harita_kapsami("## Not mapped (small helpers)\nfoo, bar\n", ["foo"]), ([], []))

    def test_haritada_yoksa_hata(self):
        errors, _ = kontrol.harita_kapsami("## Not mapped (small helpers)\n", ["foo"])
        self.assertEqual(len(errors), 1)
        self.assertIn("foo", errors[0])

    def test_gercek_harita_sablonu_gecer(self):
        text = (WAYPOINT / "HARITA.md").read_text(encoding="utf-8")
        self.assertEqual(kontrol.harita(text)[0], [])


class DersHatirlatmaTestleri(unittest.TestCase):
    def test_duzeltme_mesajlari_uyari_verir(self):
        for message in ("Hata düzeltildi", "Giriş butonu düzeltildi"):
            with self.subTest(message=message):
                self.assertEqual(kontrol.ders_hatirlatma(message)[0], [])
                self.assertEqual(len(kontrol.ders_hatirlatma(message)[1]), 1)

    def test_ozellik_ekleme_uyari_vermez(self):
        self.assertEqual(kontrol.ders_hatirlatma("Giriş butonu eklendi"), ([], []))


class KayitTuruTestleri(unittest.TestCase):
    def test_gecerli_turler(self):
        for kind in ("Kurulum", "\u00d6zellik", "D\u00fczeltme", "D\u00fczenleme", "Belge"):
            with self.subTest(kind=kind):
                self.assertEqual(kontrol.kayit_turu(f"{kind}: \u00d6rnek", [], False), ([], []))

    def test_tur_yoksa_hata(self):
        self.assertEqual(len(kontrol.kayit_turu("Bir de\u011fi\u015fiklik", [], False)[0]), 1)

    def test_merge_serbest(self):
        self.assertEqual(kontrol.kayit_turu("Merge branch x", [], False), ([], []))

    def test_yorum_satirlari_atlanir(self):
        self.assertEqual(kontrol.kayit_turu("# yorum\n\n\u00d6zellik: Eklendi", [], False), ([], []))

    def test_belge_kodla_hata(self):
        self.assertEqual(len(kontrol.kayit_turu("Belge: A\u00e7\u0131kla", ["app.js"], False)[0]), 1)

    def test_belge_waypoint_serbest(self):
        self.assertEqual(kontrol.kayit_turu("Belge: A\u00e7\u0131kla", [".waypoint/ILERLEME.md"], False), ([], []))

    def test_duzeltme_test_gerekir(self):
        self.assertEqual(len(kontrol.kayit_turu("D\u00fczeltme: Hata", ["app.js"], True)[0]), 1)

    def test_duzeltme_test_dosyasi_ile_serbest(self):
        self.assertEqual(kontrol.kayit_turu("D\u00fczeltme: Hata", ["app.js", "test_app.js"], True), ([], []))

    def test_duzeltme_test_yok_aciklamasi_ile_serbest(self):
        self.assertEqual(kontrol.kayit_turu("D\u00fczeltme: Hata\n\ntest yok: sadece CSS", ["app.js"], True), ([], []))

    def test_test_komutu_yoksa_serbest(self):
        self.assertEqual(kontrol.kayit_turu("D\u00fczeltme: Hata", ["app.js"], False), ([], []))

    def test_test_komutu_okunur(self):
        self.assertTrue(kontrol.test_komutu("## Testleri \u00e7al\u0131\u015ft\u0131rma\n`node --test`"))
        self.assertFalse(kontrol.test_komutu("## Testleri \u00e7al\u0131\u015ft\u0131rma\n`...`"))

class YorumSatiriTestleri(unittest.TestCase):
    def test_yorumdaki_function_kelimesi_sayilmaz(self):
        diff = "+// this function handles clicks\n+  return value; // helper function x\n"
        self.assertEqual(kontrol.yeni_fonksiyonlar(diff), [])

    def test_export_function_bulunur(self):
        self.assertEqual(kontrol.yeni_fonksiyonlar("+export async function girisYap() {}"), ["girisYap"])

    def test_buyuk_i_ile_duzeltme(self):
        _, uyarilar = kontrol.ders_hatirlatma("İLK HATA DÜZELTİLDİ")
        self.assertEqual(len(uyarilar), 1)


if __name__ == "__main__":
    unittest.main()
