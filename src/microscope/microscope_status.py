from python.execute import Execute
import threading
import time
import ast
from typing import List

class MicroscopeStatus:

    def __init__(self, executor: Execute):

        self.status = {}
        self.executor = executor
        self.is_running = True
        self._start = True # check if is the start of the program
    
    def getStatus(self) -> dict:

        return self.status

    def getCurrentStatus(self) -> dict:

        code = "print(mmc.getSystemState().dict())"

        # update microscope status
        result = self.executor.run_code(code)
        
        self.status = ast.literal_eval(result)

        return self.status
    
    def is_different(self, previous_dict: dict, new_dict: dict) -> bool:

        return previous_dict == new_dict

    
    def update(self) -> List[str]:

        previous_status = self.getStatus()
        new_status = self.getCurrentStatus()
        changed = []
        if self.is_different(previous_status, new_status):

            # update new status
            self.status = new_status
            # print new values
            return self.show_new_values(previous_status, new_status)
        return changed

    def show_new_values(self, previous_dict: dict, new_dict: dict) -> List[str]:

        # show which parameter(s) change
        # dict(str, dict(str, str))
        # dict(deviceLabel, dict(propertyLabel, values))
        changes = []
        for deviceLabel in new_dict.keys():
            for propertyLabel in new_dict[deviceLabel].keys():
                # check if the value is a number or a string
                try:
                    previous_value = float(previous_dict[deviceLabel][propertyLabel])
                    new_value = float(new_dict[deviceLabel][propertyLabel])
                except:
                    previous_value = previous_dict[deviceLabel][propertyLabel]
                    new_value = new_dict[deviceLabel][propertyLabel]
                if previous_value != new_value:
                    print(f'The device {deviceLabel} has changed the property {propertyLabel} from value {previous_value} to value {new_value}')
                    changes.append(f'The device {deviceLabel} has changed the property {propertyLabel} from value {previous_value} to value {new_value}')

        return changes

    def monitor(self, check_interval = 1):

        if not self._start:# add the option to skip the first check

            while self.is_running: 
                self.update()
                time.sleep(check_interval)
        
