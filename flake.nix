{
  description = ''
    Tool for watching anime from popular russian sources
    ! Only in TUI mode !
  '';

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    inputs:
    inputs.flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import inputs.nixpkgs {
          inherit
            system
            ;
        };
      in
      rec {
        packages = {
          anicli-ru = pkgs.callPackage ./nix/package.nix { };
          default = packages.anicli-ru;
        };
        devShells = {
          default = pkgs.mkShell {
            buildInputs = [ packages.default ];
          };
        };
        overlays = {
          default = final: prev: {
            anicli-ru = packages.default;
          };
        };
      }
    );
}
