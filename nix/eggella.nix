{
  buildPythonApplication,
  fetchPypi,
  hatchling,
  prompt-toolkit,
  #
  version ? null,
  hash ? null,
}:

buildPythonApplication rec {
  pname = "eggella";
  inherit version;
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
