{
  description = ''
    Tool for watching anime from popular russian sources
    ! Only in TUI mode !
  '';

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    let
      supportedSystems = [ "x86_64-linux" "aarch64-linux" ];
    in
    flake-utils.lib.eachSystem supportedSystems (system:
      let
        pkgs = import nixpkgs { 
          inherit system;
        };
      in
      {
        packages = {
          anicli-ru = pkgs.callPackage ./nix/package.nix { };
          default = self.packages.${system}.anicli-ru;
        };
        
        devShells = {
          default = pkgs.mkShell {
            buildInputs = [ self.packages.${system}.default ];
          };
        };
        
        overlays = final: prev: {
          anicli-ru = self.packages.${system}.anicli-ru;
          default = self.packages.${system}.anicli-ru;
        };
      }
    );
}
