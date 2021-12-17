# Wisconsin Autonomous Command Line Interface Tool

This repository holds the WA CLI tool. This tool is expandable and is primarily used to reduce repetitive processes or implements helpful scripts to doing various tasks (like installing packages, etc.).

## Setup

To setup the WA cli, it is fairly simple. You simply need Python3 installed on your system, and then run the following command:

```
pip3 install wa_cli
```

**NOTE: Not actually implemented yet!!**

## Developing

To develop the WA cli, you can do the following.

### Clone the repo

First, clone the miniav repo locally:

```bash
git clone git@github.com:uwsbel/wa_cli.git
cd wa_cli
```

### Install the miniav package

_**Note: This installs the  repository using symlinks. This means you can edit the files and test the changes without reinstalling the tool.**_

```bash
python setup.py develop
```
