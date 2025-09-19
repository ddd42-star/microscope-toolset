from src.local.execute import Execute
import ast


class MicroscopeStatus:

    def __init__(self, executor: Execute):

        self.executor = executor


    def get_current_status(self) -> dict:

        code = "print(mmc.getSystemState().dict())"
        result_status = self.executor.run_code(code)
        current_status = ast.literal_eval(result_status)

        return current_status

    def get_properties(self) -> dict:

        code ="tmp_list=[(x, mmc.getDeviceSchema(x)) for x in mmc.getLoadedDevices()]\nall_properties = dict(tmp_list)\nprint(all_properties)"
        result_properties = self.executor.run_code(code)
        json_object = ast.literal_eval(result_properties)

        return json_object

    def get_available_configs(self):

        code = "complete_dict={}\nfor x in mmc.getAvailableConfigGroups():\n\ttmp_dict={}\n\tfor y in mmc.getAvailableConfigs(x):\n\t\tconfiguration = mmc.getConfigData(x,y).dict()\n\t\ttmp_dict[y] = configuration\n\tcomplete_dict[x]=tmp_dict\nprint(complete_dict)"

        available_config = self.executor.run_code(code)
        config_json = ast.literal_eval(available_config)

        return config_json
