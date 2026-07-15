{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs = {
        nixpkgs.follows = "nixpkgs";
        pyproject-nix.follows = "pyproject-nix";
      };
    };
    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs = {
        pyproject-nix.follows = "pyproject-nix";
        uv2nix.follows = "uv2nix";
        nixpkgs.follows = "nixpkgs";
      };
    };
  };
  outputs =
    {
      self,
      nixpkgs,
      pyproject-nix,
      uv2nix,
      pyproject-build-systems,
    }:
    let
      forEachSystem =
        f:
        nixpkgs.lib.genAttrs nixpkgs.lib.systems.doubles.all (
          system:
          f (
            import nixpkgs {
              inherit system;
            }
          )
        );
    in
    {
      packages = forEachSystem (pkgs: {
        default =
          let
            workspace = uv2nix.lib.workspace.loadWorkspace {
              workspaceRoot = ./.;
            };
            overlay = workspace.mkPyprojectOverlay {
              sourcePreference = "wheel";
            };
            pythonSet =
              (pkgs.callPackage pyproject-nix.build.packages { python = pkgs.python312; }).overrideScope
                (
                  pkgs.lib.composeManyExtensions [
                    pyproject-build-systems.overlays.default
                    overlay
                  ]
                );
            anicliPkg = pythonSet.anicli-ru;
            venv = pythonSet.mkVirtualEnv "anicli-ru-env" (
              workspace.deps.default // { anicli-ru = [ "all" ]; }
            );
          in
          pkgs.symlinkJoin {
            name = "anicli-ru-${anicliPkg.version or "latest"}";
            paths = [ venv ];
            nativeBuildInputs = [ pkgs.makeWrapper ];
            postBuild = ''
              rm $out/bin/anicli-ru
              makeWrapper ${venv}/bin/anicli-ru $out/bin/anicli-ru \
                --prefix PATH : ${
                  pkgs.lib.makeBinPath [
                    pkgs.mpv
                    pkgs.ffmpeg-full
                  ]
                }
            '';
          };
      });
    };
}
