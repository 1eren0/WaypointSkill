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
        return subprocess.run(args, cwd=self.target, env=self.env, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    def check_install(self, command):
        self.run_cmd(command)
        for relative in (".waypoint/KURALLAR.md", ".waypoint/komutlar/bitir.md", ".waypoint/guncelle.bat",
                         ".waypoint/guncelle.command", ".waypoint/hooks/kontrol.py", "AGENTS.md", "CLAUDE.md"):
            self.assertTrue((self.target / relative).is_file(), relative)
        configured = subprocess.run(["git", "config", "core.hooksPath"], cwd=self.target,
                                    env=self.env, text=True, stdout=subprocess.PIPE, check=True)
        self.assertEqual(configured.stdout.strip(), ".waypoint/hooks")
        agents = self.target / "AGENTS.md"
        self.run_cmd(command)
        self.assertEqual(agents.read_text(encoding="utf-8").count(".waypoint/KURALLAR.md"), 1)

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

    @unittest.skipUnless(shutil.which("sh"), "sh bulunamadı")
    def test_shell_installer(self):
        script = (ROOT / "install.sh").resolve()
        self.check_install(["sh", str(script)])

    def test_powershell_installer(self):
        if os.name != "nt":
            self.skipTest("install.ps1 Windows kurulumu; macOS/Linux install.sh kullanır")
        executable = shutil.which("powershell") or shutil.which("pwsh")
        if not executable:
            self.skipTest("PowerShell bulunamadı")
        command = [executable, "-NoProfile"]
        if Path(executable).name.lower().startswith("powershell"):
            command += ["-ExecutionPolicy", "Bypass"]
        command += ["-File", str((ROOT / "install.ps1").resolve())]
        self.check_install(command)


if __name__ == "__main__":
    unittest.main()
