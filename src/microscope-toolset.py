# Run the application
import sys
import os
from python.execute import Execute

def main():

    # the input should be like this
    # python microscope-toolset --cfg <cfg name> --api_key <LLM key> --database <path to database> 
    # python microscope-toolset --cfg <cfg name> --api_key --database <path to database> 
    tot_arg = len(sys.argv) - 1 

    list_arg = str(sys.argv)

    
    if "--cfg" not in list_arg:
        raise TypeError("missing --cfg keyword")
    
    if "--api_key" not in list_arg:
        raise TypeError("missing --api_key keyword")

    if "--database" not in list_arg:
        raise TypeError("missing --database keyword")
    
    try:
        # try to convert the input given in the command line
        path_cfg_file = str(sys.argv[2])

    except Exception as e:
        return e
    
    try:
        # get API key
        api_key_dict = {}
        if str(sys.argv[4]) == "--database":
            #get API key from system
            
            for i in ["OPENAI_API_KEY","GEMINI_API_KEY", "OLLOMA_API_KEY", "ANTHROPIC_API_KEY"]:
                api_key_dict[i] = os.getenv(i)
            # TODO add part when the key is missing
                try:
                    # try to convert the input given in the command line
                    path_database_file = str(sys.argv[5])

                except Exception as e:
                    return e

        else:
            try:
                # get information about the api_key. Should be of a format of type_LLM:key
                llm, key = str(sys.argv[4].split(":"))
            except Exception as e:
                return e
            
            api_key_dict[llm] = key

            try:
                # try to convert the input given in the command line
                path_database_file = str(sys.argv[6])

            except Exception as e:
                return e

    except Exception as e:
        return e
    
    # start the program

    try:
        # Instancied the namespace
        executor = Execute(path_cfg_file)

        # call the databas
        # TODO

    except Exception as e:
        sys.exit(e)
    
   


if "__main__" == "__name__":
    # run the program
    main()
    