from __future__ import annotations

from pathlib import Path
import subprocess
import questionary
import os
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from .constants import CATEGORY_CHOICES, PLATFORMS, TARGETS
from .generator import render_markdown, validate_cheat, write_cheat
from .models import Cheat
from .validator import validate_file
from .arsenal_config import load_arsenal_variables, save_arsenal_variables


console = Console()
QUESTIONARY_STYLE = questionary.Style([
    ("question", "fg:cyan bold"),
    ("pointer", "fg:red bold"),
])


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")

def show_header() -> None:
    console.print(
        Panel(
            "[cyan]Arsenal Manager[/cyan] - [yellow]raphaelthief[/yellow]\n"
            "Manage your personal Arsenal cheatsheets and configuration.",
            title="Menu",
        )
    )

def choose_many(title: str, choices: list[str], all_label: str = "ALL") -> list[str]:
    selected = questionary.checkbox(title, choices=[all_label, *choices], instruction="Space = select • Enter = confirm",).ask()
    if selected is None:
        return []
    if all_label in selected:
        return choices
    return selected


def choose_categories() -> list[str]:
    return choose_many("Select categories", CATEGORY_CHOICES, "ALL CATEGORIES")


def choose_platforms() -> list[str]:
    return choose_many("Select platforms", list(PLATFORMS.keys()), "ALL PLATFORMS")


def choose_targets() -> list[str]:
    return choose_many("Select targets", list(TARGETS.keys()), "ALL TARGETS")


def create_cheat_interactive(output_dir: Path) -> Path | None:
    clear_screen()
    console.print(
        Panel(
            "[cyan]Create a new custom Arsenal cheatsheet in ~/.cheats.[/cyan]\n"
            "Define the title, description, command, platform and target. The cheatsheet will be categorized under CUSTOM.\n"
            "Default variables available: <LHOST> <LPORT> <RHOST> <RPORT> | <user> <password> | <wordlist> \n"
            "[red]>[/red] [blue][<PLATEFORM>] <TARGET> <CATEGORIE>[/blue] [cyan]CUSTOM[/cyan] [yellow]<YOUR_TITLE>[/yellow] [magenta]<YOUR_COMMAND>[/magenta]\n"
            "[dim]Example:[/dim]\n"
            "[red]>[/red] [blue][L] Rem RECON[/blue] [cyan]CUSTOM[/cyan] [yellow]nmap - hosts alive[/yellow] [magenta]nmap -sn <ip_range>[/magenta]",
            title="Create a cheat",
            expand=False
        )
    )

    title = questionary.text("Title:").ask()
    if not title:
        return None
    description = questionary.text("Description:").ask() or ""
    command = questionary.text("Command:").ask()
    if not command:
        return None
    categories = choose_categories()
    platforms = choose_platforms()
    targets = choose_targets()
    tags = [x.strip() for x in (questionary.text("Extra tags (comma-separated):").ask() or "").split(",") if x.strip()]

    cheat = Cheat(title=title, description=description, command=command, categories=categories, platforms=platforms, targets=targets, tags=tags)
    errors = validate_cheat(cheat)
    if errors:
        for error in errors:
            console.print(f"[red]✗[/red] {error}")
        return None

    console.print(Panel(render_markdown(cheat), title="Preview", expand=False))
    if not questionary.confirm("Save this cheat?").ask():
        return None
    path = write_cheat(cheat, output_dir)
    console.print(f"[green]Saved:[/green] {path}")
    return path


def _cheat_rows(directory: Path) -> list[tuple[Path, bool, str]]:
    rows = []
    for path in sorted(directory.glob("*.md")):
        problems = validate_file(path)
        valid = not problems
        rows.append((path, valid, problems[0] if problems else "Valid"))
    return rows


def manage_cheats_interactive(directory: Path) -> bool:
    """Browse custom cheats, show them, and optionally edit them with nano."""
    while True:
        clear_screen()
        console.print(
            Panel(
                "[cyan]Browse, validate, edit or delete your custom "
                "Arsenal cheats.[/cyan]",
                title="My Cheats",
                expand=False,
            )
        )

        rows = _cheat_rows(directory)
        if not rows:
            console.print("[yellow]No custom cheats yet.[/yellow]")
            return True

        table = Table(title="")
        table.add_column("#", justify="right", style="bold")
        table.add_column("Status", justify="center")
        table.add_column("Cheat")
        for index, (path, valid, _) in enumerate(rows, 1):
            table.add_row(str(index), "[green]✓ VALID[/green]" if valid else "[red]✗ INVALID[/red]", path.stem)
        console.print(table)

        choices = [f"{i}. {path.stem}" for i, (path, _, _) in enumerate(rows, 1)] + ["Back"]
        selected = questionary.select("Select a cheat", choices=choices, instruction="↑/↓ + Enter", style=QUESTIONARY_STYLE).ask()
        if not selected or selected == "Back":
            return False
            
        index = int(selected.split(".", 1)[0]) - 1
        path, valid, problem = rows[index]

        console.print(Panel(path.read_text(encoding="utf-8"), title=f"{path.stem} — {'VALID' if valid else 'INVALID'}", expand=False))
        if not valid:
            console.print(f"[red]Validation:[/red] {problem}")
        action = questionary.select("What do you want to do?", choices=["Delete cheat", "Edit with nano", "Back"], style=QUESTIONARY_STYLE).ask()
        if action == "Edit with nano":
            editor = __import__("shutil").which("nano")
            if not editor:
                console.print("[red]nano was not found on PATH.[/red]")
                continue
            subprocess.run([editor, str(path)], check=False)
            problems = validate_file(path)
            if problems:
                console.print("[red]✗ Still invalid:[/red]")
                for item in problems:
                    console.print(f"  [red]•[/red] {item}")
            else:
                console.print(f"[green]✓ Valid:[/green] {path.name}")
        elif action == "Delete cheat":
            confirm = questionary.confirm(f'Delete "{path.stem}"?', default=False,).ask()
            if confirm:
                try:
                    path.unlink()
                    console.print(f"[green]✓ Deleted:[/green] {path.name}")
                except OSError as exc:
                    console.print(f"[red]✗ Unable to delete:[/red] {exc}")


def manage_arsenal_variables_interactive() -> bool:
    """Manage Arsenal global variables stored in ~/.arsenal.json."""
    while True:
        clear_screen()
        
        console.print(
            Panel(
                "[cyan]Manage the global variables used by Arsenal.[/cyan]\n"
                "Changes are saved directly to ~/.arsenal.json.",
                title="Arsenal variables",
                expand=False,
            )
        )

        try:
            variables = load_arsenal_variables()
        except RuntimeError as exc:
            console.print(f"[bold red]✗ Error:[/bold red] {exc}")
            return True

        if variables:
            table = Table()
            table.add_column("Variable", style="bold")
            table.add_column("Value")

            for name, value in sorted(variables.items()):
                table.add_row(name, value)

            console.print(table)
        else:
            console.print("[yellow]No Arsenal variables configured.[/yellow]")

        choices = [
            "1. Add variable",
            "2. Edit variable",
            "3. Delete variable",
            "4. Clear all variables",
            "Back",
        ]

        action = questionary.select("Choose an action", choices=choices, instruction="Use ↑/↓ and Enter", style=QUESTIONARY_STYLE).ask()
        if not action or action == "Back":
            return False

        if action == "1. Add variable":
            name = questionary.text("Variable name:", validate=lambda value: (True if value.strip() else "Variable name cannot be empty."), style=QUESTIONARY_STYLE).ask()
            if name is None:
                continue

            name = name.strip()
            if name in variables:
                console.print(
                    f"[yellow]Variable '{name}' already exists. "
                    "Use Edit variable instead.[/yellow]"
                )
                continue

            value = questionary.text(f"Value for {name}:", style=QUESTIONARY_STYLE).ask()
            if value is None:
                continue

            variables[name] = value

            try:
                save_arsenal_variables(variables)
                console.print(f"[green]✓ Variable '{name}' added.[/green]")
            except RuntimeError as exc:
                console.print(f"[bold red]✗ Error:[/bold red] {exc}")

        elif action == "2. Edit variable":
            if not variables:
                console.print("[yellow]No variables to edit.[/yellow]")
                continue

            name = questionary.select("Select a variable", choices=sorted(variables.keys()), instruction="Use ↑/↓ and Enter", style=QUESTIONARY_STYLE).ask()
            if not name:
                continue

            value = questionary.text(
                f"New value for {name}:",
                default=variables[name],
                style=QUESTIONARY_STYLE,
            ).ask()

            if value is None:
                continue

            variables[name] = value

            try:
                save_arsenal_variables(variables)
                console.print(f"[green]✓ Variable '{name}' updated.[/green]")
            except RuntimeError as exc:
                console.print(f"[bold red]✗ Error:[/bold red] {exc}")

        elif action == "3. Delete variable":
            if not variables:
                console.print("[yellow]No variables to delete.[/yellow]")
                continue

            name = questionary.select("Select a variable", choices=sorted(variables.keys()), instruction="Use ↑/↓ and Enter", style=QUESTIONARY_STYLE).ask()
            if not name:
                continue

            confirm = questionary.confirm(f'Delete variable "{name}"?', default=False, style=QUESTIONARY_STYLE).ask()
            if not confirm:
                continue

            del variables[name]

            try:
                save_arsenal_variables(variables)
                console.print(f"[green]✓ Variable '{name}' deleted.[/green]")
            except RuntimeError as exc:
                console.print(f"[bold red]✗ Error:[/bold red] {exc}")

        elif action == "4. Clear all variables":
            if not variables:
                console.print("[yellow]No variables to clear.[/yellow]")
                continue

            confirm = questionary.confirm("Delete ALL Arsenal variables?", default=False, style=QUESTIONARY_STYLE,).ask()
            if not confirm:
                continue

            try:
                save_arsenal_variables({})
                console.print("[green]✓ All Arsenal variables cleared.[/green]")
            except RuntimeError as exc:
                console.print(f"[bold red]✗ Error:[/bold red] {exc}")



def main_menu() -> str | None:
    clear_screen()
    show_header()
    choices = [
        "1. Create a cheat",
        "2. Manage my cheats (delete or show / edit with nano)",
        "3. Manage Arsenal variables",
        "4. Validate cheats",
        "5. Configure Arsenal cheats",
        "6. Arsenal status",
        "7. Restore Arsenal configuration",
        "8. Install / update Arsenal with pipx",
        "9. TIOCSTI settings",
        "0. Exit"
    ]

    style = questionary.Style([("question", "fg:cyan bold"), ("pointer", "fg:red bold")])
    return questionary.select("Choose an action", choices=choices, instruction="Use ↑/↓ and Enter", style=QUESTIONARY_STYLE).ask()
