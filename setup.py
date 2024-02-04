import re
from setuptools import setup


def get_version():
    with open("OCCT/__init__.py") as f:
        for line in f:
            m = re.match(r"__version__ = ['\"](.+)['\"]", line)
            if m:
                return m.group(1)
    raise ValueError("Could not find version")


setup(
    name='OCCT',
    version=get_version(),
    packages=['OCCT', 'OCCT.Extend', 'OCCT.Display'],
    package_data={'OCCT': ['*.so', '*.pyd', '*.dll', 'Display/_resources/*']},
    author='Trevor Laughlin',
    description='Python bindings for OpenCASCADE via pybind11.',
    url='https://github.com/trelau/pyOCCT',
    license='LGPL v2.1',
    platforms=['Windows', 'Linux']
)
