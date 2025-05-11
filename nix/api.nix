{
  pkgs,
  pyPkgs,
  #
  version ? null,
  hash ? null,
}:

with pyPkgs;

buildPythonApplication rec {
  pname = "anicli_api";
  inherit version;
  pyproject = true;
  dontCheckRuntimeDeps = true;

  src = pkgs.fetchPypi {
    inherit
      pname
      version
      hash
      ;
  };

  build-system = [
    poetry-core
    hatchling
  ];

  dependencies = [
    attrs
    httpx
    httpx.optional-dependencies.http2
    hatchling
    parsel
    tqdm
  ];
}
