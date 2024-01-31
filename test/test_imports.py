import unittest
from os.path import abspath, dirname, split, splitext
from glob import glob

class Test_ModulesImport(unittest.TestCase):
    def testModulesImport(self):
        errors = []
        root = abspath(dirname(dirname(__file__)))

        mods = []
        for f in glob(f'{root}/src/*.cxx'):
            mod, _ = splitext(split(f)[1])
            if mod.endswith("_2"):
                continue
            mods.append(f'OCCT.{mod}')

        for mod in mods:
            try:
                __import__(mod)
            except ImportError as e:
                if "Vtk" in mod:
                    pass # Ignore
                else:
                    errors.append(mod)
                print(f"Error importing {mod}:")
                print(f"  {e}")
        self.assertFalse(errors)

if __name__ == '__main__':
    unittest.main()
