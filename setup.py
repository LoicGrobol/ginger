import os.path

import json

with open('package.json') as package_json:
    package_metadata = json.load(package_json)

import glob
from setuptools import setup
import itertools
from setuptools.command.install import install as _install
import pip


class install(_install):
    def run(self):
        _install.run(self)
        # Local dependencies
        for dep_path in (spec[6:] for dep, spec in package_metadata["dependencies"].items()
                         if spec.startswith('file:')):
            pip.main(['install', os.path.abspath(dep_path)])


# Getting complex (sub)package dependencies
packages_data = {}
for package, data_patterns_lst in package_metadata["packages_data"].items():
    package_path = package_metadata["packages"][package]
    package_data_path = (
        (
            os.path.relpath(concrete_path, package_path)
            for concrete_path in glob.glob(os.path.join(package_path, data_pattern), recursive=True)
        )
        for data_pattern in data_patterns_lst
    )
    packages_data[package] = list(itertools.chain.from_iterable(package_data_path))

# Ensure that `package.json` is in the root package
packages_data[package_metadata["name"]] = packages_data.get(package_metadata["name"], []) + ['package.json']


setup(
    name=package_metadata["name"],

    version=package_metadata["version"],

    description=package_metadata["description"],

    url=package_metadata["url"],

    author=package_metadata["author"]["name"],
    author_email=package_metadata["author"]["email"],

    license=package_metadata["license"],
    keywords=package_metadata["keywords"],
    classifiers=package_metadata["classifiers"],

    packages=[package_metadata["name"],  *package_metadata["packages"].keys()],
    package_dir={package_metadata["name"]: '.', **package_metadata["packages"]},
    package_data=packages_data,

    install_requires=['{dep}{spec}'.format(dep=dep, spec=spec)
                      for dep, spec in package_metadata["dependencies"].items()
                      if not spec.startswith('file:')],

    entry_points={
        group: [
            '{name}={command}'.format(name=name, command=command)
            for name, command in epoints.items()
        ]
        for group, epoints in package_metadata["entry_points"].items()
    },

    include_package_data=True
)
