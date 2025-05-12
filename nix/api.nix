{
  buildPythonApplication,
  fetchPypi,
  attrs,
  hatchling,
  httpx,
  parsel,
}:

let
  pname = "anicli_api";
  version = "0.7.14";
  hash = "sha256-zmB2U4jyDPCLuykUc6PyrlcTULaXDxQ8ZvyTmJfOI0s=";
in

buildPythonApplication {
  inherit
    pname
    version
    ;
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
