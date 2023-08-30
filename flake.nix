{
  description = "Description for the project";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    poetry-overrides = {
      url = "github:emanueljg/poetry-overrides";
      # debug url
      # url = "path:/home/ejg/poetry-overrides";
    };
  };

  outputs = inputs @ {flake-parts, ...}:
    flake-parts.lib.mkFlake {inherit inputs;} {
      imports = [
      ];

      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "aarch64-darwin"
        "x86_64-darwin"
      ];

      perSystem = {
        config,
        self',
        inputs',
        pkgs,
        system,
        ...
      }:
        with pkgs; let
          poetryBase = {
            projectDir = ./.;
            python = python311;
            overrides = callPackage inputs.poetry-overrides.overrides {};
          };
        in {
          packages = rec {
            default = PACKAGE_NAME;
            PACKAGE_NAME =
              pkgs.poetry2nix.mkPoetryApplication
              (poetryBase // {checkGroups = [];});
          };
          devShells = rec {
            default = PACKAGE_NAME;
            PACKAGE_NAME = (pkgs.poetry2nix.mkPoetryEnv poetryBase).env;
          };
          formatter = pkgs.alejandra;
        };

      flake = {
      };
    };
}
