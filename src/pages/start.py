from pages.states import EXIT, MAIN_MENU, START_PAGE

def start_page():
    # start the program
    #mainLogger = logging.getLogger(__name__)
    #mainLogger.info("Welcome to Microscope-toolset!!\n\n")
    print("Welcome to Microscope-toolset!!\n\n")
    print("Please select: 'start', 'infos', 'exit'")

    user_choice = input("> ")

    if user_choice.lower().strip() == 'start':
        return MAIN_MENU
    elif user_choice.lower().strip() == 'exit':
        return EXIT
    else:
        print("Invalid request! Please select one of the available options!")
        return START_PAGE