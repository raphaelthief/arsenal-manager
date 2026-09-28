from __future__ import annotations

import ast
import os
import re
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


class ArsenalNotFound(RuntimeError):
    pass


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, capture_output=True, check=False)


def find_arsenal_executable() -> Path:
    value = shutil.which("arsenal")
    if not value:
        raise ArsenalNotFound("The 'arsenal' executable was not found on PATH.")
    return Path(value).resolve()


def _config_from_arsenal_python(executable: Path) -> Path | None:
    """Ask the exact Python interpreter shipped with the pipx venv."""
    candidates = [
        executable.parent / "python",
        executable.parent / "python3",
    ]
    for python in candidates:
        if not python.exists():
            continue
        result = run_command([
            str(python), "-c",
            "import arsenal.modules.config as c; print(c.__file__)"
        ])
        if result.returncode == 0:
            path = Path(result.stdout.strip()).resolve()
            if path.exists():
                return path

    # Fallback for wrappers/alternate pipx layouts.
    for parent in [executable.parent, *executable.parents]:
        for pattern in ("lib/python*/site-packages/arsenal/modules/config.py", "lib/python*/site-packages/arsenal*/modules/config.py",):
            matches = list(parent.glob(pattern))
            if matches:
                return matches[0].resolve()
    return None


def find_config_path() -> Path:
    executable = find_arsenal_executable()
    path = _config_from_arsenal_python(executable)
    if path:
        return path

    # Common system/user installations.
    for base in [
        Path.home() / ".local",
        Path("/usr/local"),
        Path("/usr"),
        Path("/opt"),
    ]:
        for match in base.glob("**/site-packages/arsenal/modules/config.py"):
            return match.resolve()

    raise ArsenalNotFound("Could not locate Arsenal's modules/config.py. The 'arsenal' executable was found, but its Python package could not be located.")


def extract_cheats_paths(source: str, config_path: Path | None = None) -> list[str]:
    """Extract literal CHEATS_PATHS entries, resolving simple join()/expanduser() expressions."""
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if "CHEATS_PATHS" not in targets:
                continue
            value = node.value
            if not isinstance(value, (ast.List, ast.Tuple)):
                return []
            paths: list[str] = []
            for item in value.elts:
                if isinstance(item, ast.Constant) and isinstance(item.value, str):
                    paths.append(os.path.expanduser(item.value))
                elif isinstance(item, ast.Call) and isinstance(item.func, ast.Name) and item.func.id == "join":
                    parts = []
                    for arg in item.args:
                        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                            parts.append(arg.value)
                        elif isinstance(arg, ast.Name):
                            if config_path is not None and arg.id == "BASEPATH":
                                parts.append(str(config_path.parent.parent.parent))
                            elif config_path is not None and arg.id == "DATAPATH":
                                parts.append(str(config_path.parent.parent / "data"))
                            elif arg.id == "HOMEPATH":
                                parts.append(str(Path.home()))
                            else:
                                parts.append(f"<{arg.id}>")
                    if parts:
                        paths.append(os.path.join(*parts))
            return paths
    return []


def backup_config(config_path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = Path.home() / ".config" / "arsenal-manager" / "backups" / stamp
    backup_dir.mkdir(parents=True, exist_ok=True)
    destination = backup_dir / "config.py"
    shutil.copy2(config_path, destination)
    return destination


def patch_cheats_paths(config_path: Path, custom_dir: Path, keep_default: bool = False) -> Path:
    """Patch CHEATS_PATHS while preserving a backup and Arsenal's real default path."""
    backup = backup_config(config_path)
    source = config_path.read_text(encoding="utf-8")

    if keep_default:
        default_expr = None
        for line in source.splitlines():
            if "# DEFAULT" in line and line.strip().endswith(", # DEFAULT"):
                default_expr = line.strip().removesuffix(", # DEFAULT")
                break
        if default_expr is None:
            # Current Arsenal stores bundled cheats under arsenal/data/cheats.
            if (config_path.parent.parent / "data" / "cheats").exists() or "DATAPATH" in source:
                default_expr = 'join(DATAPATH, "cheats")'
            else:
                default_expr = 'join(BASEPATH, "cheats")'
        replacement = (
            "CHEATS_PATHS = [\n"
            f"    {default_expr}, # DEFAULT\n"
            f"    r\"{custom_dir}\",\n"
            "]"
        )
    else:
        replacement = f'CHEATS_PATHS = [r"{custom_dir}"]'

    pattern = re.compile(r"(?ms)^CHEATS_PATHS\s*=\s*\[.*?\]\s*(?=\n|$)")
    updated, count = pattern.subn(replacement, source, count=1)
    if count != 1:
        raise RuntimeError("Could not find the CHEATS_PATHS list in Arsenal's config.py.")

    config_path.write_text(updated, encoding="utf-8")
    return backup


def restore_latest_backup(config_path: Path) -> Path:
    backup_root = Path.home() / ".config" / "arsenal-manager" / "backups"
    backups = sorted(backup_root.glob("*/config.py"))
    if not backups:
        raise FileNotFoundError("No Arsenal Manager backup was found.")
    backup = backups[-1]
    shutil.copy2(backup, config_path)
    return backup


def install_arsenal(force_pipx: bool = False) -> str:
    """Install/update Arsenal with pipx for the current user. Never calls sudo."""
    existing = shutil.which("arsenal")
    pipx = shutil.which("pipx")
    if not pipx:
        raise RuntimeError("pipx is required. This installer never runs sudo.")
    if existing and not force_pipx:
        return f"Arsenal already available: {existing}"
    args = [pipx, "install"]
    if force_pipx:
        args.append("--force")
    args.append("arsenal-cli")
    result = run_command(args)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "pipx installation failed.")
    return result.stdout.strip() or "Arsenal installed with pipx."


def tiocsti_persistent_state() -> str:
    """Return whether the manager's persistent TIOCSTI override is configured."""
    manager_file = Path("/etc/sysctl.d/99-arsenal-tiocsti.conf")
    try:
        if manager_file.exists() and "dev.tty.legacy_tiocsti=1" in manager_file.read_text(encoding="utf-8"):
            return "manager-file"
    except PermissionError:
        pass

    sysctl_conf = Path("/etc/sysctl.conf")
    try:
        if sysctl_conf.exists():
            for line in sysctl_conf.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("dev.tty.legacy_tiocsti=") and not line.startswith("#"):
                    return "sysctl-conf" if line.endswith("=1") else "disabled"
    except PermissionError:
        pass
    return "not-configured"


def tiocsti_state() -> str:
    sysctl = shutil.which("sysctl")
    if not sysctl:
        return "unknown"
    result = run_command([sysctl, "-n", "dev.tty.legacy_tiocsti"])
    if result.returncode != 0:
        return "unsupported"
    return "enabled" if result.stdout.strip() == "1" else "disabled"


def enable_tiocsti_session() -> str:
    if not shutil.which("sudo"):
        raise RuntimeError("sudo was not found.")
    result = run_command(["sudo", "sysctl", "-w", "dev.tty.legacy_tiocsti=1"])
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Could not enable TIOCSTI.")
    return result.stdout.strip() or "TIOCSTI enabled for the current session."


def disable_tiocsti_session() -> str:
    if not shutil.which("sudo"):
        raise RuntimeError("sudo was not found.")
    result = run_command(["sudo", "sysctl", "-w", "dev.tty.legacy_tiocsti=0"])
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Could not disable TIOCSTI.")
    return result.stdout.strip() or "TIOCSTI disabled for the current session."


def disable_tiocsti_persistent() -> str:
    if not shutil.which("sudo"):
        raise RuntimeError("sudo was not found.")
    manager_file = "/etc/sysctl.d/99-arsenal-tiocsti.conf"
    command = f"if [ -f {manager_file} ]; then sudo rm -f {manager_file}; fi; sudo sysctl --system"
    result = subprocess.run(["bash", "-lc", command], text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Could not remove the persistent TIOCSTI override.")
    return "Manager's persistent TIOCSTI override removed; system sysctl configuration reloaded."


def enable_tiocsti_persistent() -> str:
    if not shutil.which("sudo"):
        raise RuntimeError("sudo was not found.")
    command = (
        "printf '%s\\n' 'dev.tty.legacy_tiocsti=1' "
        "| sudo tee /etc/sysctl.d/99-arsenal-tiocsti.conf >/dev/null "
        "&& sudo sysctl --system"
    )
    result = subprocess.run(["bash", "-lc", command], text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Could not persist TIOCSTI.")
    return "TIOCSTI enabled now and persisted in /etc/sysctl.d/99-arsenal-tiocsti.conf."






def arsenal_variables_path() -> Path:
    """Return Arsenal's global variables file."""
    return Path("~/.arsenal.json").expanduser()


def load_arsenal_variables() -> dict[str, str]:
    """Load Arsenal global variables from ~/.arsenal.json."""
    path = arsenal_variables_path()

    if not path.exists():
        return {}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"Unable to read Arsenal variables file {path}: {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise RuntimeError(
            f"Invalid Arsenal variables file: {path} must contain a JSON object."
        )

    return {
        str(key): str(value)
        for key, value in data.items()
    }


def save_arsenal_variables(variables: dict[str, str]) -> None:
    """Save Arsenal global variables to ~/.arsenal.json."""
    path = arsenal_variables_path()

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                variables,
                indent=2,
                ensure_ascii=False,
            ) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        raise RuntimeError(
            f"Unable to write Arsenal variables file {path}: {exc}"
        ) from exc