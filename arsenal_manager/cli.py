from __future__ import annotations

from pathlib import Path
import typer
import questionary
import os
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from .arsenal_config import (
                                ArsenalNotFound, disable_tiocsti_persistent, disable_tiocsti_session,
                                enable_tiocsti_persistent, enable_tiocsti_session,
                                extract_cheats_paths, find_arsenal_executable, find_config_path,
                                tiocsti_persistent_state,
                                install_arsenal, patch_cheats_paths, restore_latest_backup, tiocsti_state,
                            )
from .constants import DEFAULT_CHEATS_DIR
from .interactive import create_cheat_interactive, main_menu, manage_cheats_interactive, manage_arsenal_variables_interactive
from .validator import validate_file

app = typer.Typer(help="Interactive manager for Arsenal cheatsheets.")
cheat_app = typer.Typer(help="Manage custom cheats.")
app.add_typer(cheat_app, name="cheat")
console = Console()
console = Console()
QUESTIONARY_STYLE = questionary.Style([("question", "fg:cyan bold"), ("pointer", "fg:red bold"),])

def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")

def cheats_dir() -> Path:
    path = Path(DEFAULT_CHEATS_DIR).expanduser()
    path.mkdir(parents=True, exist_ok=True)
    return path

@app.callback(invoke_without_command=True)
def root(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        interactive()

@app.command()
def interactive():
    """Open the interactive menu."""
    while True:
        clear_screen()
        choice = main_menu()
        if not choice or choice.startswith("0."):
            console.print("[cyan]Bye.[/cyan]")
            return
            
        pause = True
        
        try:
            if choice.startswith("1."): create_cheat_interactive(cheats_dir())
            elif choice.startswith("2."): pause = manage_cheats_interactive(cheats_dir())
            elif choice.startswith("3."): pause = manage_arsenal_variables_interactive()
            elif choice.startswith("4."): _validate()
            elif choice.startswith("5."): pause = configure_interactive()
            elif choice.startswith("6."): status()
            elif choice.startswith("7."): restore()
            elif choice.startswith("8."): install(force=True)
            elif choice.startswith("9."): pause = tiocsti_menu()
        except (ArsenalNotFound, RuntimeError, FileNotFoundError, ValueError) as exc:
            console.print(f"[bold red]✗ Error:[/bold red] {exc}")
        except KeyboardInterrupt:
            console.print("\n[yellow]Cancelled.[/yellow]")

        if pause:
            input("\nPress Enter to continue...")


def configure_interactive() -> bool:
    clear_screen()
    current_mode = "UNKNOWN"
    try:
        config = find_config_path()
        paths = extract_cheats_paths(config.read_text(encoding="utf-8"), config)
        default_candidates = {
            str(config.parent.parent / "data" / "cheats"),
            str(config.parent.parent / "cheats"),
            str(config.parent.parent.parent / "cheats")
        }

        only_custom = (bool(paths) and len(paths) == 1 and paths[0] not in default_candidates)
        if only_custom:
            current_mode = "[bold cyan]ONLY MY CHEATS[/bold cyan]"
        else:
            current_mode = ("[bold magenta]MY CHEATS + ARSENAL BUNDLED CHEATS[/bold magenta]")

    except ArsenalNotFound as exc:
        current_mode = f"[bold red]ERROR: {exc}[/bold red]"

    console.print(
        Panel(
            "[cyan]Arsenal cheats visibility[/cyan]\n"
            "Arsenal internal commands such as >set, >show, >clear "
            "and >exit remain available.\n\n"
            f"Current configuration: {current_mode}",
            title="Configure Arsenal",
            expand=False,
        )
    )

    choice = questionary.select(
        "Choose an option",
        choices=[
            "1. Only my cheats",
            "2. My cheats + Arsenal bundled cheats",
            "Back",
        ],
        instruction="Use ↑/↓ and Enter",
        style=QUESTIONARY_STYLE
    ).ask()

    if not choice or choice == "Back":
        return False

    if choice == "1. Only my cheats":
        configure(keep_default=False)
    elif choice == "2. My cheats + Arsenal bundled cheats":
        configure(keep_default=True)

    return True
    

def tiocsti_menu() -> bool:
    clear_screen()

    current = tiocsti_state()
    persistent = tiocsti_persistent_state()

    if current:
        current_label = "[green]ENABLED[/green]"
    else:
        current_label = "[red]DISABLED[/red]"

    if persistent:
        persistent_label = "[green]ENABLED (manager file)[/green]"
    else:
        persistent_label = "[red]DISABLED[/red]"

    console.print(
        Panel(
            "[cyan]Configure the Linux TIOCSTI kernel setting required "
            "by Arsenal to run commands from the terminal.[/cyan]\n\n"
            f"Current session : {current_label}\n"
            f"After reboot    : {persistent_label}",
            title="TIOCSTI configuration",
            expand=False,
        )
    )

    choice = questionary.select(
        "Choose an action",
        choices=[
            "1. Enable for current session only",
            "2. Enable now + persist after reboot",
            "3. Disable for current session only",
            "4. Remove this manager's persistent setting",
            "Back"
        ],
        instruction="Use ↑/↓ and Enter",
        style=QUESTIONARY_STYLE,
    ).ask()

    if not choice or choice == "Back":
        return False

    if choice == "1. Enable for current session only":
        enable_tiocsti_session()
    elif choice == "2. Enable now + persist after reboot":
        enable_tiocsti_persistent()
    elif choice == "3. Disable for current session only":
        disable_tiocsti_session()
    elif choice == "4. Remove this manager's persistent setting":
        disable_tiocsti_persistent()

    return True


@app.command()
def install(force: bool = typer.Option(False, "--force", help="Run pipx install --force.")):
    """Install/update Arsenal for the current user with pipx; never runs sudo."""
    try:
        clear_screen()
        console.print(
            Panel(
                "[cyan]Install or update Arsenal using pipx.[/cyan]\n"
                "The installation is isolated from the system Python environment.",
                title="Install / update Arsenal",
                expand=False
            )
        )
        
        console.print(f"[green]{install_arsenal(force_pipx=force)}[/green]")
        if tiocsti_state() in {"disabled", "unknown"}:
            console.print("[yellow]Arsenal may require the TIOCSTI workaround; see menu option 8.[/yellow]")
    except RuntimeError as exc:
        console.print(f"[bold red]✗ Error:[/bold red] {exc}")
        raise typer.Exit(code=1)

@app.command()
def configure(keep_default: bool = typer.Option(False, "--keep-default", help="Keep bundled cheats too.")):
    """Choose custom-only or custom-plus-bundled cheats."""
    try:
        config = find_config_path()
        backup = patch_cheats_paths(config, cheats_dir(), keep_default=keep_default)
        mode = "MY CHEATS + DEFAULTS" if keep_default else "ONLY MY CHEATS"
        console.print(f"[bold green]✓ Configured:[/bold green] [cyan]{mode}[/cyan]")
        console.print(f"  Config : {config}\n  Cheats : {cheats_dir()}\n  Backup : {backup}")
    except ArsenalNotFound as exc:
        console.print(f"[bold red]✗ Error:[/bold red] {exc}")
        raise typer.Exit(code=1)

@app.command()
def restore():
    """Restore the latest Arsenal configuration backup."""
    try:
        clear_screen()
        console.print(
            Panel(
                "[cyan]Restore the latest backup of the Arsenal configuration.[/cyan]\n"
                "Use this to undo the last configuration changes made by Arsenal Manager.",
                title="Restore Arsenal configuration",
                expand=False,
            )
        )
        
        config = find_config_path()
        backup = restore_latest_backup(config)
        console.print(f"[green]✓ Restored:[/green] {config}\n[dim]From:[/dim] {backup}")
    except (ArsenalNotFound, FileNotFoundError) as exc:
        console.print(f"[bold red]✗ Error:[/bold red] {exc}")
        raise typer.Exit(code=1)

@app.command()
def status():
    """Show colorful Arsenal and manager status."""
    clear_screen()
    console.print(
        Panel(
            "[cyan]Display the current Arsenal installation, "
            "configuration and TIOCSTI status.[/cyan]",
            title="Arsenal status",
            expand=False,
        )
    )
    
    table = Table(title="")
    table.add_column("Item", style="bold")
    table.add_column("Status", justify="center")
    table.add_column("Value")
    
    try:
        exe = find_arsenal_executable()
        table.add_row("Arsenal executable", "[bold green]FOUND[/bold green]", str(exe))
    except ArsenalNotFound as exc:
        table.add_row("Arsenal executable", "[bold red]MISSING[/bold red]", str(exc))
    directory = Path(DEFAULT_CHEATS_DIR).expanduser()
    table.add_row("Custom cheats directory", "[green]FOUND[/green]" if directory.exists() else "[yellow]MISSING[/yellow]", str(directory))

    variables_file = Path("~/.arsenal.json").expanduser()
    table.add_row("Arsenal variables", "[bold green]FOUND[/bold green]" if variables_file.exists() else "[yellow]MISSING[/yellow]", str(variables_file))
        
    try:
        config = find_config_path()
        table.add_row("Arsenal config", "[bold green]FOUND[/bold green]", str(config))
        paths = extract_cheats_paths(config.read_text(encoding="utf-8"), config)
        for i, path in enumerate(paths, 1):
            default_candidates = {
                str(config.parent.parent / "data" / "cheats"),
                str(config.parent.parent / "cheats"),
                str(config.parent.parent.parent / "cheats")
            }
            
            is_default = path in default_candidates
            table.add_row(f"CHEATS_PATHS[{i}]", "[yellow]DEFAULT[/yellow]" if is_default else "[cyan]CUSTOM[/cyan]", path)
        
        default_candidates = {
            str(config.parent.parent / "data" / "cheats"),
            str(config.parent.parent / "cheats"),
            str(config.parent.parent.parent / "cheats")
        }
        
        only_custom = bool(paths) and len(paths) == 1 and paths[0] not in default_candidates
        table.add_row("Cheat visibility", "[bold cyan]ONLY MY CHEATS[/bold cyan]" if only_custom else "[bold magenta]MY CHEATS + DEFAULTS[/bold magenta]", "")
    except ArsenalNotFound as exc:
        table.add_row("Arsenal config", "[bold red]ERROR[/bold red]", str(exc))
        
    state = tiocsti_state()
    label = {"enabled":"[bold green]ENABLED[/bold green]","disabled":"[bold yellow]DISABLED[/bold yellow]", "unsupported":"[dim]UNSUPPORTED[/dim]","unknown":"[yellow]UNKNOWN[/yellow]"}.get(state, "[yellow]UNKNOWN[/yellow]")
    table.add_row("TIOCSTI (current session)", label, "effective kernel value right now")
    persistent = tiocsti_persistent_state()
    persistent_label = {
        "manager-file": "[bold green]ENABLED[/bold green]",
        "sysctl-conf": "[bold green]ENABLED[/bold green]",
        "disabled": "[yellow]DISABLED[/yellow]",
        "not-configured": "[yellow]NOT CONFIGURED[/yellow]",
    }.get(persistent, "[yellow]UNKNOWN[/yellow]")
    
    table.add_row("TIOCSTI (after reboot)", persistent_label, persistent)
    console.print(table)

@cheat_app.command("new")
def new():
    create_cheat_interactive(cheats_dir())

@cheat_app.command("list")
def list_cheats():
    files = sorted(cheats_dir().glob("*.md"))
    if not files:
        console.print("[yellow]No custom cheats yet.[/yellow]")
        return
    for path in files:
        console.print(f"[cyan]•[/cyan] {path.stem}")

@cheat_app.command("show")
def show(name: str):
    matches = list(cheats_dir().glob(f"{name}.md")) + list(cheats_dir().glob(name))
    if not matches:
        console.print(f"[red]Not found:[/red] {name}")
        raise typer.Exit(code=1)
    console.print(matches[0].read_text(encoding="utf-8"))

def _validate() -> bool:
    clear_screen()
    console.print(
        Panel(
            "[cyan]Check the structure, required tags and command "
            "blocks of your custom Arsenal cheats.[/cyan]",
            title="Validate cheats",
            expand=False,
        )
    )
    
    directory = cheats_dir()
    files = sorted(directory.rglob("*.md"))
    if not files:
        console.print("[yellow]No custom cheats found.[/yellow]")
        return False
        
    table = Table(title="")
    table.add_column("Status", justify="center")
    table.add_column("Cheat")
    table.add_column("Details")
    invalid = 0
    valid = 0
    for path in files:
        problems = validate_file(path)
        if not problems:
            valid += 1
            table.add_row("[green]✓ VALID[/green]", path.stem, "OK")
        else:
            invalid += 1
            details = "; ".join(problems) if problems else "Invalid structure"
            table.add_row("[red]✗ INVALID[/red]", path.stem, details)
    console.print(table)
    console.print(f"\n[green]{valid} valid[/green] • [red]{invalid} invalid[/red] • {len(files)} total")
    return invalid > 0


@cheat_app.command("validate")
def validate():
    if _validate():
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
