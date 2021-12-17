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
import logging

# Create logger
LOGGER = logging.getLogger(__name__)

# Create a handler with the desired format
DEFAULT_LOGGING_FORMAT = '%(levelname)-8s :: %(module)s.%(funcName)-10s :: %(message)s'
CONSOLE_HANDLER = logging.StreamHandler()
CONSOLE_HANDLER.setFormatter(logging.Formatter(fmt=DEFAULT_LOGGING_FORMAT))

# Set default logging levels
DEFAULT_LOGGING_LEVEL = logging.WARNING
CONSOLE_HANDLER.setLevel(logging.WARNING)
LOGGER.setLevel(DEFAULT_LOGGING_LEVEL)

# Add the handler to the logger
LOGGER.addHandler(CONSOLE_HANDLER)


def set_verbosity(verbosity: int):
    """
    Set the verbosity level for the logger.
    Default verbosity is WARNING. ``verbosity`` should be a value
    greater than 0 and less than 2 that represents how many levels below WARNING is desired.
    For instance, if ``verbosity`` is 1, the new level will be INFO because
    that is one below WARNING. If ``verbosity`` is 2, the new level is DEBUG.
    DEBUG and INFO are currently the only two implemented

    Args:
        verbosity (int): A value between 0 and 2 that represents the number of levels below WARNING that should be used when logging.
    """

    if verbosity < 0 or verbosity > 2:
        raise ValueError(
            f"Verbosity should be greater than 0 and less than 2. Got {verbosity}.")

    level = logging.WARNING - verbosity * 10
    LOGGER.setLevel(level)
    CONSOLE_HANDLER.setLevel(level)
    print(f"Verbosity has been set to {logging.getLevelName(level)}")
