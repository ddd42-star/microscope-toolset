from pages.states import MAIN_MENU, CHAT_PAGE, EXIT, DATABASE
from prompts.main_agent import MainAgentState


def menu():

    print("""
    Your available options are:\n
    1) chat (Start a new chat)\n
    2) database (create a database)\n
    3) exit\n
    """)
    user_input = input("> ")
    if user_input.lower().strip() == 'chat':
        return CHAT_PAGE
    elif user_input.lower().strip() == 'database':
        return DATABASE
    elif user_input.lower().strip() == "exit":
        return EXIT
    else:
        print("Invalid options! Please select one available options")
        return MAIN_MENU

def chat(executor, client_openai, dbAgent, softwareEngeneeringAgent, reAcAgent, strategy_agent, no_coding_agent, clarification_agent, error_agent, log_agent):

    # instance a new main agent
    # Instance the Main Agent
    main_agent = MainAgentState(client_openai=client_openai, db_agent=dbAgent,
                                software_agent=softwareEngeneeringAgent, reasoning_agent=reAcAgent,
                                strategy_agent=strategy_agent, no_coding_agent=no_coding_agent,
                                clarification_agent=clarification_agent, error_agent=error_agent,
                                executor=executor)

    user_query = user_request_query()

    # change to chat page
    # menu = ""
    # while menu != "quit":
    #     menu = chat(mainAgent=mainAgent,
    #                 dbAgent=dbAgent,
    #                 promptAgent=promptAgent,
    #                 codeAgent=softwareEngeneeringAgent,
    #                 reacAgent=reAcAgent,
    #                 executor=executor,
    #                 microscopeStatus=microscopeStatus,
    #                 fileName=path_cfg_file)

    """
    1) Start: User make a question
    2) Enter the state loop until terminate or Unknown status
    3) Reset states and communication
    """

    while user_query.lower().strip() != "quit":

        loop_user_query = loop_through_states(main_agent=main_agent, initial_user_query=user_query)

        if loop_user_query in ['reset', 'unknown']:
            # reset state
            main_agent.set_state("initial")
            # reset the context dict
            old_context = main_agent.get_context()
            # add the summary to the conversation
            summary_chat = log_agent.prepare_summary(old_context)
            print(summary_chat)
            if summary_chat.intent == "summary":
                data = {"prompt": summary_chat.message, "output": old_context['code'], "feedback": "", "category": ""}
                main_agent.db_agent.add_log(data)
            main_agent.set_context(old_output=old_context['output'], old_microscope_status=old_context['microscope_status'])
            user_query = user_request_query()

    return MAIN_MENU

def database(dbLog):

    # Create database
    print("""
        Your available options are:\n
        1) create (create a database)\n
        2) list (list all database) \n
        3) exit\n
        """)
    user_input = input("> ")

    if user_input.lower().strip() == 'create':
        user_choice = user_new_collection()
        print(f'You selected the name {user_choice}. Are you sure? Please answer yes or no!')
        user_confirm = input("> ")
        if user_confirm.lower().strip() == 'yes':
            try:
                dbLog.create_collection(collection_name=user_choice)
                return MAIN_MENU
            except Exception as e:
                print("impossible to create the new collection.")
                return MAIN_MENU
        elif user_confirm.lower().strip() == 'no':
            return MAIN_MENU
        else:
            print("invalid options!")
            return MAIN_MENU

    elif user_input.lower().strip() == 'list':
        list_of_collection = dbLog.list_collection()
        print(f"The available collection are {list_of_collection}")
        return MAIN_MENU
    elif user_input.lower().strip() == 'exit':
        return EXIT
    else:
        print("Invalid options!")
        return MAIN_MENU

def user_new_collection():
    print("Please select the name of your new collection: \n")
    user_choice = input("> ")

    return user_choice

def user_request_query():
    user_query = input("Digit your query: ")

    return user_query

def loop_through_states(main_agent, initial_user_query):
    user_input = initial_user_query
    while True:

        response = main_agent.process_query(user_query=user_input)

        # checks new state
        if main_agent.get_state() in ["awaiting_clarification", "awaiting_user_approval"]:
            print(f"Main Agent: {response}")
            # add input
            user_input = input("User: ")
        elif main_agent.get_state() == "terminate":
            print(f"The output of the user's query: {main_agent.get_context()['output']}")
            output = 'reset'
            break

        elif main_agent.get_state() == "Unknown_status":
            print("Unknown request")
            output = 'unknown'
            break
        else:
            user_input = None # the states don't need a user input


    return output
