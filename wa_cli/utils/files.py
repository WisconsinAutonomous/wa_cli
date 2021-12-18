#
# MIT License
#
# Copyright (c) 2018-2021 Wisconsin Autonomous
#
# See https://wa.wisc.edu
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

# Import some utils
from wa_cli.utils.logger import LOGGER

# External library imports
from pathlib import Path
from typing import Union


def file_exists(filename: str, throw_error: bool = False) -> bool:
    """
    Check if the passed filename is an actual file

    Args:
        filename (str): The filename to check
        throw_error (bool): If True, will throw an error if the file doesn't exist. Defaults to False.

    Returns:
        bool: True if the file exists, false otherwise

    Throws:
        FileNotFoundError: If filename is not a file and throw_error is set to true    
    """
    is_file = Path(filename).is_file()
    if throw_error and not is_file:
        raise FileNotFoundError(f"{filename} is not a file.")
    return is_file


def get_resolved_path(path, wa_cli_relative: bool = False, return_as_str: bool = True) -> Union[str, Path]:
    """
    Get the fully resolved path to a specific file. If ``wa_cli_relative`` is set to true,
    the desired filename is relative to the ``wa_cli`` root subdirectory.

    Args:
        path (str): The path to get a fully resolved path from
        wa_cli_relative (bool): Whether the filepath is relative to the wa_cli subfolder. Defaults to False.
        return_as_str (bool): Returns the path as a string. Otherwise will return as a pathlib.Path object. Defaults to True

    Returns:
        Union[str, Path]: The fully resolved path as a string or Path object
    """
    path = Path(path)
    if wa_cli_relative:
        from wa_cli import __file__ as wa_cli_file
        path = Path(wa_cli_file).parent / path

    resolved_path = path.resolve()
    if return_as_str:
        return str(resolved_path)
    else:
        return resolved_path
