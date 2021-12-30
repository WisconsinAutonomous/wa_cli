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
CLI command that handles running various scripts for Wisconsin Autonomous members
"""

# Imports from wa_cli
from wa_cli.utils.logger import LOGGER
from wa_cli.utils.files import get_resolved_path
from wa_cli.utils.dependencies import check_for_dependency


def run_license(args):
    """The license command will automatically place headers at the top of each requested file.

    """
    LOGGER.debug("Running 'script license' entrypoint...")

    # Don't want to have install everything when wa_cli is installed
    # So check dependencies here
    LOGGER.info("Checking dependencies...")
    check_for_dependency('regex', install_method='pip install regex')

    # Import the script and any other necessary modules
    from wa_cli.scripts.licenseheaders import main
    from datetime import datetime
    
    # Prepare our arguments
    if args.tmpl is None:
        copyright_tmpl = get_resolved_path("scripts/data/.copyright.tmpl", wa_cli_relative=True)
    else:
        copyright_tmpl = get_resolved_path(args.tmpl)

    years = args.years
    if years is None:
        years = f"2018-{datetime.now().year}"

    # Generate the argument list for the script
    LOGGER.info("Building licenseheaders script arguments...")
    script_args = ["licenseheader"]
    script_args.extend(["--tmpl", copyright_tmpl]) # the template
    script_args.extend(["--years", years])
    script_args.extend(["--projname", args.projname])
    script_args.extend(["--owner", args.owner])
    script_args.extend(["--projurl", args.projurl])
    script_args.extend(["--dir", get_resolved_path(args.dir)])
    script_args.extend(["--ext"])
    script_args.extend(args.ext)
    script_args.extend(["--exclude", get_resolved_path("scripts/licenseheaders.py", wa_cli_relative=True)])
    for _ in range(args.verbosity):
        script_args.extend(["--verbose"])
    if args.dry_run:
        script_args.extend(["--dry"])
            
    LOGGER.info("Running licenseheaders script...")
    LOGGER.debug(f"Running licenseheaders script with the following args: {script_args}.")
    main(script_args)

    LOGGER.info("Finished running licenseheaders script.")

def init(subparser):
    """Initializer method for the `script` entrypoint.

    This entrypoint serves as a mechanism for running various scripts meant for members of the
    Wisconsin Autonomous student organization.
    """
    LOGGER.debug("Initializing 'script' entrypoint...")

    # Create some entrypoints for additional commands
    subparsers = subparser.add_subparsers(required=False)

    # License subcommand
    # Used to add licenses to the headers of each file in a repository
    license = subparsers.add_parser("license", description="Script which adds a license to the header of each file in a repository")
    license.add_argument("dir", type=str, help="The directory to recursively process.")
    license.add_argument("--tmpl", type=str, help="Template file to use. If it is not set, will default to using the template shipped with the package.", default=None)
    license.add_argument("--years", type=str, help="Year or year range to use. If not set, will use the 2018-<the current year>.", default=None)
    license.add_argument("--projname", type=str, help="Name of the project.", default="WA")
    license.add_argument("--owner", type=str, help="Name of the copyright owner.", default="Wisconsin Autonomous")
    license.add_argument("--projurl", type=str, help="URL of the project.", default="https://wa.wisc.edu")
    license.add_argument("--ext", type=str, nargs="*", help="If specified, restrict processing to the specified extension(s) only.", default=["py", "cpp"])
    license.set_defaults(cmd=run_license)

    return subparser

