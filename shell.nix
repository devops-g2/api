{ pkgs ? import <nixpkgs> { }
, inputsFrom ? [ ]
}: pkgs.mkShell { inherit inputsFrom; }
