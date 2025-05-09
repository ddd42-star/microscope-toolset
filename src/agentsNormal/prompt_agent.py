


class PromptAgent:

    def __init__(self):
        self.prompt = ""

    def create_prompt(self, reformulated_query: str, context: str) -> str:
        new_prompt = """
        CONTEXT:
        {context}

        REFORMULATED QUERY:
        {reformulated}
        """.format(
            context=context,
            reformulated=reformulated_query
        )

        return new_prompt

    def add_new_strategy(self, context: str, reformulated_query: str, new_strategy: str) -> str:
        new_prompt = """
        CONTEXT:
        {context}

        REFORMULATED QUERY:
        {reformulated}

        TRY THIS NEW STRATEGY:
        {new_strategy}

""".format(context=context, reformulated=reformulated_query, new_strategy=new_strategy)

        return new_prompt
