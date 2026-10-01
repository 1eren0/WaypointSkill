import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("kontrol.py")
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


class HaritaTestleri(unittest.TestCase):
    def test_bos_kit_sablonu_gecer(self):
        text = (Path(__file__).parents[1] / "docs" / "HARITA.md").read_text(encoding="utf-8")
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
        text = (Path(__file__).parents[1] / "docs" / "DERSLER.md").read_text(encoding="utf-8")
        self.assertEqual(kontrol.dersler(text)[0], [])

    def test_yirmi_bir_kural_hata(self):
        text = "## Kurallar\n" + "\n".join(f"- kural {i}" for i in range(21)) + "\n## Kayıtlar\n"
        self.assertEqual(len(kontrol.dersler(text)[0]), 1)


class IlerlemeTestleri(unittest.TestCase):
    def test_bos_kit_sablonu_gecer(self):
        text = (Path(__file__).parents[1] / "docs" / "ILERLEME.md").read_text(encoding="utf-8")
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
        self.assertIn("docs/GUNLUK_ARSIV.md", warnings[0])


if __name__ == "__main__":
    unittest.main()
