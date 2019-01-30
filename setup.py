import os
from setuptools import setup, find_packages

import versioneer

setup (
    name = "c2dataviewer",
    version = versioneer.get_version(),
    author = "G. Shen",
    author_email = "gshen@anl.gov",
    description = "Python based data viewer for next generation of APS control system (C2)",
    packages = find_packages(),
    package_data = {'c2dataviewer': ['c2dv.cfg', '**/*.ui']},
    include_package_data = True,
    install_requires = [],
    entry_points = {'console_scripts': ['c2dv=c2dataviewer.c2dv:main']},
)
