# pyOCCT — Python bindings for OpenCASCADE

[![Documentation Status](https://readthedocs.org/projects/pyocct/badge/?version=latest)](http://pyocct.readthedocs.io/en/latest/?badge=latest)
[![Join the chat at https://gitter.im/pyOCCT/Lobby](https://badges.gitter.im/pyOCCT/Lobby.svg)](https://gitter.im/pyOCCT/Lobby?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
![Workflow](https://github.com/trelau/pyOCCT/workflows/Workflow/badge.svg)

[![Anaconda-Server Badge](https://anaconda.org/trelau/pyocct/badges/version.svg)](https://anaconda.org/trelau/pyocct)
[![Anaconda-Server Badge](https://anaconda.org/trelau/pyocct/badges/latest_release_date.svg)](https://anaconda.org/trelau/pyocct)
[![Anaconda-Server Badge](https://anaconda.org/trelau/pyocct/badges/installer/conda.svg)](https://anaconda.org/trelau/pyocct)
[![Anaconda-Server Badge](https://anaconda.org/trelau/pyocct/badges/platforms.svg)](https://anaconda.org/trelau/pyocct)
[![Anaconda-Server Badge](https://anaconda.org/trelau/pyocct/badges/downloads.svg)](https://anaconda.org/trelau/pyocct)

The **pyOCCT** project provides Python bindings to the OpenCASCADE geometry kernel via pybind11.
Together, this technology stack enables rapid CAD/CAE/CAM application development in the popular
Python programming language.

If you are looking for Python bindings for CAE capabilities, check out
[pySMESH](https://github.com/trelau/pySMESH). 

## Enabling technology
The `pyOCCT` core technology stack includes:

* [OpenCASCADE](https://www.opencascade.com): Open CASCADE Technology (OCCT) is an object-oriented
  C++ class library designed for rapid production of sophisticated domain-specific CAD/CAM/CAE
  applications.

* [pybind11](https://github.com/pybind/pybind11): A lightweight header-only library that exposes
  C++ types in Python and vice versa, mainly to create Python bindings of existing C++ code.

## Getting started using conda
[Conda packages](https://anaconda.org/trelau/dashboard/) are available for a number of
platforms and Python versions. Get started with:

    conda create -n pyocct python=3.8
    activate pyocct
    conda install -c conda-forge -c trelau pyocct

This will create an environment named "pyocct" and install `pyOCCT` and all necessary dependencies.
You can replace the "pyocct" environment name with anything you'd like.

To support minimal visualization the wxPython package is required and can be installed via conda by:

    conda activate pyocct
    conda install -c conda-forge wxpython

Navigate to the `examples/` folder and run from the active environment:

    python import_step.py

and you should see the following image in the viewing tool if all the requirements are correctly
installed.

![compressor](./docs/source/resources/compressor.jpg)

Installation files can be cleaned up by:

    conda clean -a

## Building from sources
To build from sources, you must generate the binding source code locally. This can be done using the
[pyOCCT_binder](https://github.com/trelau/pyOCCT_binder) project which is available as a git
submodule in this repository within the `binder/` folder.

Clone this repository and use the `--recurse-submodules` command to initialize and download the
external `pyOCCT_binder` project:

    git clone --recurse-submodules https://github.com/trelau/pyOCCT.git

The binder uses `clang` to parse the C++ header files of the libraries and generate the source
code. If you are familiar with `conda`, an environment can be created for this task by:

    conda env create -f binder/environment.yml

If all the necessary dependencies are available, the binder can be run to generate the binding
sources:

    python binder/run.py -c binder/config.txt -o src

Be sure and check the output from the binding generation process in the command prompt in case there
are missing header files or other errors.

After the binding sources are generated:

    mkdir build
    cd build
    cmake ..

Note that `PTHREAD_INCLUDE_DIR` will likely need defined manually since it cannot typically not be
automatically found by CMake.


## Updating for new version

When updating to a new version of OCCT please ensure the occt version is
updated in the following files:

- ci/conda/meta.yaml
- binder/environment.yml
- CMakeLists.txt (project version, settings, and OCCT required version)
- OCCT/__init__.py
- Ensure cmake/OCCT_Modules.cmake is up to date
