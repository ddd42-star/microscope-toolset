from agents.database_agent import DatabaseAgent
from agents.software_agent import SoftwareEngeneeringAgent
from agents.reasoning_agent import ReasoningAgent
from agents.strategy_agent import StrategyAgent
from agents.error_agent import ErrorAgent
from agents.no_coding_agent import NoCodingAgent
from agents.clarification_agent import ClarificationAgent
from agents.structuredOutput import MainAgentOutput
from prompts.mainAgentPrompt import CLASSIFY_INTENT
from python.prepare_code import prepare_code
from python.execute import Execute
import ast
from openai import OpenAI


def user_message(message):

    return [{"role": "user", "content": message}]


def agent_message(message: str):

    return [{"role": "assistant", "content": message}]


class MainAgentState:

    def __init__(self, client_openai: OpenAI, db_agent: DatabaseAgent, software_agent: SoftwareEngeneeringAgent,
                 reasoning_agent: ReasoningAgent, strategy_agent: StrategyAgent, no_coding_agent: NoCodingAgent,
                 clarification_agent: ClarificationAgent, error_agent: ErrorAgent,
                 executor: Execute):
        self.state = "initial"
        self.context = {
            "conversation": [],
            "user_query": "",
            "context": "",
            "extra_infos": "",
            "microscope_status": {},
            "previous_outputs": "",
            "main_agent_strategy": None,
            "new_strategy": None,
            "code": None,
            "error": None,
            "error_analysis": None,
            "finale_output": False,
            "output": None,
            "clarification_request": ""
        }
        self.client_openai = client_openai
        self.db_agent = db_agent
        self.software_agent = software_agent
        self.reasoning_agent = reasoning_agent
        self.strategy_agent = strategy_agent
        self.error_agent = error_agent
        self.execute = executor
        self.no_coding_agent = no_coding_agent
        self.clarification_agent = clarification_agent
        # add differents agents

    def get_state(self) -> str:
        return self.state

    def get_context(self):
        return self.context

    def set_state(self, new_state: str):
        self.state = new_state
    def set_context(self, old_output, old_microscope_status):
        # TODO: add later conversation (maybe!)
        self.context = {
            "conversation": [],
            "user_query": "",
            "context": "",
            "extra_infos": "",
            "microscope_status": old_microscope_status,
            "previous_outputs": old_output,
            "main_agent_strategy": None,
            "new_strategy": None,
            "code": None,
            "error": None,
            "error_analysis": None,
            "finale_output": False,
            "output": None,
            "clarification_request": ""
        }

    def process_query(self, user_query: str):

        # return state, {dict with information}
        if self.state == "initial":
            # retrieve the context from the vector db
            # retrieve the log from the feedback db
            # retrieve the context just once
            if self.context["context"] == "":
                context = self.db_agent.look_for_context(query=user_query)
                self.context["context"] = context
                self.context["user_query"] = user_query
                #self.context["conversation"] = self.context["conversation"] + self.user_message(user_query)

            # classify user's intent
            classify_intent = self.classify_intent(context=self.context)

            if classify_intent.intent == 'ask_for_info':
                self.state = "awaiting_clarification"
                self.context["clarification_request"] = classify_intent.message
                # add LLM answer to the conversation
                self.context["conversation"] = self.context["conversation"] + agent_message(classify_intent.message)
                return classify_intent.message
            elif classify_intent.intent == 'propose_strategy':
                self.state = "planning_strategy"
                return None # no message needed
            elif classify_intent.intent == 'no_code_needed':
                # answer normally
                answer_message = self.no_coding_agent.no_coding_asnwer(self.context)
                self.context["output"] = answer_message
                self.state = "terminate"
                return  None # no message needed

        elif self.state == "awaiting_clarification":
            # 1) awaiting clarification from user query
            #user_clarification = self.clarification_agent.user_clarification(self.context)
            user_clarification = user_query.lower()
            self.context["extra_infos"] =  "User: " + user_clarification
            # add to the conversation
            self.context["conversation"] = self.context["conversation"] +  user_message(user_clarification)
            self.state = "initial"

            return None # no message needed

            # 2) awaiting clarification from agent strategy
            # TODO checks if works for both clarification

        elif self.state == "planning_strategy":

            # no new strategy
            if self.context["new_strategy"] is None:
                if self.context["main_agent_strategy"] is None:
                    #  1) create a strategy
                    created_strategy = self.strategy_agent.generate_strategy(self.context)

                else:
                    # 2) user doesn't like the main strategy
                    created_strategy = self.strategy_agent.generate_strategy(self.context)

                if created_strategy.intent == "strategy":
                    # add strategy to self.context
                    self.context["main_agent_strategy"] = created_strategy.message
                    # add to conversation
                    self.context["conversation"] = self.context["conversation"] + user_message(created_strategy.message)
                    # change state
                    self.state = "awaiting_user_approval"
                    return created_strategy.message
                elif created_strategy.intent == "need_information":
                    self.state = "awaiting_clarification"
                    self.context["clarification_request"] = created_strategy.message
                    # add to conversation
                    self.context["conversation"] = self.context["conversation"] + agent_message(created_strategy.message)
                    return created_strategy.message

            else:
                # 2) new strategy
                new_strategy_agent = self.strategy_agent.revise_strategy(self.context)
                if new_strategy_agent.intent == "new_strategy":
                    self.context["new_strategy"] = new_strategy_agent.message
                    # add to conversation
                    self.context["conversation"] = self.context["conversation"] + agent_message(new_strategy_agent.message)
                    self.state = "executing_code"

                    return None # no message needed

        elif self.state == "awaiting_user_approval":
            # add to conversation
            self.context["conversation"] = self.context["conversation"] + user_message(user_query.lower())
            # ask the user for approval
            if user_query.lower() == "yes":
                self.state = "executing_code"
                return None # no message needed
            elif user_query.lower() == "no":
                self.state = "planning_strategy"
                return "Please propose a new strategy."
            else:
                self.state = "awaiting_user_approval"
                return "Please answer 'yes' or 'no'!"

        elif self.state == "validating_strategy":
            # this with the new strategy proposed
            pass
        elif self.state == "executing_code":
            if self.context["new_strategy"] is None:

                # create piece of code
                code = self.software_agent.generate_code(context=self.context)
            else:
                # fix code
                code = self.software_agent.fix_code(context=self.context)

            if code.intent == "code":
                # run the code
                prepare_code_to_run = prepare_code(code.message.strip("```"))
                self.context["code"] = prepare_code_to_run
                print("prepare code: ", prepare_code_to_run)
                # logger.info("prepare code: %s", prepare_code_to_run)
                # run the code
                self.context["conversation"] = self.context["conversation"] + agent_message(prepare_code_to_run)
                output = self.execute.run_code(prepare_code_to_run)
                # is_valid = False
                if "Error" not in output:
                    # 1) run successfully
                    # is_valid = True
                    self.state = "finish"
                    self.context["final_output"] = True
                    self.context["output"] = output
                    return None # no message needed

                else:
                    # 2) errors. Catch it and send it to the agent
                    self.context["error"] = output
                    # add to conversation
                    self.context["conversation"] = self.context["conversation"] + agent_message(output)
                    self.state = "handling_errors"
                    return None # no message needed

        elif self.state == "handling_errors":
            # 1) analyze the error
            error_analysis = self.error_agent.analyze_error(self.context)
            if error_analysis.intent == "error_analysis":
                # 2) ask new strategy
                self.state = "planning_strategy"
                self.context["error_analysis"] = error_analysis.message
                return None # no message needed

        elif self.state == "finish":
            if self.context["final_output"] is True:
                # add to conversation
                self.context["conversation"] = self.context["conversation"] + agent_message(f"The output of the query is {self.context['output']}")
                # reset all the needed variable ready for a new user query
                self.state = "terminate"
                return None # no message needed
        self.state = "Unknown_status"
        return None # no message needed

    def classify_intent(self, context):
        #print("this is the context that pass:", context)
        prompt = CLASSIFY_INTENT.format(
            context=context["context"] or "no information",
            microscope_status=context["microscope_status"] or "no information",
            previous_outputs=context["previous_outputs"] or "no information"
        )
        # print(prompt)
        history = [{"role": "system","content": prompt},{"role": "user","content": context["user_query"]}] + context["conversation"]
        response = self.client_openai.beta.chat.completions.parse(
            model="gpt-4.1-mini",
            messages=history,
            response_format=MainAgentOutput
        )
        return self.parse_agent_response(response.choices[0].message.content)  # it should be a python dictonary

    def parse_agent_response(self, response: str):
        # try:
        #     return ast.literal_eval(response)
        # except (ValueError, SyntaxError):
        #     pass


        # return ast.literal_eval(response)
        # verify if the LLM managed to output
        output_raw = MainAgentOutput.model_validate_json(response)

        return output_raw
