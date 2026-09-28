# Arsenal Manager

Interactive CLI manager for [Orange Cyberdefense Arsenal](https://github.com/Orange-Cyberdefense/arsenal)

Arsenal Manager provides a simple terminal interface to manage your personal Arsenal cheatsheets, Arsenal configuration, global variables, TIOCSTI settings and Arsenal installation

The goal is to keep your personal cheats separate from Arsenal's bundled cheats while preserving Arsenal's internal commands and workflow.


<div align="center">
  <img src="https://raw.githubusercontent.com/raphaelthief/arsenal-manager/refs/heads/main/pictures/main.png" alt="Status menu">
</div>


---

## Features

* Create custom Arsenal cheatsheets interactively
* Store personal cheats in `~/.cheats`
* Browse, validate, edit and delete custom cheats
* Validate all custom cheats before using them with Arsenal
* Configure Arsenal to use:

  * only your custom cheats
  * your custom cheats + Arsenal bundled cheats
* Manage Arsenal global variables stored in `~/.arsenal.json`

  * show variables
  * add variables
  * edit variables
  * delete variables
  * clear all variables
* Display Arsenal installation and configuration status
* Backup and restore Arsenal configuration
* Install or update Arsenal through `pipx`
* Configure the Linux TIOCSTI workaround required by Arsenal
* Colorful interactive terminal interface using Rich
* Interactive menus using Questionary

---

## Requirements

* Linux
* Python `>= 3.10`
* `pipx`
* [Arsenal](https://github.com/Orange-Cyberdefense/arsenal)

Arsenal Manager does not install Arsenal through `sudo`.

System-level operations such as modifying the Linux TIOCSTI setting may still require administrator privileges.

---

## Installation

Clone the repository:

```bash
git clone https://github.com/raphaelthief/arsenal-manager.git
cd arsenal-manager
```

Install Arsenal Manager with `pipx`:

```bash
pipx install .
```

The command will then be available as:

```bash
arsenal-manager
or
arscreator
```

Run it:

```bash
arsenal-manager
```

---

## Development installation

For local development, you can also use:

```bash
./run-dev.sh
```

Or execute the package directly:

```bash
python -m arsenal_manager
```

After modifying the source code, reinstall the `pipx` application if you are testing the installed command:

```bash
pipx install --force .
```

---

## Main menu

The interactive interface provides the following actions:

```text
Create a cheat
Manage my cheats
Manage Arsenal variables
Validate cheats
Configure Arsenal cheats
Arsenal status
Restore Arsenal configuration
Install / update Arsenal with pipx
TIOCSTI settings
Exit
```

---

# Custom cheats

Custom cheats are stored in:

```text
~/.cheats
```

Arsenal Manager creates and manages Markdown files in this directory.

A basic custom cheat looks like:

````markdown
# CUSTOM

% fuzzer, fuzz, wfuzz

#plateform/windows #target/local #cat/RECON

## wifi scanner

Scan Wifi with airodump-ng.

```text
sudo airodump-ng <interface>
```
````


The exact tags supported by Arsenal Manager include:

### Platforms

```text
#plateform/linux
#plateform/windows
#plateform/mac
#plateform/multiple
````

### Targets

```text
#target/local
#target/remote
#target/serve
```

### Categories

Examples:

```text
#cat/RECON
#cat/ATTACK
#cat/ATTACK/CONNECT
#cat/CODE
#cat/CRACKING
#cat/PIVOT
#cat/PRIVESC
#cat/POSTEXPLOIT
#cat/PERSIST
```

---

# Creating a cheat

From the main menu:

```text
Create a cheat
```

Arsenal Manager asks for information such as:

* title
* description
* command
* platform
* target
* category
* optional tags

The resulting Markdown file is saved in:

```text
~/.cheats
```

The generated format is compatible with Arsenal's Markdown cheat parser.

<div align="center">
  <img src="https://raw.githubusercontent.com/raphaelthief/arsenal-manager/refs/heads/main/pictures/cheatcreate1.png" alt="Status menu">
</div>

<div align="center">
  <img src="https://raw.githubusercontent.com/raphaelthief/arsenal-manager/refs/heads/main/pictures/cheatcreate2.png" alt="Status menu">
</div>


---

# Managing cheats

Use:

```text
Manage my cheats
```

You can:

* browse your custom cheats
* view the Markdown content
* see whether a cheat is valid
* edit a cheat with `nano`
* delete a cheat

Invalid cheats are clearly marked in the interface.

<div align="center">
  <img src="https://raw.githubusercontent.com/raphaelthief/arsenal-manager/refs/heads/main/pictures/managecheats1.png" alt="Status menu">
</div>   

<div align="center">
  <img src="https://raw.githubusercontent.com/raphaelthief/arsenal-manager/refs/heads/main/pictures/managecheats2.png" alt="Status menu">
</div>   

---

# Validating cheats

Use:

```text
Validate cheats
```

Arsenal Manager checks the Markdown files stored in `~/.cheats`.

The validator checks the required structure and tags, including:

* category
* platform
* target
* command block
* required Markdown structure

Example result:

<div align="center">
  <img src="https://raw.githubusercontent.com/raphaelthief/arsenal-manager/refs/heads/main/pictures/validate.png" alt="Status menu">
</div>  

---

# Arsenal cheat visibility

Arsenal Manager can modify Arsenal's `CHEATS_PATHS` configuration.

## Only my cheats

Arsenal will load only:

```text
~/.cheats
```

This hides Arsenal's bundled cheat collection while keeping Arsenal's internal commands available.

For example:

```text
>set
>show
>clear
>exit
```

remain part of Arsenal's internal command system.

<div align="center">
  <img src="https://raw.githubusercontent.com/raphaelthief/arsenal-manager/refs/heads/main/pictures/setcheats.png" alt="Status menu">
</div>  


## My cheats + Arsenal bundled cheats

Arsenal will load both:

```text
~/.cheats
```

and Arsenal's default cheat directory.

---

# Arsenal global variables

Arsenal stores global variables in:

```text
~/.arsenal.json
```

For example:

```json
{
  "ip": "192.168.1.0/24",
  "interface": "wlan0"
}
```

Arsenal Manager provides a dedicated menu:

```text
Manage Arsenal variables
```

From there you can:

* show variables
* add a variable
* edit a variable
* delete a variable
* clear all variables

This avoids having to manually edit the JSON file.

For example, adding:

```text
ip = 192.168.1.0/24
```

results in:

```json
{
  "ip": "192.168.1.0/24"
}
```

These variables are the same global variables used by Arsenal's commands such as:

```text
>set
>show
>clear
```

<div align="center">
  <img src="https://raw.githubusercontent.com/raphaelthief/arsenal-manager/refs/heads/main/pictures/variables.png" alt="Status menu">
</div>  

---

# Arsenal status

The `Arsenal status` screen provides a quick overview of the current configuration.

Example:

<div align="center">
  <img src="https://raw.githubusercontent.com/raphaelthief/arsenal-manager/refs/heads/main/pictures/status.png" alt="Status menu">
</div>  

---

# Configuration backups

Before modifying Arsenal's configuration, Arsenal Manager can create a backup.

This makes it possible to restore the previous Arsenal configuration if required.

Use:

```text
Restore Arsenal configuration
```

to restore the latest available backup.

---

# TIOCSTI configuration

Some Arsenal functionality requires Linux TIOCSTI support.

Arsenal may display an error similar to:

```text
Arsenal needs TIOCSTI enable for running
```

Arsenal Manager provides a dedicated:

```text
TIOCSTI settings menu.
```


Available actions include:

<div align="center">
  <img src="https://raw.githubusercontent.com/raphaelthief/arsenal-manager/refs/heads/main/pictures/TIOCSTIconf.png" alt="Status menu">
</div>  

The current kernel state and persistent configuration are displayed separately.

The manager's persistent configuration is stored in:

```text
/etc/sysctl.d/99-arsenal-tiocsti.conf
```

System-wide configuration changes may require administrator privileges.

Arsenal Manager does not silently run `sudo`.

---

# Installing / updating Arsenal

Arsenal Manager can install or update Arsenal using `pipx`.

From the menu:

```text
Install / update Arsenal with pipx
```

The equivalent command is:

```bash
pipx install --force arsenal-cli
```

The manager does not install Arsenal using:

```bash
sudo pip
```

or modify the system Python environment.

---

# Configuration files

Arsenal Manager interacts with the following locations:

| Path                                    | Purpose                       |
| --------------------------------------- | ----------------------------- |
| `~/.cheats`                             | Personal Arsenal cheatsheets  |
| `~/.arsenal.json`                       | Arsenal global variables      |
| Arsenal `config.py`                     | Arsenal configuration         |
| `/etc/sysctl.d/99-arsenal-tiocsti.conf` | Persistent TIOCSTI workaround |

Arsenal's own bundled cheats remain inside the Arsenal installation and are not copied into `~/.cheats`.

---

# Dependencies

Arsenal Manager uses:

* [Typer](https://typer.tiangolo.com/) — CLI framework
* [Rich](https://rich.readthedocs.io/) — terminal UI
* [Questionary](https://questionary.readthedocs.io/) — interactive prompts

---

# Safety and configuration philosophy

Arsenal Manager does not modify Arsenal's bundled cheat files.

Personal cheats are kept separately in:

```text
~/.cheats
```

Arsenal configuration changes are backed up before modification where applicable.

System-level operations are explicit and exposed through dedicated menu actions.

In particular, the TIOCSTI configuration is never silently changed during installation.

---


## Disclaimer

This project is an independent management tool for Arsenal.

Arsenal itself is developed by Orange Cyberdefense:

https://github.com/Orange-Cyberdefense/arsenal
