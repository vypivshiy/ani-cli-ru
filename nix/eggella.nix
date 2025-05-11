{
  pkgs,
  pyPkgs,
  #
  version ? null,
  hash ? null,
}:

with pyPkgs;

buildPythonApplication rec {
  pname = "eggella";
  inherit version;
  pyproject = true;

  src = pkgs.fetchPypi {
    inherit
      pname
      version
      hash
      ;
  };

  build-system = [
    setuptools
    hatchling
  ];

  dependencies = [
    prompt-toolkit
  ];
}
