from __future__ import annotations

CATEGORIES = {
    "UTILS": [],
    "RECON": [],
    "ATTACK": [
        "BRUTEFORCE-SPRAY",
        "LISTEN-SERVE",
        "FILE_TRANSFERT",
        "CONNECT",
        "EXPLOIT",
        "MITM",
        "REVERSE_SHELL",
        "INJECTION",
    ],
    "CODE": [
        "SAMPLE",
        "WHITEBOX",
    ],
    "CRACKING": [
        "PASSWORD",
    ],
    "PIVOT": [
        "TUNNEL-PORTFW",
    ],
    "PRIVESC": [],
    "POSTEXPLOIT": [
        "CREDS_RECOVER",
    ],
    "PERSIST": [],
}

PLATFORMS = {
    "Linux": "linux",
    "Windows": "windows",
    "macOS": "mac",
    "Multiple": "multiple",
}

TARGETS = {
    "Local": "local",
    "Remote": "remote",
    "Server": "serve",
}

DEFAULT_CHEATS_DIR = "~/.cheats"
ARSENAL_PACKAGE = "arsenal-cli"

CATEGORY_CHOICES = list(CATEGORIES.keys()) + [
    f"{parent}/{child}"
    for parent, children in CATEGORIES.items()
    for child in children
]
