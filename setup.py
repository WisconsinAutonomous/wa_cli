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
"""A setuptools based setup module."""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

# Get the long description from the README file
long_description = (here / 'README.md').read_text(encoding='utf-8')


def parse_requirements():
    with open('requirements.txt') as f:
        required = f.read().splitlines()

    return required

def create_version():
    from setuptools_scm.version import get_local_dirty_tag

    def clean_scheme(version):
        return get_local_dirty_tag(version) if version.dirty else '+clean'

    return {'local_scheme': clean_scheme}

setup(
    name='wa_cli',  # Required
    use_scm_version=create_version,
    description='Wisconsin Autonomous Command Line Interface Tool',  # Optional
    long_description=long_description,  # Optional
    long_description_content_type='text/markdown',  # Optional (see note above)
    author='Wisconsin Autonomous',  # Optional
    author_email="wisconsinautonomous@studentorg.wisc.edu",
    license="MIT",
    packages=find_packages(),  # Required
    python_requires='>=3.6, <4',
    install_requires=parse_requirements(),  # Optional
    entry_points={  # Optional
        'console_scripts': [
            'wa=wa_cli.wa:main',
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Software Development",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
    project_urls={  # Optional
        "Homepage": "https://github.com/WisconsinAutonomous/wa_cli/",
        "Bug Reports": "https://github.com/WisconsinAutonomous/wa_cli/issues",
        "Source Code": "https://github.com/WisconsinAutonomous/wa_cli/",
        "Our Team!": "https://wa.wisc.edu",
    },
)
