import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="Waypoint ü ")
        self.target = Path(self.temp.name)
        self.env = os.environ.copy()
        self.env["WAYPOINT_SOURCE"] = str(ROOT)

    def tearDown(self):
        self.temp.cleanup()

    def run_cmd(self, args):
        return subprocess.run(args, cwd=self.target, env=self.env, text=True, encoding="utf-8", errors="replace",
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    def check_install(self, command):
        # The project's own hooks folder is remembered so Waypoint keeps running it.
        self.run_cmd(["git", "init", "-q"])
        self.run_cmd(["git", "config", "core.hooksPath", "eski-hooks"])
        self.run_cmd(command)
        remembered = subprocess.run(["git", "config", "waypoint.oncekiHooks"], cwd=self.target,
                                    env=self.env, text=True, stdout=subprocess.PIPE, check=True)
        self.assertEqual(remembered.stdout.strip(), "eski-hooks")
        for relative in (".waypoint/KURALLAR.md", ".waypoint/komutlar/bitir.md", ".waypoint/guncelle.bat",
                         ".waypoint/guncelle.command", ".waypoint/hooks/kontrol.py", "AGENTS.md", "CLAUDE.md"):
            self.assertTrue((self.target / relative).is_file(), relative)
        configured = subprocess.run(["git", "config", "core.hooksPath"], cwd=self.target,
                                    env=self.env, text=True, stdout=subprocess.PIPE, check=True)
        self.assertEqual(configured.stdout.strip(), ".waypoint/hooks")
        agents = self.target / "AGENTS.md"
        self.run_cmd(command)
        self.assertEqual(agents.read_text(encoding="utf-8").count(".waypoint/KURALLAR.md"), 1)
        remembered = subprocess.run(["git", "config", "waypoint.oncekiHooks"], cwd=self.target,
                                    env=self.env, text=True, stdout=subprocess.PIPE, check=True)
        self.assertEqual(remembered.stdout.strip(), "eski-hooks")

        # Existing project instructions remain, with the pointer appended once.
        shutil.rmtree(self.target / ".waypoint")
        agents.write_text("project-specific guidance\n", encoding="utf-8")
        self.run_cmd(command)
        self.assertIn("project-specific guidance", agents.read_text(encoding="utf-8"))
        self.assertEqual(agents.read_text(encoding="utf-8").count(".waypoint/KURALLAR.md"), 1)

        # The old "follow it exactly" pointer is replaced on update; other lines stay.
        legacy = ("Before doing anything in this project, read `.waypoint/KURALLAR.md` "
                  "and follow it exactly. It overrides your defaults.")
        agents.write_text(f"project-specific guidance\n\n# Waypoint\n\n{legacy}\n", encoding="utf-8")
        self.run_cmd(command)
        updated = agents.read_text(encoding="utf-8")
        self.assertNotIn("follow it exactly", updated)
        self.assertIn("Before working in this project, read `.waypoint/KURALLAR.md`.", updated)
        self.assertIn("project-specific guidance", updated)

        progress =self.target / ".waypoint/ILERLEME.md"
        progress.write_text("user progress data\n", encoding="utf-8")
        (self.target / ".waypoint/KURALLAR.md").write_text("modified rules\n", encoding="utf-8")
        (self.target / ".waypoint/VERSION").write_text("0.1\n", encoding="utf-8")
        (self.target / ".waypoint/komutlar/bitir.md").write_text("old recipe\n", encoding="utf-8")
        (self.target / ".waypoint/komutlar/eski.md").write_text("removed recipe\n", encoding="utf-8")
        (self.target / ".waypoint/guncelle.bat").unlink()
        self.run_cmd(command)
        self.assertTrue((self.target / ".waypoint/guncelle.bat").is_file())
        self.assertEqual((self.target / ".waypoint/komutlar/bitir.md").read_text(encoding="utf-8"),
                         (ROOT / "template/.waypoint/komutlar/bitir.md").read_text(encoding="utf-8"))
        self.assertFalse((self.target / ".waypoint/komutlar/eski.md").exists())
        self.assertEqual((self.target / ".waypoint/VERSION").read_text(encoding="utf-8"),
                         (ROOT / "template/.waypoint/VERSION").read_text(encoding="utf-8"))
        self.assertEqual(progress.read_text(encoding="utf-8"), "user progress data\n")
        self.assertNotEqual((self.target / ".waypoint/KURALLAR.md").read_text(encoding="utf-8"), "modified rules\n")

    def check_update_restores_git_hooks(self, command):
        # Older versions switched off hooks in .git/hooks; updating turns them back on.
        self.run_cmd(["git", "init", "-q"])
        self.run_cmd(["git", "config", "core.hooksPath", ".waypoint/hooks"])
        hooks = self.target / ".git" / "hooks"
        hooks.mkdir(exist_ok=True)
        (hooks / "pre-commit").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        self.run_cmd(command)
        remembered = subprocess.run(["git", "config", "waypoint.oncekiHooks"], cwd=self.target,
                                    env=self.env, text=True, stdout=subprocess.PIPE, check=True)
        self.assertEqual(remembered.stdout.strip(), ".git/hooks")

    @unittest.skipUnless(shutil.which("sh"), "sh bulunamadı")
    def test_shell_update_restores_git_hooks(self):
        self.check_update_restores_git_hooks(["sh", str((ROOT / "install.sh").resolve())])

    @unittest.skipUnless(shutil.which("sh"), "sh bulunamadı")
    def test_shell_installer(self):
        script = (ROOT / "install.sh").resolve()
        self.check_install(["sh", str(script)])

    def powershell_command(self):
        if os.name != "nt":
            self.skipTest("install.ps1 Windows kurulumu; macOS/Linux install.sh kullanır")
        executable = shutil.which("powershell") or shutil.which("pwsh")
        if not executable:
            self.skipTest("PowerShell bulunamadı")
        command = [executable, "-NoProfile"]
        if Path(executable).name.lower().startswith("powershell"):
            command += ["-ExecutionPolicy", "Bypass"]
        return command + ["-File", str((ROOT / "install.ps1").resolve())]

    def test_powershell_installer(self):
        self.check_install(self.powershell_command())

    def test_powershell_update_restores_git_hooks(self):
        self.check_update_restores_git_hooks(self.powershell_command())



@unittest.skipUnless(shutil.which("sh") and shutil.which("curl"), "sh ve curl gerekli")
class UpdateLauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="Waypoint ü ")
        self.root = Path(self.temp.name)
        (self.root / ".waypoint").mkdir()
        shutil.copy(ROOT / "template/.waypoint/guncelle.command", self.root / ".waypoint/guncelle.command")

    def tearDown(self):
        self.temp.cleanup()

    def run_launcher(self, url):
        env = dict(os.environ, WAYPOINT_INSTALL_URL=url)
        return subprocess.run(["sh", ".waypoint/guncelle.command"], cwd=self.root, env=env, text=True,
                              encoding="utf-8", errors="replace", capture_output=True)

    def script_url(self, body):
        # Windows curl doesn't decode %20 in file:// URLs, so the script sits in a plain-named folder.
        folder = tempfile.TemporaryDirectory(prefix="waypoint-")
        self.addCleanup(folder.cleanup)
        script = Path(folder.name) / "install.sh"
        script.write_text(body, encoding="utf-8")
        return script.resolve().as_uri()

    def test_basarili_kurulumda_bitti_der(self):
        result = self.run_launcher(self.script_url("echo kuruldu\n"))
        self.assertIn("Bitti.", result.stdout)
        self.assertNotIn("OLMADI", result.stdout)

    def test_kurulum_hata_verirse_bitti_demez(self):
        result = self.run_launcher(self.script_url("echo bozuk >&2; exit 1\n"))
        self.assertIn("Güncelleme OLMADI", result.stdout)
        self.assertNotIn("Bitti.", result.stdout)

    def test_indirme_basarisizsa_bitti_demez(self):
        result = self.run_launcher(self.script_url("")[:-len("install.sh")] + "yok.sh")
        self.assertIn("Güncelleme OLMADI", result.stdout)
        self.assertNotIn("Bitti.", result.stdout)

    def test_windows_baslaticisi_hatada_bitti_demez(self):
        lines = (ROOT / "template/.waypoint/guncelle.bat").read_text(encoding="ascii").splitlines()
        command = [line for line in lines if line and not line.startswith(("@echo", "rem "))]
        self.assertEqual(len(command), 1)  # kurulum dosyayı değiştirirken cmd tek satırı okumuş olmalı
        self.assertIn("&& (echo. & echo Bitti.", command[0])
        self.assertIn("|| (echo. & echo Guncelleme OLMADI.", command[0])

if __name__ == "__main__":
    unittest.main()
