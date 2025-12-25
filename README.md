# POS-Ticket

This is a CLI tool for printing styled tickets to an ESC/POS printer.

Tickets are constructed using Typst with parameters passed in as arguments such
as the title, subtitle, and due-dates.

# Requirements

- Python 3.13+
  - pyusb
  - Pillow
  - qrcode
  - pyserial
  - python-barcode
  - python-escpos
- Typst 14.0+

# Installation

## NixOS

First, add following to your `flake.nix` file:

```nix
inputs.pos-ticket.url = "github:isaacST08/pos-ticket";
```

Then to your `configuration.nix` file (or where ever you would like), add:

```nix
environment.systemPackages = with pkgs; [
  ...
  inputs.pos-ticket.packages.${pkgs.stdenv.hostPlatfrom.system}.default
  ...
];
```

Then save and rebuild your system.

# Usage

## NixOS

If you followed the installation instructions for NixOS above, you will have the
commands `pos-ticket` and `todo` available on your system.

The `todo` command is equivalent to `pos-ticket todo`. That is, the ticket type
parameter has been already applied to give the user a shorter command for
creating "To-Do" tickets.

For more information regarding usage for either command, simply run:

```
pos-ticket -h
```

### First Usage

By using the nix flake, the path to the Typst binary and the path to the Typst
ticket for styling are already applied for you when you use the provided
commands. However, you will still need to supply arguments to tell the program
how to contact your printer (at this time, only network printers are supported),
and what time of printer you have (the profile, more profiles can be found
[here](https://python-escpos.readthedocs.io/en/latest/printer_profiles/available-profiles.html)).

On first run, provide these flags to set these required options:

```
pos-ticket \
    --hostname <HOSTNAME> \
    --port <PORT> \
    --printer-width <PRINTABLE_WIDTH_IN_MM> \
    --profile <PROFILE> \
    --save-config
```

This will set the required values and save them to
`$HOME/.config/pos-ticket/config.json`.

The program will then use these values going forward unless they are set again
(you can set one-time values by omitting the `--save-config` flag).

## Other

For non-NixOS users, once you have installed the dependencies, you can run the
tool with:

```
python3 ./src/main.py <ticket-type> <title> [OPTIONS]
```

### First Usage

On first run, the instructions are the same as for
[NixOS users](#first-usage-0), but with a few extra requirements.

First, you will need to copy the `ticket.typ` file from the root of the repo to
the system config by running:

```
cp ./ticket.typ $HOME/.config/pos-ticket/ticket.typ
```

Alternatively, you can run the program and use the `--ticket-path <PATH>` to set
the ticket path each time.

Additionally, if the `typst` binary is not in your path, then you will need to
provide the `--typst-path <PATH>` each time you use the program.
