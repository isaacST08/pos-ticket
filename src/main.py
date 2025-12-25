from PIL import Image
from argparse import Namespace
from datetime import date
from escpos.escpos import Escpos
from escpos.printer import Network
from pathlib import Path
from xdg import xdg_config_home
import argparse
import io
import json
import subprocess

# **========================================**
# ||          <<<<< SETTINGS >>>>>          ||
# **========================================**


def getConfigDir() -> Path:
    return xdg_config_home() / "pos-ticket"


def getConfigPath() -> Path:
    return getConfigDir() / "config.json"


def updateConfigEntry(conf: dict[str, str | int], key: str, new_val):
    if isinstance(new_val, (str, int)):
        conf[key] = new_val


def loadConfig() -> dict[str, str | int]:
    conf = {}
    try:
        with open(getConfigPath(), "rt") as f:
            j = json.load(f)
            if isinstance(j, dict):
                conf = {
                    k: v
                    for k, v in j.items()
                    if type(k) == str and type(v) in (str, int)
                }
    except:
        pass

    return conf


def storeConfig(conf: dict[str, str | int]):
    # Ensure the config directory exists.
    getConfigDir().mkdir(parents=True, exist_ok=True)

    # Write the configuration to the config file.
    with open(getConfigPath(), "wt") as f:
        _ = f.write(json.dumps(conf, indent=4))


# **========================================**
# ||          <<<<< CLI ARGS >>>>>          ||
# **========================================**


def parseCliArgs() -> Namespace:
    # Load any existing configuration.
    # This will be used for defaults and will be updated if the `--save-config`
    # flag is set.
    conf = loadConfig()

    def addExistingConfigValueHelp(val_name: str, msg: str = "Config value") -> str:
        return f" [{msg}: {conf.get(val_name, '')}]" if val_name in conf.keys() else ""

    parser = argparse.ArgumentParser(
        prog="pos-ticket",
        description="CLI tool for printing tickets to a network attached ESC/POS receipt printer.",
    )

    # --- Positional Args ---
    _ = parser.add_argument(
        "ticket_type",
        help="The type of the ticket. This becomes the big bold title.",
        type=str,
    )
    _ = parser.add_argument(
        "title",
        help="The title of the ticket.",
        type=str,
    )
    _ = parser.add_argument(
        "extra_content",
        default="",
        help="Extra content to add to the ticket.",
        nargs="*",
        type=str,
    )

    # --- Flags ---
    _ = parser.add_argument(
        "-D",
        "--dont-print",
        action="store_false",
        dest="print",
        help="Whether to skip printing the ticket.",
    )
    _ = parser.add_argument(
        "-C",
        "--save-config",
        action="store_true",
        help="Whether to save the provided options to the config file.",
    )

    # --- Options ---
    _ = parser.add_argument(
        "-s",
        "--sub-title",
        default="",
        help="The optional sub-title for the ticket.",
        type=str,
    )
    _ = parser.add_argument(
        "-d",
        "--due-date",
        help="The optional due-date for the ticket. If `--due-time` is set, defaults to today's date.",
        metavar="YYYY-MM-DD",
        type=str,
    )
    _ = parser.add_argument(
        "-t",
        "--due-time",
        help="The optional due-time for the ticket.",
        metavar="HH:MM",
        type=str,
    )
    _ = parser.add_argument(
        "-p",
        "--profile",
        default=conf.get("profile", "default"),
        help="The profile to use for the printer."
        + addExistingConfigValueHelp("profile"),
        type=str,
    )
    _ = parser.add_argument(
        "-H",
        "--hostname",
        default=conf.get("hostname", None),
        help="The hostname of the printer to connect to."
        + addExistingConfigValueHelp("hostname"),
        type=str,
    )
    _ = parser.add_argument(
        "-P",
        "--port",
        default=conf.get("port", 9100),
        help="The port number to use to connect to the printer."
        + addExistingConfigValueHelp("port"),
        type=int,
    )
    _ = parser.add_argument(
        "-w",
        "--printer-width",
        default=conf.get("printer_width", None),
        help="The maximum width that this printer can print in millimeters."
        + addExistingConfigValueHelp("printer_width"),
        type=int,
    )
    _ = parser.add_argument(
        "-T",
        "--typst-path",
        default="typst",
        help="The path to the typst binary. [Default: `typst`]",
        type=str,
    )
    _ = parser.add_argument(
        "-k",
        "--ticket-path",
        default=conf.get("ticket_path", getConfigDir() / "ticket.typ"),
        help="The path to the typst file to use to format the ticket."
        + addExistingConfigValueHelp("ticket_path"),
        type=str,
    )

    # ----- Parse Args -----
    args = parser.parse_args()

    # If the due time was set but the due date wasn't, set the due date to
    # today's date.
    if args.due_time and not args.due_date:
        args.due_date = date.today().isoformat()

    # ----- Save the args if requested -----
    if args.save_config:
        updateConfigEntry(conf, "profile", args.profile)
        updateConfigEntry(conf, "hostname", args.hostname)
        updateConfigEntry(conf, "port", args.port)
        updateConfigEntry(conf, "printer_width", args.printer_width)
        updateConfigEntry(conf, "ticket_path", args.ticket_path)

        storeConfig(conf)

    return args


# **=================================================**
# ||          <<<<< UTILITY FUNCTIONS >>>>>          ||
# **=================================================**


def getDictEntry(d, keys, default):
    # If the keys is a list, get the next key from it.
    if isinstance(keys, list):
        # If only one key is in the list, we have reached the end: Return the
        # value of that key of the current dictionary.
        if len(keys) == 1:
            return d.get(keys[0], default)
        # If there are multiple keys in the key list, get the dictionary nested
        # at that key and recurs.
        elif len(keys) >= 2 and keys[0] in d.keys():
            return getDictEntry(d[keys[0]], keys[1:], default)
        return default

    # If the keys is just one key, use that as the dictionary key and return
    # the result.
    else:
        return d.get(keys, default)


def setDictEntry(d, keys, value):
    if isinstance(keys, list):
        if len(keys) == 1:
            d[keys[0]] = value
        elif len(keys) >= 2:
            if keys[0] not in d.keys() or not isinstance(d[keys[0]], dict):
                d[keys[0]] = {}
            setDictEntry(d[keys[0]], keys[1:], value)
    else:
        d[keys] = value


def scaleImageToPrinterWidth(p: Escpos, img_src: str | bytes, fit_scale: float = 1.0):
    # Get the image from the source.
    img = Image.open(io.BytesIO(img_src) if type(img_src) == bytes else img_src)

    # Calculate the scale required to have the image fit the paper.
    scale = min(max(fit_scale, 0.001), 1.0)
    try:
        p_data = p.profile.profile_data
        scale *= int(getDictEntry(p_data, ["media", "width", "pixels"], 500))
        scale /= img.width
    except:
        pass

    # Return the scaled image.
    return img.resize((round(img.width * scale), round(img.height * scale)))


# **====================================================**
# ||          <<<<< PRINTER CONSTRUCTORS >>>>>          ||
# **====================================================**


def generateNetworkPrinter(args: Namespace) -> Escpos:
    printer = Network(
        host=args.hostname,
        port=args.port,
        profile=args.profile,
    )

    # Set the printers width.
    if args.printer_width:
        # Set the printers millimeter width.
        setDictEntry(
            printer.profile.profile_data, ["media", "width", "mm"], args.printer_width
        )

        # Get the printers dpi.
        printer_dpi = getDictEntry(printer.profile.profile_data, ["media", "dpi"], None)

        # Set the printers pixel width.
        if printer_dpi is not None:
            setDictEntry(
                printer.profile.profile_data,
                ["media", "width", "pixels"],
                printer_dpi * args.printer_width / 25.4,
            )

    # Set the printer to default print settings.
    printer.set_with_default()
    printer.line_spacing()

    return printer


# **=============================================**
# ||          <<<<< TYPST TICKETS >>>>>          ||
# **=============================================**


def typstCompile(
    source_path: str,
    format: str,
    ppi: int,
    sys_inputs: dict[str, str],
    typst_bin_path: str = "typst",
) -> bytes:
    # Construct the args for compiling the Typst document.
    args = [
        typst_bin_path,
        "compile",
        source_path,
        f"--ppi={ppi}",
        f"--format={format}",
    ]
    for key, val in sys_inputs.items():
        args.append("--input")
        args.append(f"{key}={val}")
    args.append("-")  # PNG to STDOUT.

    # Compile the Typst doc PNG.
    typst_result = subprocess.run(args, capture_output=True)

    # Return the bytes of the Typst doc PNG.
    return typst_result.stdout


def printTypstTicket(
    printer: Escpos,
    ticket_type: str,
    title: str | None = None,
    sub_title: str | None = None,
    due_date_str: str | None = None,
    due_time_str: str | None = None,
    extra_content: str | None = None,
    typst_bin_path: str = "typst",
    ticket_path: str = "./ticket.typ",
):
    # Create the default sys input for typst with just the ticket type.
    sys_inputs = {
        "ticket_type": ticket_type,
    }

    # Add all non-none values to the sys inputs.
    if title:
        sys_inputs["title"] = title
    if sub_title:
        sys_inputs["sub_title"] = sub_title
    if due_date_str:
        sys_inputs["due_date_str"] = due_date_str
    if due_time_str:
        sys_inputs["due_time_str"] = due_time_str
    if extra_content:
        sys_inputs["extra_content"] = extra_content

    ppi = 500
    try:
        ppi = int(
            getDictEntry(
                printer.profile.profile_data, ["media", "width", "pixels"], 250
            )
        )
        ppi *= 2
    except:
        pass

    # Compile the typst ticket.
    png_bytes = typstCompile(
        ticket_path,
        format="png",
        ppi=ppi,
        sys_inputs=sys_inputs,
        typst_bin_path=typst_bin_path,
    )

    # Convert the Typst PNG bytes to an image that is scaled to the width of
    # the printer.
    typst_png = scaleImageToPrinterWidth(printer, png_bytes)

    # Print the image to the printer.
    printer.image(typst_png, center=True)
    printer.line_spacing(0)
    printer.ln()
    printer.cut()
    printer.line_spacing()


# **====================================**
# ||          <<<<< MAIN >>>>>          ||
# **====================================**


def main():
    args = parseCliArgs()

    printer = generateNetworkPrinter(args)

    # Print the ticket.
    if args.print:
        printTypstTicket(
            printer,
            args.ticket_type,
            title=args.title,
            sub_title=args.sub_title,
            due_date_str=args.due_date,
            due_time_str=args.due_time,
            extra_content=(
                " ".join(args.extra_content)
                if type(args.extra_content) == list
                else args.extra_content
            ),
            typst_bin_path=args.typst_path,
            ticket_path=args.ticket_path,
        )


if __name__ == "__main__":
    main()
