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


def load_json(filename: str) -> dict:
    """Load a json file

    Will simply use the `json library <https://docs.python.org/3/library/json.html>` and return the
    loaded dictionary.

    Args:
        filename (str): The file to load

    Returns:
        dict: The loaded json file contents in a dictionary form.
    """
    import json

    with open(filename) as f:
        j = json.load(f)

    return j

def check_field(j: dict, field: str, value=None, field_type=None, allowed_values: list = None, optional: bool = False):
    """Check a field in a dict loaded from json

    Args:
        j (dict): The dictionary loaded via a json file
        field (str): The field to check
        value (Any, optional): Some value field must be
        field_type (Type, optional): The type the field must be
        allowed_values: The allowed values
        optional (bool, optional): Whether the field is optional

    Raises:
        KeyError: If the field is not in j
        ValueError: If the value of j[field] does not equal some value
        TypeError: If the type of j[field] is not the same as field_type
        ValueError: j[field] is not one of the allowed_values
    """

    if field not in j:
        if optional:
            return

        raise KeyError(f"_check_field: '{field}' is not in the passed json")

    if value is not None and j[field] != value:
        raise ValueError(
            f"_check_field: was expecting '{value}' for '{field}', but got '{j[field]}'.")

    if field_type is not None and not isinstance(j[field], field_type):
        raise TypeError(
            f"_check_field: was expecting '{field}' to be '{field_type}', but was '{type(j[field])}'.")

    if allowed_values is not None:
        _check_field_allowed_values(j, field, allowed_values)
