"""Create one ignored workspace or bind an existing private workspace without copying it."""
import argparse
from pathlib import Path

from workspace import ROOT, bind_workspace, resolve_workspace, workspace_path

COPIES = {
    "AGENTS.md": "workspace-agent-rules.md",
    "profile.md": "profile.md",
    "preferences.md": "preferences.md",
    "applications/index.md": "applications-index.md",
}
DIRECTORIES = ("resume",)
RESUME_SUFFIXES = frozenset({".pdf", ".docx", ".md", ".txt"})


def initialize(root=ROOT, workspace=None, use_existing=False, resume_file=None):
    root = Path(root).resolve()
    target = resolve_workspace(root, workspace) if workspace is not None else workspace_path(root)
    if target.is_symlink() or (target.exists() and not target.is_dir()):
        raise ValueError("Expected a real private workspace directory.")
    if use_existing:
        if resume_file is not None:
            raise ValueError("--use-existing only binds existing records; import a resume as a separate explicit task.")
        if not target.is_dir() or not all((target / name).is_file() for name in ("profile.md", "preferences.md")):
            raise ValueError("An existing workspace must contain profile.md and preferences.md.")
        bind_workspace(root, target)
        return [], []
    resume_source = None
    resume_target = None
    resume_content = None
    if resume_file is not None:
        resume_source = Path(resume_file).expanduser().resolve(strict=True)
        if not resume_source.is_file() or resume_source.suffix.lower() not in RESUME_SUFFIXES:
            raise ValueError("Provide a PDF, DOCX, Markdown or plain-text resume file.")
        resume_target = target / "resume" / resume_source.name
        if resume_target.is_symlink():
            raise ValueError("Resume destination must not be a symlink.")
        resume_content = resume_source.read_bytes()
    if workspace is None and not target.exists() and any((root / name).exists() for name in ("local", "applications")):
        raise ValueError("Legacy personal folders found. Consolidate them, then bind with --workspace PATH --use-existing.")
    paths = [target / name for name in (*COPIES, *DIRECTORIES)]
    for path in paths:
        for part in (path, *path.parents):
            if part.is_symlink():
                raise ValueError("Workspace paths must not be symlinks.")
            if part == target:
                break
            if part != path and part.exists() and not part.is_dir():
                raise ValueError("Expected a workspace directory.")
        directory = path.relative_to(target).as_posix() in DIRECTORIES
        if path.exists() and path.is_dir() != directory:
            raise ValueError("Unexpected workspace path type.")
    if resume_target is not None and resume_target.exists():
        if not resume_target.is_file() or resume_target.read_bytes() != resume_content:
            raise FileExistsError("A different resume already uses this filename; preserve it and choose another name.")
    contents = {name: (root / "skills" / "setup-workspace" / "assets" / "templates" / template).read_text(encoding="utf-8")
                for name, template in COPIES.items()}
    created, kept = [], []
    for name, content in contents.items():
        path = target / name
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with path.open("x", encoding="utf-8") as stream:
                stream.write(content)
            created.append(name)
        except FileExistsError:
            kept.append(name)
    for name in DIRECTORIES:
        (target / name).mkdir(parents=True, exist_ok=True)
    if resume_source is not None and not resume_target.exists():
        # Only an explicitly supplied resume is imported. This command does not
        # extract personal facts or infer preferences; the Agent does that next.
        with resume_target.open("xb") as stream:
            stream.write(resume_content)
    bind_workspace(root, target)
    return created, kept


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", help="Private workspace path; default is the configured path or workspace/")
    parser.add_argument("--use-existing", action="store_true", help="Only bind; do not create or copy personal files")
    parser.add_argument("--resume-file", help="Explicit resume to copy into the ignored resume/ directory; Agent extraction follows separately")
    args = parser.parse_args()
    added, existing = initialize(workspace=args.workspace, use_existing=args.use_existing, resume_file=args.resume_file)
    print("Existing workspace bound; no personal files copied." if args.use_existing else
          "Workspace ready: %d blank files created, %d existing files preserved." % (len(added), len(existing)))
    print("Personal contents and workspace.local.json stay outside shared commits.")
    if not args.use_existing:
        print("Next: Agent reads the provided resume into profile.md, proposes directions, and asks for location and salary expectations in preferences.md.")
        print("This command creates templates and optionally imports a resume; it does not extract or invent personal facts.")
