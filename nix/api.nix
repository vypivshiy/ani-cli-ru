{
  buildPythonApplication,
  fetchPypi,
  attrs,
  hatchling,
  httpx,
  parsel,
  #
  version ? null,
  hash ? null,
}:

buildPythonApplication rec {
  pname = "anicli_api";
  inherit version;
  pyproject = true;
  dontCheckRuntimeDeps = true;

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
    attrs
    httpx
    httpx.optional-dependencies.http2
    parsel
  ];
}
