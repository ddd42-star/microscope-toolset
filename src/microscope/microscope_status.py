import pymmcore_plus
from python.execute import Execute

class MicroscopeStatus:

    def __init__(self):

        self.status = {}
    

    def getCurrentStatus(self, executor: Execute) -> dict:

        code = "mmc.getSystemState().dict()"

        # update microscope status
        self.status = dict(executor.run_code(code))

        return self.status
    
