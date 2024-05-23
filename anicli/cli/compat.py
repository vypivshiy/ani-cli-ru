import sys

if sys.version_info >= (3, 11):
    import tomllib
else:
    import toml as tomllib

__all__ = ["tomllib"]
