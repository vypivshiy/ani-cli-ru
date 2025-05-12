{
  buildPythonApplication,
  fetchPypi,
  hatchling,
  prompt-toolkit,
}:

let
  pname = "eggella";
  version = "0.1.7";
  hash = "sha256-8Vo39BePA86wcLKs/F+u2N7tpIpPrEyEPp3POszy050=";
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
    prompt-toolkit
  ];
}
