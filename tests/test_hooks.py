import os
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
