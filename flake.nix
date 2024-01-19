{
  description = "Description for the project";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-23.11";
    pre-commit-hooks = {
      url = "github:cachix/pre-commit-hooks.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = inputs @ { flake-parts, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      imports = [
      ];

      systems = import ./nix/systems.nix;

      perSystem =
        { self'
        , pkgs
        , system
        , ...
        }:
        let
          poetryBase = {
            projectDir = ./.;
            python = pkgs.python311;
            preferWheels = true;
          };
          pre-commit = import ./nix/pre-commit.nix { inherit pkgs inputs system self'; };
          poetry2nix = inputs.poetry2nix.lib.mkPoetry2Nix { inherit pkgs; };
        in
        {
          packages.default = poetry2nix.mkPoetryApplication
            (poetryBase // { checkGroups = [ ]; });
          checks.pre-commit = pre-commit.checks.pre-commit-check;
          devShells.default = pkgs.callPackage ./shell.nix {
            inputsFrom = [
              (poetry2nix.mkPoetryEnv poetryBase).env
              pre-commit.devShells.default
            ];
          };
          formatter = pkgs.nixpkgs-fmt;
        };

      flake = { };
    };
}
