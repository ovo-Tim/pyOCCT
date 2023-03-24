from unittest import TestCase
from glob import glob

class Test_ModulesImport(TestCase):
    def testModulesImport(self):
        errors = []
        mods = ['OCCT.' + f[7:-4] for f in glob('../src/*.cxx')]
        for mod in mods:
            print(f"Importing... {mod}")
            try:
                __import__(mod)
                print("Ok")
            except ImportError as e:
                errors.append(mod)
                print(f"Error: {e}")
        self.assertFalse(errors)

