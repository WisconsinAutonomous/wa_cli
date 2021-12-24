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
import os
import inspect
import importlib


def _not_hidden(f):
    return f[0] != "_" and f[0] != '.'


def _get_files(file_):
    return [
        os.path.splitext(f.name)[0]
        for f in os.scandir(os.path.dirname(file_))
        if f.is_file() and _not_hidden(f.name)
    ]


def _get_dirs(file_, ignore=[]):
    return [
        os.path.splitext(f.name)[0]
        for f in os.scandir(os.path.dirname(file_))
        if f.is_dir() and _not_hidden(f.name) and f.name not in ignore
    ]


def _import(module, gbls, ignore=[]):
    # Get caller info
    filename = inspect.stack()[1].filename
    path = os.path.dirname(os.path.realpath(
        filename)).split("wa_cli")[-1]
    path = f"wa_cli{path.replace(os.path.sep, '.')}" if path else "wa_cli"

    # get a handle on the module
    mdl = importlib.import_module(f"{path}.{module}")

    # is there an __all__?  if so respect it
    if "__all__" in mdl.__dict__:
        names = mdl.__dict__["__all__"]
    else:
        # otherwise we import all names that don't begin with _
        names = [x for x in mdl.__dict__ if not x.startswith("_")]

    # now drag them in
    gbls.update({k: getattr(mdl, k) for k in names})
