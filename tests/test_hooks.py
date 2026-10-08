import os
from datetime import date
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("sh") and shutil.which("git"), "sh and git are required")
class HookPythonRequiredTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(prefix="Waypoint ü ")
        self.repo = Path(self.temp_dir.name)
        shutil.copytree(REPO_ROOT / "template" / ".waypoint", self.repo / ".waypoint")
        self.run_git("init")
        self.run_git("config", "core.hooksPath", ".waypoint/hooks")
        self.run_git("config", "user.name", "Waypoint Test")
        self.run_git("config", "user.email", "waypoint@example.com")
        (self.repo / "sample.txt").write_text("test\n", encoding="utf-8")
        self.run_git("add", "sample.txt")

    def tearDown(self):
        self.temp_dir.cleanup()

    def run_git(self, *args):
        return subprocess.run(
            ["git", *args], cwd=self.repo, text=True, encoding="utf-8", capture_output=True, check=True
        )

    def test_commit_is_blocked_without_python(self):
        env = os.environ.copy()
        env["WAYPOINT_NO_PYTHON"] = "1"
        result = subprocess.run(
            ["git", "commit", "-m", "(Setup) Install Waypoint"],
            cwd=self.repo,
            env=env,
            text=True,
            encoding="utf-8",
            capture_output=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Python 3 bulunamadı", result.stdout + result.stderr)

    def test_commit_msg_hook_is_blocked_without_python(self):
        message_file = self.repo / "COMMIT_EDITMSG"
        message_file.write_text("(Setup) Install Waypoint\n", encoding="utf-8")
        env = os.environ.copy()
        env["WAYPOINT_NO_PYTHON"] = "1"
        result = subprocess.run(
            ["sh", ".waypoint/hooks/commit-msg", str(message_file)],
            cwd=self.repo,
            env=env,
            text=True,
            encoding="utf-8",
            capture_output=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Python 3 bulunamadı", result.stdout + result.stderr)

    def test_pre_commit_with_python_does_not_report_missing_python(self):
        env = os.environ.copy()
        env.pop("WAYPOINT_NO_PYTHON", None)
        result = subprocess.run(
            ["sh", ".waypoint/hooks/pre-commit"],
            cwd=self.repo,
            env=env,
            text=True,
            encoding="utf-8",
            capture_output=True,
        )
        self.assertNotIn("Python 3 bulunamadı", result.stdout + result.stderr)

    def commit(self, message):
        env = dict(os.environ, WAYPOINT_NO_UPDATE_CHECK="1")  # testler internete çıkmasın
        return subprocess.run(
            ["git", "commit", "-m", message], cwd=self.repo, env=env, text=True, encoding="utf-8", capture_output=True
        )

    def onceki_hook(self, name, body):
        folder = self.repo / "eski-hooks"
        folder.mkdir(exist_ok=True)
        hook = folder / name
        hook.write_bytes(f"#!/bin/sh\n{body}\n".encode("utf-8"))
        hook.chmod(0o755)
        self.run_git("config", "waypoint.oncekiHooks", "eski-hooks")

    def docs_staged(self):
        self.run_git("reset", "-q")
        (self.repo / "NOTLAR.md").write_text("not\n", encoding="utf-8")
        self.run_git("add", "NOTLAR.md")

    def test_projenin_onceki_hooklari_da_calisir(self):
        for name in ("pre-commit", "commit-msg", "post-commit"):
            self.onceki_hook(name, f"echo {name} >> calisan.txt")
        self.docs_staged()
        self.assertEqual(self.commit("docs: add notes").returncode, 0)
        ran = (self.repo / "calisan.txt").read_text(encoding="utf-8").split()
        self.assertEqual(ran, ["pre-commit", "commit-msg", "post-commit"])

    def test_onceki_hook_engellerse_kayit_alinmaz(self):
        self.onceki_hook("pre-commit", "echo eski kontrol bozuk; exit 1")
        self.docs_staged()
        result = self.commit("docs: add notes")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("eski kontrol bozuk", result.stdout + result.stderr)

    def test_waypointin_olmadigi_hook_da_aktarilir(self):
        self.onceki_hook("pre-push", 'echo "$1 $(cat)" > push.txt')
        result = subprocess.run(["sh", ".waypoint/hooks/pre-push", "origin"], cwd=self.repo, input="refs/heads/main",
                                text=True, encoding="utf-8", capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.repo / "push.txt").read_text(encoding="utf-8").strip(), "origin refs/heads/main")

    def test_oto_kayit_engel_ve_kayit_yazar(self):
        self.assertNotEqual(self.commit("feat: add sample").returncode, 0)  # Günlük satırı yok
        self.run_git("reset", "-q")
        (self.repo / "NOTLAR.md").write_text("not\n", encoding="utf-8")
        self.run_git("add", "NOTLAR.md")
        self.assertEqual(self.commit("docs: add notes").returncode, 0)
        log = (self.repo / ".waypoint" / "oto-kayit.log").read_text(encoding="utf-8")
        self.assertIn("ENGEL  .waypoint/ILERLEME.md: kod değişti", log)
        self.assertIn("KAYIT  docs: add notes (1 dosya)", log)
        self.assertNotIn("oto-kayit.log", self.run_git("status", "--porcelain").stdout)

    def test_kayda_eklenmemis_gunluk_satiri_sayilmaz(self):
        self.run_git("reset", "-q")
        self.run_git("add", ".waypoint")
        self.assertEqual(self.commit("chore: install waypoint").returncode, 0)
        progress = self.repo / ".waypoint" / "ILERLEME.md"
        today = date.today().isoformat()
        progress.write_text(progress.read_text(encoding="utf-8") + f"- {today}: örnek eklendi\n", encoding="utf-8")
        self.run_git("add", "sample.txt")
        result = self.commit("feat: add sample")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Günlük bölümünde bugünün", result.stdout + result.stderr)
        self.run_git("add", ".waypoint/ILERLEME.md")
        self.assertEqual(self.commit("feat: add sample").returncode, 0)

    def docs_commit_with_test(self, command, timeout="300"):
        progress = self.repo / ".waypoint" / "ILERLEME.md"
        text = progress.read_text(encoding="utf-8").replace("## Testleri çalıştırma\n`...`", f"## Testleri çalıştırma\n`{command}`")
        progress.write_text(text, encoding="utf-8")
        self.run_git("reset", "-q")
        (self.repo / "NOTLAR.md").write_text("not\n", encoding="utf-8")
        self.run_git("add", "NOTLAR.md")
        env = dict(os.environ, WAYPOINT_NO_UPDATE_CHECK="1", WAYPOINT_TEST_TIMEOUT=timeout)
        return subprocess.run(
            ["git", "commit", "-m", "docs: add notes"], cwd=self.repo, env=env, text=True, encoding="utf-8", capture_output=True
        )

    def test_kalan_test_kaydi_engeller(self):
        result = self.docs_commit_with_test("echo kirik; exit 1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Testler geçmedi", result.stdout + result.stderr)
        self.assertIn("kirik", result.stdout + result.stderr)
        self.assertIn("ENGEL  Testler geçmedi", (self.repo / ".waypoint" / "oto-kayit.log").read_text(encoding="utf-8"))

    def test_kapanmayan_test_kaydi_kilitlemez(self):
        result = self.docs_commit_with_test("sleep 60", timeout="2")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("2 saniyede bitmedi", result.stdout + result.stderr)

    def test_testler_kaydedilen_depoyu_gormez(self):
        # Git, hook'a GIT_INDEX_FILE gibi ayarlar verir; testlere geçerse geçici depolardaki git komutları gerçek depoya gider.
        result = self.docs_commit_with_test('test -z "$GIT_INDEX_FILE$GIT_DIR$GIT_WORK_TREE$GIT_PREFIX"')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_gecen_test_kayda_izin_verir(self):
        self.assertEqual(self.docs_commit_with_test("echo tamam").returncode, 0)

    def test_kayit_uzak_depoya_yuklenir(self):
        remote = self.repo / "uzak.git"
        subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True, capture_output=True)
        self.run_git("remote", "add", "origin", str(remote))
        self.run_git("reset", "-q")
        (self.repo / "NOTLAR.md").write_text("not\n", encoding="utf-8")
        self.run_git("add", "NOTLAR.md")
        result = self.commit("docs: add notes")
        self.assertEqual(result.returncode, 0)
        self.assertIn("GitHub'a yüklendi", result.stdout + result.stderr)
        branch = self.run_git("symbolic-ref", "--short", "HEAD").stdout.strip()
        pushed = subprocess.run(["git", "--git-dir", str(remote), "log", "--format=%s", branch],
                                text=True, encoding="utf-8", capture_output=True, check=True)
        self.assertEqual(pushed.stdout.strip(), "docs: add notes")
        self.assertIn(f"YUKLE  {branch}", (self.repo / ".waypoint" / "oto-kayit.log").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
