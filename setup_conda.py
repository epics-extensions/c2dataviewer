"""
C2 DATA VIEWER is distributed subject to a Software License Agreement found
in the file LICENSE that is included with this distribution.
SPDX-License-Identifier: EPICS
"""

import subprocess
import re
from setuptools import setup, find_packages





def get_version():
    """
    Get version from the git repository in the following format (This should be compatible with PEP440):
        - If the current commit has a tag and no uncommitted changes function will return only tag as a string.
        - If the current commit doesn't have a tag or there are uncommitted changes, version string will look like:
            <last tag in the current development line>_<offset of the last commit from the last tag>_<last commit>[<_dirty if there are uncommitted changes>]
    """
    try:
        version_git = subprocess.check_output(["git", "describe", "--tags", "--long", "--dirty"]).rstrip()
        match = re.search(r'(.*)-(\d+)-g([0-9,a-f]{7})-?(dirty)?', version_git.decode())
        version = match[1]
        tagOffset = int(match[2])
        hash = match[3]
        dirty = match[4]

        if tagOffset == 0 and not dirty:
            VERSION = version
        else:
            VERSION = f"{version}+{tagOffset}.{hash}{'.' if dirty else ''}{dirty if dirty else ''}"

    except:
        print(f"Error: Can not determinate version from git. Using default value of '0.0.1'")
        VERSION = "0.0.1"

    return VERSION


with open("README.md", 'r') as fh:
    long_description = fh.read()


setup (
    name = "c2dataviewer",
    version = get_version(),
    author = "G. Shen",
    author_email = "gshen@anl.gov",
    description = "Python based data viewer for next generation of APS control system (C2)",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    packages = find_packages(),
    package_data = {'c2dataviewer': ['c2dv.cfg', '**/*.ui']},
    include_package_data = True,
    install_requires=[ ],
    entry_points = {'console_scripts': ['c2dv=c2dataviewer.c2dv:main']},
)
