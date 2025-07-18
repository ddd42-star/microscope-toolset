

class SessionContext:

    def __init__(self, user_query: str):
        self.user_query = user_query
        self.outputs = []
        self.errors = []
        self.is_finalized = False

    def add_output(self, output: str):
        self.outputs.append(output)

    def add_errors(self, error_message: str):
        self.errors.append(error_message)

    def finalize(self):
        self.is_finalized = True
