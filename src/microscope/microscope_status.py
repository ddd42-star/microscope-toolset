import pymmcore_plus
from python.execute import Execute

class MicroscopeStatus:

    def __init__(self):

        self.status = {}
    

    def getCurrentStatus(self, executor: Execute) -> dict:

        code = "mmc.getSystemState().dict()"

        return dict(executor.run_code(code))
    
