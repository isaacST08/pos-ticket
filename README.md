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
