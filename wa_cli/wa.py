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
"""
The entrypoint for the Wisconsin Autonomous CLI tool is `wa`.
The main parser will have a few options, such as verbosity or a help menu.
For the most part, the entrypoint will be used to access subparsers,
where each subparser implements it's own unique logic. Examples of
subparsers may be `sim` to do things related to `wa_simulator`, or
`script` to run helper scripts such as our license tool or code styling.
"""
# Command imports
import wa_cli.script as script
import wa_cli.sim as sim

# Utility imports
from wa_cli.utils.logger import set_verbosity

# General imports
import argparse


def main():
    # Main entrypoint and initialize the cmd method
    # set_defaults specifies a method that is called if that parser is used
    parser = argparse.ArgumentParser(description="Wisconsin Autonomous Command Line Interface") # noqa
    parser.add_argument('-v', '--verbose', dest='verbosity', action='count', help='Level of verbosity', default=0) # noqa
    parser.add_argument('--dry-run', action="store_true", help="Run as a dry run")
    parser.set_defaults(cmd=lambda x: x)

    # Initialize the subparsers
    subparsers = parser.add_subparsers()
    script.init(subparsers.add_parser("script", description="Entrypoint for various generic scripts useful to Wisconsin Autonomous members"))
    sim.init(subparsers.add_parser("sim", description="Entrypoint for WA simulator related commands"))

    # Parse the arguments and update logging
    args = parser.parse_args()
    set_verbosity(args.verbosity)

    # Calls the cmd for the used subparser
    args.cmd(args)

