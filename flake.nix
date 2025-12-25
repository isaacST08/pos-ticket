{
  description = "CLI utility for printing tickets to a ESC/POS printer.";

  # Latest stable Nixpkgs.
  inputs.nixpkgs.url = "https://flakehub.com/f/NixOS/nixpkgs/0";

  outputs = {nixpkgs, ...}: let
    lib = nixpkgs.lib;

    # **=======================================**
    # ||          <<<<< OPTIONS >>>>>          ||
    # **=======================================**

    pname = "pos-ticket";
    version = "0.1.0";
    pythonPkgName = "python313";
    meta = {
      description = "CLI utility for printing tickets to a ESC/POS printer.";
    };

    # Systems supported.
    allSystems = [
      "x86_64-linux" # 64-bit Intel/AMD Linux
      "aarch64-linux" # 64-bit ARM Linux
      "x86_64-darwin" # 64-bit Intel macOS
      "aarch64-darwin" # 64-bit ARM macOS
    ];

    # **=======================================**
    # ||          <<<<< HELPERS >>>>>          ||
    # **=======================================**

    # Helper to provide system-specific attributes.
    forAllSystems = f:
      nixpkgs.lib.genAttrs allSystems (
        system:
          f {
            pkgs = import nixpkgs {inherit system;};
          }
      );

    # **============================================**
    # ||          <<<<< REQUIREMENTS >>>>>          ||
    # **============================================**

    requiredPythonPackages = pyPkgs:
      with pyPkgs; [
        python-escpos
        pyusb
        pillow
        qrcode
        pyserial
        python-barcode
        xdg
      ];

    requiredSystemPackages = pkgs:
      with pkgs; [
        typst
      ];
  in {
    packages = forAllSystems (
      {pkgs, ...}: let
        pyPkgs = pkgs.${pythonPkgName}.pkgs;

        # ----- PYTHON PACKAGE -----
        pythonPackage = pyPkgs.buildPythonPackage {
          inherit pname version meta;

          pyproject = true;
          build-system = with pyPkgs; [setuptools];

          src = ./src;

          buildInputs = with pyPkgs; [setuptools wheel];
          propagatedBuildInputs = requiredPythonPackages pyPkgs;
          dependencies = requiredSystemPackages pkgs;
        };

        pythonEnv = pkgs.${pythonPkgName}.buildEnv.override {
          extraLibs = [pythonPackage];
        };
      in {
        default = pkgs.stdenv.mkDerivation rec {
          inherit pname version meta;

          propagatedBuildInputs = [pythonEnv];

          src = ./.;

          installPhase = let
            mkPythonBin = name: args:
            # sh
            ''
              cat > $out/bin/${name} <<EOF
              #!/bin/sh
              exec ${pythonEnv}/bin/python3 ${src}/src/main.py -T "${lib.getExe pkgs.typst}" ${builtins.concatStringsSep " " args} "\$@"
              EOF
              chmod +x $out/bin/${name}
            '';
          in
            # sh
            ''
              mkdir -p $out/bin
              ${mkPythonBin pname []}
              ${mkPythonBin "todo" ["Todo"]}
            '';
        };
      }
    );

    devShells = forAllSystems (
      {pkgs, ...}: let
        python = pkgs.${pythonPkgName}.override {
          self = python;
        };
      in {
        default = pkgs.mkShell {
          packages = (
            (requiredSystemPackages pkgs)
            ++ [(python.withPackages (python-pkgs: requiredPythonPackages python-pkgs))]
          );
        };
      }
    );
  };
}
