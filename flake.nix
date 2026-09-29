{
  description = "Flake using pyproject.toml metadata";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";
    pyproject-nix.url = "github:pyproject-nix/pyproject.nix";
    pyproject-nix.inputs.nixpkgs.follows = "nixpkgs";
  };
  outputs = inputs @ {flake-parts, ...}: let
    project = inputs.pyproject-nix.lib.project.loadPyproject {
      projectRoot = ./.;
    };

    pythonAttr = "python314";
  in
    flake-parts.lib.mkFlake {inherit inputs;} {
      imports = [];
      systems = ["x86_64-linux" "aarch64-linux" "aarch64-darwin"];

      perSystem = {
        pkgs,
        self',
        ...
      }: let
        python = pkgs.${pythonAttr};
        pythonEnv = python.withPackages (project.renderers.withPackages {inherit python;});

        appAttrs = project.renderers.buildPythonPackage {
          inherit python;
        };
        sphinxTotal = python.withPackages (python-pkgs:
          with python-pkgs; [
            sphinx
            sphinx-rtd-theme
            sphinx-autodoc-typehints # not used
            sphinx-autobuild
          ]);
      in {
        devShells.default = pkgs.mkShell {
          packages = [
            pkgs.python314Packages.mypy
            pythonEnv
            pkgs.just
            pkgs.gnumake
            pkgs.uv
            sphinxTotal
          ];
          shellHook = ''
            export INCLUDE_TODOS=""
            export BAST3ST_ADMIN_SERVER="http://localhost:42039/"
          '';
        };
        devShells.full = pkgs.mkShell {
          packages = [
            pythonEnv
            self'.packages.bast3st-full
            pkgs.just
            pkgs.gnumake
            pkgs.uv
            sphinxTotal
          ];
          shellHook = ''
            export INCLUDE_TODOS=""
          '';
        };

        formatter = pkgs.alejandra;

        packages = let
          python = pkgs.${pythonAttr};
        in {
          bast3st-lib = python.pkgs.buildPythonPackage ({
              pythonImportsCheck = ["bast3st"];
            }
            // project.renderers.buildPythonPackage {
              inherit python;
            });

          default = self'.packages.bast3st-full;

          bast3st-only-app = python.pkgs.buildPythonApplication (appAttrs
            // {
              pname = project.pyproject.project.name;
              version = project.pyproject.project.version;

              src = ./.;

              pyproject = true;

              pythonImportsCheck = ["bast3st"];

              build-system = with python.pkgs; [
                setuptools
                wheel
              ];
            });

          docs = pkgs.stdenv.mkDerivation {
            pname = "${project.pyproject.project.name}-html-docs";
            version = project.pyproject.project.version;

            src = ./.;

            nativeBuildInputs = [
              pythonEnv
              sphinxTotal
              pkgs.gnumake
            ];

            buildPhase = ''
              cd docs
              make html
              mkdir -p $out/share/doc/bast3st
              cp -r build/html $out/share/doc/bast3st
            '';
            installPhase = ''echo "finished"'';
          };

          bast3st-full = pkgs.stdenv.mkDerivation {
            pname = "${project.pyproject.project.name}";
            version = project.pyproject.project.version;

            src = ./src; # not really needed

            buildPhase = ''
              mkdir -p $out/share/doc
              cp -r ${self'.packages.bast3st-lib}/* $out/
              cp -r ${self'.packages.docs}/share/doc/* $out/share/doc/
            '';
            installPhase = '''';
          };

          # man = pkgs.stdenv.mkDerivation {
          #   pname = "bast3st";
          #   version = "0.1.0";

          #   src = ./docs/build/man/bast3st.1;
          #   unpackPhase = ''
          #     mkdir -p $out/share/man/man1
          #     cp $src $out/share/man/man1/bast3st.1
          #   '';

          #   # meta = with pkgs.lib; {
          #   # description = "Bast3St";
          #   # mainProgram = "exename";
          #   # };
          # };
        };
        apps.bast3st = {
          type = "app";
          program = self'.packages.bast3st;
          meta = {
            description = "main 'bast3st' binary";
          };
        };
      };
    };
}
