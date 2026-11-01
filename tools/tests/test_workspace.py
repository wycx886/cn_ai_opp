"""Exercise real Git sharing boundaries using disposable repositories and synthetic records."""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))
from check_public import audit
sys.path.insert(0, str(REPO / "skills/setup-workspace/scripts"))
from init_local import COPIES, DIRECTORIES, initialize
from workspace import CONFIG_NAME, ROOT as WORKSPACE_ROOT, workspace_path


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "repo"
        self.root.mkdir()
        shutil.copytree(REPO / "skills/setup-workspace/assets/templates", self.root / "skills/setup-workspace/assets/templates")
        shutil.copyfile(REPO / ".gitignore", self.root / ".gitignore")
        self.git("init", "-q")
        self.git("config", "user.name", "Workspace Test")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "commit.gpgsign", "false")

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.root), *args], stderr=subprocess.PIPE)

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def test_skill_scripts_resolve_the_repository_root(self):
        self.assertEqual(WORKSPACE_ROOT, REPO)

    def test_default_workspace_is_blank_and_idempotent(self):
        created, kept = initialize(self.root)
        target = self.root / "workspace"
        self.assertEqual(set(created), set(COPIES))
        self.assertFalse(kept)
        self.assertEqual(workspace_path(self.root), target.resolve())
        self.assertTrue(all((target / name).is_dir() for name in DIRECTORIES))
        self.assertIn("待填写", (target / "profile.md").read_text())
        self.assertFalse(list((target / "applications").glob("*/log.md")))
        self.assertEqual(set(DIRECTORIES), {"resume"})
        self.assertEqual({p.name for p in target.iterdir()},
                         {"AGENTS.md", "profile.md", "preferences.md", "resume", "applications"})
        self.assertEqual({p.name for p in (target / "applications").iterdir()}, {"AGENTS.md", "README.md"})
        for optional in ("applications/inbox", "applications/archive", "applications/headhunters",
                         "drafts", "research", "playbooks", "legacy", "tmp"):
            self.assertFalse((target / optional).exists(), optional)
        self.write("workspace/AGENTS.md", "Synthetic custom workspace rules; preserve me.\n")
        self.write("workspace/profile.md", "Synthetic facts; preserve me.\n")
        self.write("workspace/applications/example/log.md", "Synthetic progress; preserve me.\n")
        before = {p.relative_to(target): p.read_bytes() for p in target.rglob("*") if p.is_file()}
        created, kept = initialize(self.root)
        self.assertFalse(created)
        self.assertEqual(set(kept), set(COPIES))
        for name, content in before.items():
            self.assertEqual((target / name).read_bytes(), content)

    def test_binding_existing_external_workspace_does_not_copy_or_modify_it(self):
        target = Path(self.temp.name) / "private-workspace"
        target.mkdir()
        for name in ("AGENTS.md", "README.md", "profile.md", "preferences.md"):
            (target / name).write_text("Synthetic existing record; preserve original layout.\n")
        before = {p.name: p.read_bytes() for p in target.iterdir()}
        created, kept = initialize(self.root, workspace="../private-workspace", use_existing=True)
        self.assertEqual((created, kept), ([], []))
        self.assertEqual(workspace_path(self.root), target.resolve())
        self.assertEqual(before, {p.name: p.read_bytes() for p in target.iterdir()})
        self.assertFalse((self.root / "workspace").exists())
        self.git("add", ".")
        self.assertNotIn(CONFIG_NAME, self.git("ls-files").decode().splitlines())
        self.assertEqual(audit(self.root), [])

    def synthetic_resume(self, suffix=".pdf", content=b"Synthetic resume content; no actual personal data.\x00\n"):
        path = Path(self.temp.name) / ("synthetic-resume" + suffix)
        path.write_bytes(content)
        return path

    def test_explicit_resume_import_preserves_bytes_source_and_blank_facts(self):
        for suffix in (".pdf", ".docx", ".md", ".txt"):
            with self.subTest(suffix=suffix):
                source = self.synthetic_resume(suffix)
                original = source.read_bytes()
                initialize(self.root, resume_file=source)
                target = self.root / "workspace/resume" / source.name
                self.assertEqual(target.read_bytes(), original)
                self.assertEqual(source.read_bytes(), original)
        templates = self.root / "skills/setup-workspace/assets/templates"
        for name, template in (("profile.md", "profile.md"), ("preferences.md", "preferences.md")):
            self.assertEqual((self.root / "workspace" / name).read_bytes(), (templates / template).read_bytes())

    def test_reimport_of_identical_resume_is_idempotent(self):
        source = self.synthetic_resume()
        initialize(self.root, resume_file=source)
        target = self.root / "workspace"
        before = {p.relative_to(target): p.read_bytes() for p in target.rglob("*") if p.is_file()}
        config_before = (self.root / CONFIG_NAME).read_bytes()
        created, _ = initialize(self.root, resume_file=source)
        self.assertFalse(created)
        self.assertEqual(before, {p.relative_to(target): p.read_bytes() for p in target.rglob("*") if p.is_file()})
        self.assertEqual((self.root / CONFIG_NAME).read_bytes(), config_before)

    def test_resume_name_collision_preserves_existing_resume_and_source(self):
        source = self.synthetic_resume(content=b"Synthetic first version\n")
        initialize(self.root, resume_file=source)
        target = self.root / "workspace"
        before = {p.relative_to(target): p.read_bytes() for p in target.rglob("*") if p.is_file()}
        config_before = (self.root / CONFIG_NAME).read_bytes()
        source.write_bytes(b"Synthetic conflicting second version\n")
        with self.assertRaises((ValueError, FileExistsError)):
            initialize(self.root, resume_file=source)
        self.assertEqual(before, {p.relative_to(target): p.read_bytes() for p in target.rglob("*") if p.is_file()})
        self.assertEqual((self.root / CONFIG_NAME).read_bytes(), config_before)
        self.assertEqual(source.read_bytes(), b"Synthetic conflicting second version\n")

    def test_invalid_resume_is_rejected_before_workspace_creation(self):
        missing = Path(self.temp.name) / "missing.pdf"
        unsupported = self.synthetic_resume(".bin")
        directory = Path(self.temp.name) / "directory.pdf"
        directory.mkdir()
        for source in (missing, unsupported, directory):
            with self.subTest(source=source.name), self.assertRaises((ValueError, FileNotFoundError)):
                initialize(self.root, resume_file=source)
            self.assertFalse((self.root / "workspace").exists())
            self.assertFalse((self.root / CONFIG_NAME).exists())

    def test_bind_existing_and_resume_import_cannot_be_combined(self):
        target = Path(self.temp.name) / "existing-private"
        target.mkdir()
        for name in ("profile.md", "preferences.md"):
            (target / name).write_text("Synthetic existing private facts\n", encoding="utf-8")
        before = {p.name: p.read_bytes() for p in target.iterdir()}
        source = self.synthetic_resume()
        original = source.read_bytes()
        with self.assertRaises(ValueError):
            initialize(self.root, workspace=target, use_existing=True, resume_file=source)
        self.assertEqual(before, {p.name: p.read_bytes() for p in target.iterdir()})
        self.assertEqual(source.read_bytes(), original)
        self.assertFalse((self.root / CONFIG_NAME).exists())
        self.assertFalse((self.root / "workspace").exists())

    def test_imported_resume_and_workspace_remain_git_ignored(self):
        source = self.synthetic_resume(".docx")
        initialize(self.root, resume_file=source)
        self.git("add", ".")
        public_paths = self.git("ls-files").decode().splitlines()
        self.assertFalse(any(name.startswith("workspace/") for name in public_paths))
        self.assertNotIn(CONFIG_NAME, public_paths)
        self.assertNotIn(source.name, public_paths)
        self.assertEqual(audit(self.root), [])
        self.assertEqual((self.root / "workspace/resume" / source.name).read_bytes(), source.read_bytes())

    def test_invalid_workspace_targets_are_rejected(self):
        for target in (".", "..", "data/personal"):
            with self.subTest(target=target), self.assertRaises(ValueError):
                initialize(self.root, workspace=target)
        self.assertFalse((self.root / CONFIG_NAME).exists())

    def test_use_existing_requires_existing_facts_and_preferences(self):
        with self.assertRaises(ValueError):
            initialize(self.root, workspace="../missing", use_existing=True)
        self.assertFalse((self.root / CONFIG_NAME).exists())

    def test_initialization_refuses_linked_workspace(self):
        (self.root / "workspace").symlink_to(self.root / "skills/setup-workspace/assets/templates", target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            initialize(self.root)
        self.assertFalse((self.root / CONFIG_NAME).exists())

    def test_legacy_workspace_does_not_silently_create_a_second_one(self):
        self.write("local/profile.md", "Synthetic existing facts\n")
        with self.assertRaisesRegex(ValueError, "Legacy"):
            initialize(self.root)
        self.assertFalse((self.root / "workspace").exists())

    def test_normal_add_excludes_workspace_configuration_and_legacy_personal_paths(self):
        initialize(self.root)
        fixtures = ("workspace/resume/resume.md", "workspace/applications/example/log.md",
                    "local/profile.md", "applications/example/log.md", "private/note.md",
                    "resume/resume.md", "resumes/resume.md", "profile.md", ".env", "draft.eml")
        for name in fixtures:
            self.write(name, "Synthetic private fixture\n")
        self.git("add", ".")
        paths = set(self.git("ls-files").decode().splitlines())
        self.assertIn("skills/setup-workspace/assets/templates/profile.md", paths)
        self.assertFalse(paths.intersection((*fixtures, CONFIG_NAME)))
        self.assertFalse(any(p.startswith("workspace/") for p in paths))
        self.assertEqual(audit(self.root), [])

    def test_force_added_workspace_and_path_configuration_are_blocked(self):
        for name in ("workspace/profile.md", CONFIG_NAME):
            with self.subTest(name=name):
                self.write(name, "Synthetic private fixture\n")
                self.git("add", "-f", name)
                self.assertTrue(any("Index: " + name in p for p in audit(self.root)))

    def test_missing_nested_repository_cannot_use_parent_workspace(self):
        nested = self.root / "shared-project"
        nested.mkdir()
        self.write("docs/personal-note.md", "Synthetic private parent content\n")
        self.git("add", "docs/personal-note.md")
        self.assertTrue(any("Repository root mismatch" in p for p in audit(nested)))

    def test_deleted_private_history_is_still_blocked(self):
        self.write("workspace/profile.md", "Synthetic private fixture\n")
        self.git("add", "-f", "workspace/profile.md")
        self.git("commit", "-qm", "Synthetic fixture")
        self.git("rm", "-q", "workspace/profile.md")
        self.git("commit", "-qm", "Remove synthetic fixture")
        self.assertTrue(any("History: workspace/profile.md" in p for p in audit(self.root)))

    def test_historical_public_views_are_allowed_after_catalog_migration(self):
        self.write("companies/example.md", "Synthetic public view\n")
        self.git("add", "companies/example.md")
        self.git("commit", "-qm", "Old public view")
        (self.root / "catalog/companies").mkdir(parents=True)
        self.git("mv", "companies/example.md", "catalog/companies/example.md")
        self.git("commit", "-qm", "Intermediate public view layout")
        (self.root / "data/views/companies").mkdir(parents=True)
        self.git("mv", "catalog/companies/example.md", "data/views/companies/example.md")
        self.assertEqual(audit(self.root), [])

    def test_retired_root_layout_and_duplicate_indexes_cannot_be_reintroduced(self):
        for name in ("docs/sample.md", "scripts/sample.py", "templates/sample.md", "catalog/sample.md",
                     "schemas/sample.json", "tests/sample.py", "data/targets.json", "data/investor-index.json",
                     "data/investors/sample.json", "data/views/investors/sample.md", "data/platforms.json"):
            with self.subTest(name=name):
                self.write(name, "Synthetic obsolete-layout fixture\n")
                self.git("add", name)
                self.assertTrue(any("Index: " + name in p for p in audit(self.root)))

    def test_unexpected_top_level_file_is_blocked(self):
        self.write("personal-notes.md", "Synthetic fixture\n")
        self.git("add", "personal-notes.md")
        self.assertTrue(any("outside the shared file allowlist" in p for p in audit(self.root)))

    def test_shared_symlink_is_blocked(self):
        (self.root / "data").mkdir()
        (self.root / "data/linked.md").symlink_to("../workspace/profile.md")
        self.git("add", "data/linked.md")
        self.assertTrue(any("symlink" in p for p in audit(self.root)))

    def test_home_paths_and_credentials_are_blocked_without_echoing_content(self):
        fixtures = ("/" + "home" + "/example/person/private.md", "ghp_" + "a" * 36,
                    "sk-proj-" + "b" * 40, "-----BEGIN " + "PRIVATE KEY-----")
        for content in fixtures:
            with self.subTest(kind=content[:3]):
                self.write("data/sample.md", content + "\n")
                self.git("add", "data/sample.md")
                problems = audit(self.root)
                self.assertTrue(any("content withheld" in p for p in problems))
                self.assertNotIn(content, "\n".join(problems))


if __name__ == "__main__":
    unittest.main()
