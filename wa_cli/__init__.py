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

import signal
from ._import import _import, _get_dirs, _get_files
from ._version import version as __version__

__author__ = "Wisconsin Autonomous (wisconsinautonomous@studentorg.wisc.edu)"
"""Wisconsin Autonomous (wisconsinautonomous@studentorg.wisc.edu)"""
__license__ = "MIT"
"""MIT"""

for d in _get_dirs(__file__):
    _import(d, globals())

for f in _get_files(__file__):
    _import(f, globals())


def _signal_handler(sig, frame):
    """Signal handler that will exit if ctrl+c is recorded in the terminal window.

    Allows easier exiting of a matplotlib plot

    Args:
        sig (int): Signal number
        frame (int): ?
    """

    import sys
    sys.exit(0)


# setup the signal listener to listen for the interrupt signal (ctrl+c)
signal.signal(signal.SIGINT, _signal_handler)

del _import, _get_dirs, _get_files, signal
