"""A collection of values for other modules to use.

If you wish to use a different source of data, this is the place to modify.

"""

import os
import importlib.util
import importlib.resources
from pathlib import Path

from typing import List, Optional, Generator, BinaryIO, Union

BASE_PATH_ENVIRONMENT_VAR: str = "FUZZDB_DIR"
BASE_PATH: Optional[Path] = None

__all__ = ["get_strings", "get_integers", "get_floats"]


def _get_fuzzdb_path() -> Path:
    """Configure the base path for fuzzdb file imports.

    fuzzdb is not a python module, so we cannot maximize the functionality
    of importlib to scan and import all of the files as resources. We instead
    find the first, most likely working path of fuzzdb based on the package
    structure provided by importlib, then provide the absolute path to
    that location.

    If FUZZDB_DIR is set in the environment, this method prioritizes searching
    for it first.

    If BASE_PATH has been set (is not None), this immediately
    returns as it has been already set by other code in this module.

    Arguments: None
    Returns: absolute path to fuzzdb/attack resource directory
    """
    global BASE_PATH
    # Once BASE_PATH is set we do not want to change it so this is a no-op.
    if BASE_PATH:
        return BASE_PATH
    package_name = "protofuzz"
    module_name = "fuzzdb"
    search_paths: List[Path] = []
    fuzzdb_path: Optional[Path] = None
    # We prioritize checking the env variable over the project recursive
    # copy of fuzzdb as the env being set implies the user wants that
    # location.
    if BASE_PATH_ENVIRONMENT_VAR in os.environ:
        search_paths.append(Path(os.environ[BASE_PATH_ENVIRONMENT_VAR]))
    # We convert this to a Path as it will be easier to traverse in other
    # methods, Path only accepts strings/bytes
    module_path = Path(
        str(importlib.resources.files(package_name).joinpath(module_name))
    )
    search_paths.append(module_path)
    for module_path in search_paths:
        attack_path = module_path / Path("attack")
        # Use the 1st directory we find that exists and seems like a fuzzdb dir
        if os.path.exists(attack_path):
            fuzzdb_path = attack_path
            break
    if not fuzzdb_path:
        raise RuntimeError("Could not import fuzzdb dependency files.")
    BASE_PATH = fuzzdb_path
    return fuzzdb_path


def _limit_helper(stream: Union[BinaryIO, Generator, List], limit: int) -> Generator:
    """Limit a stream depending on the "limit" parameter."""
    for value in stream:
        yield value
        if limit == 1:
            return
        else:
            limit = limit - 1  # FIXME


def _fuzzdb_integers(limit: int = 0) -> Generator:
    """Return integers from fuzzdb."""
    path = _get_fuzzdb_path() / Path("integer-overflow/integer-overflows.txt")
    with open(path, "rb") as stream:
        for line in _limit_helper(stream, limit):
            yield int(line.decode("utf-8"), 0)


def _fuzzdb_get_strings(max_len: int = 0) -> Generator:
    """Return strings from fuzzdb."""
    ignored = ["integer-overflow"]
    for subdir in os.listdir(_get_fuzzdb_path()):
        if subdir in ignored:
            continue
        subdir_abs_path = _get_fuzzdb_path() / Path(subdir)
        try:
            listing = os.listdir(subdir_abs_path)
        except NotADirectoryError:
            continue
        for filename in listing:
            if not filename.endswith(".txt"):
                continue
            subdir_abs_path_filename = subdir_abs_path / Path(filename)
            with open(subdir_abs_path_filename, "rb") as source:
                for line in source:
                    string = line.decode("utf-8").strip()
                    if not string or string.startswith("#"):
                        continue
                    if max_len != 0 and len(line) > max_len:
                        continue

                    yield string


def get_strings(max_len: int = 0, limit: int = 0) -> Generator:
    """Return strings from fuzzdb.

    limit - Limit results to |limit| results, or 0 for unlimited.
    max_len - Maximum length of string required.

    """
    return _limit_helper(_fuzzdb_get_strings(max_len), limit)


def get_integers(bitwidth: int, unsigned: bool, limit: int = 0) -> Generator:
    """Return integers from fuzzdb database.

    bitwidth - The bitwidth that has to contain the integer
    unsigned - Whether the type is unsigned
    limit - Limit to |limit| results.

    """
    if unsigned:
        start, stop = 0, ((1 << bitwidth) - 1)
    else:
        start, stop = (-(1 << bitwidth - 1)), (1 << (bitwidth - 1) - 1)

    for num in _fuzzdb_integers(limit):
        if num >= start and num <= stop:
            yield num


def get_floats(bitwidth: int, limit: int = 0) -> Generator:
    """Return a number of interesting floating point values."""
    assert bitwidth in (32, 64, 80)
    values = [0.0, -1.0, 1.0, -1231231231231.0123, 123123123123123.123]
    for val in _limit_helper(values, limit):
        yield val
