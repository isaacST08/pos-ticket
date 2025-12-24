# shell.nix
let
  pkgs = import <nixpkgs> {};

  python = pkgs.python313.override {
    self = python;
  };
in
  pkgs.mkShell {
    packages = (
      (with pkgs; [
        typst
      ])
      ++ [
        (python.withPackages (python-pkgs:
          with python-pkgs; [
            python-escpos
            pyusb
            pillow
            qrcode
            pyserial
            python-barcode
            xdg
          ]))
      ]
    );
  }
