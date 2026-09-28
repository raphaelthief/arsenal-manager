from pathlib import Path

from arsenal_manager.generator import render_markdown, write_cheat
from arsenal_manager.models import Cheat


def test_render():
    cheat = Cheat(
        title="Nmap Service Enumeration",
        description="Enumerate services.",
        command="nmap -sC -sV <target>",
        categories=["RECON"],
        platforms=["linux"],
        targets=["remote"],
        tags=["nmap", "enumeration"],
    )
    text = render_markdown(cheat)
    assert "# RECON" in text
    assert "#cat/RECON" in text
    assert "#plateform/linux" in text
    assert "#target/remote" in text
    assert "Nmap Service Enumeration" in text


def test_write(tmp_path: Path):
    cheat = Cheat(
        title="Test Cheat",
        description="Description",
        command="echo test",
        categories=["UTILS"],
        platforms=["linux"],
        targets=["local"],
    )
    path = write_cheat(cheat, tmp_path)
    assert path.exists()
    assert path.name == "test-cheat.md"
