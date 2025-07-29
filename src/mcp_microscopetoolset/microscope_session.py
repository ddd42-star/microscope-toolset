

class MicroscopeSession:

    def __init__(self):
        """
        Initialize a Microscope Session. It will initialize once the server is started, and
        it will stop once the Napari gui is closed.
        """
        self.data_dict = {
        "user_query": "",
        "conversation": [],
        "context": "",
        "extra_infos": "",
        "microscope_status": {},
        "microscope_properties": {},
        "configuration_presets": {},
        "previous_outputs": "",
        "main_agent_strategy": None,
        "code": None,
        "error": None,
        "is_final_output": False,
        "output": None
    }


    def reset_data_dict(self, old_output, old_microscope_status, old_microscope_properties, old_microscope_presets) -> None:
        self.data_dict = {
        "user_query": "",
        "conversation": [],
        "context": "",
        "extra_infos": "",
        "microscope_status": old_microscope_status,
        "microscope_properties": old_microscope_properties,
        "configuration_presets": old_microscope_presets,
        "previous_outputs": old_output,
        "main_agent_strategy": None,
        "code": None,
        "error": None,
        "is_final_output": False,
        "output": None
    }

    def get_data_dict(self):
        return self.data_dict

    def update_data_dict(self, **kwargs):
        try:
            for k, val in kwargs.items():
                self.data_dict[k] = val
        except Exception as e:
            print(e)

    def is_main_user_query(self):
        """
        Check if the user already started the feedback loop.
        """
        if self.data_dict['user_query'] == "":
            return False

        return True


    def close_session(self):
        return None



