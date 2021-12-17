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

def check_for_dependency(package: str, install_method: str = None, raises_error: bool = False) -> bool:
    """
    Checks if a dependency is installed

    Args:
        package (str): The package to check for
        install_method (str): The install method. Ex: 'pip install <package'. Used in the error message.
        raises_error (bool): Whether to raise an error if the module does not exist.

    Return:
        bool: whether the dependency is present

    Raises:
        ModuleNotFoundError: If the module wasn't found
    """
    import importlib

    is_present = False
    try:
        importlib.import_module(package)
        is_present = True
    except ModuleNotFoundError as e:
        msg = f"Please install the {package} package."
        if install_method is not None:
            msg += f" Can be done with '{install_method}'."
        LOGGER.warn(msg)
        if raises_error:
            raise e
        else:
            exit()

    return is_present
