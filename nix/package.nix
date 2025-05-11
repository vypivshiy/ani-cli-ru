{
  pkgs,
  lib,
}:

# watch anime in terminal (cli)
# only russian sources

let
  pyPkgs = pkgs.python312Packages;
in
with pyPkgs;

let
    pname = "anicli_ru";
    version = "5.0.16";
in

buildPythonApplication {
  inherit pname version;
  pyproject = true;

  src = pkgs.fetchPypi {
    inherit pname version;
    hash = "sha256-gM9on15RQIpQVJfWW/uPeN63vSSbCJt2mNN5zkvc5Jg=";
  };

  build-system = [
    setuptools
    hatchling
  ];

  dependencies = [
    pkgs.mpv
    hatchling
    setuptools
    (callPackage ./eggella.nix {
      inherit pyPkgs;
      version = "0.1.7";
      hash = "sha256-8Vo39BePA86wcLKs/F+u2N7tpIpPrEyEPp3POszy050=";
    })
    (callPackage ./api.nix {
      inherit pyPkgs;
      version = "0.7.14";
      hash = "sha256-zmB2U4jyDPCLuykUc6PyrlcTULaXDxQ8ZvyTmJfOI0s=";
    })
  ];

  meta = with lib; {
    description = ''
      Watch anime in terminal (tui)
      ! only russian sources !
    '';
    homepage = "https://github.com/vypivshiy/ani-cli-ru";
    license = licenses.afl3;
    platforms = platforms.linux;
    maintainers = with maintainers; [
      DADA30000
      {
        name = "Azik Kurbonov";
        email = "xfalwa@gmail.com";
        github = "mctrxnv";
        githubId = 189107707;
      }
      ch4og
    ];
    mainProgram = "anicli-ru";
  };
}
