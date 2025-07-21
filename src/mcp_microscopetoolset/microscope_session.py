

class MicroscopeSession:

    def __init__(self):
        """
        Initialize a Microscope Session. It will initialize once the server is started, and
        it will stop once the Napari gui is closed.
        """
        self.data_dict = {
        "user_query": "",
        "current_user_input": "",
        "conversation": [],
        "context": "",
        "extra_infos": "",
        "microscope_status": {},
        "previous_outputs": "",
        "main_agent_strategy": None,
        "new_strategy_proposed": False,
        "code": None,
        "error": None,
        "error_analysis": None,
        "is_final_output": False,
        "output": None,
        "clarification_needed_from_user": False,
        "approval_needed_from_user": False,
        "is_request_responded": False
    }


    def reset_data_dict(self, old_output, old_microscope_status) -> None:
        self.data_dict = {
        "user_query": "",
        "current_user_input": "",
        "conversation": [],
        "context": "",
        "extra_infos": "",
        "microscope_status": old_microscope_status,
        "previous_outputs": old_output,
        "main_agent_strategy": None,
        "new_strategy_proposed": False,
        "code": None,
        "error": None,
        "error_analysis": None,
        "is_final_output": False,
        "output": None,
        "clarification_needed_from_user": False,
        "approval_needed_from_user": False,
        "is_request_responded": False
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



