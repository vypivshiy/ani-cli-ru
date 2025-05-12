{
  lib,
  buildPythonApplication,
  callPackage,
  fetchPypi,
  hatchling,
  mpv,
  tqdm,
}:

let
  pname = "anicli_ru";
  version = "5.0.16";
  hash = "sha256-gM9on15RQIpQVJfWW/uPeN63vSSbCJt2mNN5zkvc5Jg=";
in

buildPythonApplication {
  inherit
    pname
    version
    ;
  pyproject = true;

  src = fetchPypi {
    inherit
      pname
      version
      hash
      ;
  };

  build-system = [
    hatchling
  ];

  dependencies = [
    mpv
    tqdm
    (callPackage ./eggella.nix { })
    (callPackage ./api.nix { })
  ];

  meta = with lib; {
    description = ''
      Watch anime in terminal (tui)
      ! only russian sources !
    '';
    homepage = "https://github.com/vypivshiy/ani-cli-ru";
    license = licenses.gpl3Plus;
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
