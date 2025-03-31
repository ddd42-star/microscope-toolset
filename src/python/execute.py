# This class initialize namepsace dictonary where the
# testing code will be run.
import importlib
import subprocess
import sys
from io import StringIO
from contextlib import redirect_stdout


class Execute:


    def __init__(self, filename: str):
        self.namespace = {}
        exec(f"from pymmcore_plus import CMMCorePlus\nmmc = CMMCorePlus().instance()\nmmc.loadSystemConfiguration({filename})", self.namespace) # add fist line of code
        # instantiate the object
        #self.namespace["mmc"] = self.namespace["The class"]()
        # probably not necessary

    def install_library(self, module: str):
        """Install missing packages using pip"""
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", module])
        except subprocess.CalledProcessError:
            return False
        
        return True

    def test_code(self, code:str):

        while True:

            try:
                exec(code, self.namespace)
                print("Code executed successfully")
                return True
            except ModuleNotFoundError as e:# case 1, module not imported
                module_name = str(e).strip("'")[1] # to check, extract module name
                self.namespace[module_name] = importlib.import_module(module_name) 
            except ImportError as e:# case 2, module not found, it must be installed (this only after checking if all the modules are presents.)
                import_module = str(e).strip("'")[1] # extract module name
                if self.install_library(import_module):
                    continue
                else:
                    print("Could not install the module")
                    return False
            except Exception as e:
                print(f"{e}")
                print("Stop execution")
                return False
            
    def run_code(self, code: str):

        is_run = False
        while not is_run:
            try:
                f = StringIO()
                with redirect_stdout(f):
                    exec(code, self.namespace)
                

                read_output = f.getvalue().strip()
                print("Code executed successfully")
                is_run = True
            except ModuleNotFoundError as e:# case 1, module not imported
                module_name = str(e).strip("'")[1] # to check, extract module name
                self.namespace[module_name] = importlib.import_module(module_name) 
            except ImportError as e:# case 2, module not found, it must be installed (this only after checking if all the modules are presents.)
                import_module = str(e).strip("'")[1] # extract module name
                if self.install_library(import_module):
                    continue
                else:
                    print(f"Could not install the module {import_module}")
                    read_output = f"Could not install the module {import_module}"
                    break
            except Exception as e:
                print(f"{e}")
                print("Stop execution, send back the code to the agent!")
                read_output = repr(e)
                is_run = True

        return read_output
            
    

        