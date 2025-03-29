# This function takes the str of the code from the LLM 
# and prepare it for the execution


def contains_instance_object(code: str) -> bool:
    """This function return True if the code from LLM contains the instane object of the MMCCorePlus class"""

    if "pymmcore_plus.MMCCorePlus().instance" in code or "MMCCorePlus.instance()" in code:
        return True
    return False

def contains_configuration(code: str) -> bool:
    """This function return True if the code from LLM contains loadSystemConfiguration function"""

    if "loadSystemConfiguration" in code:
        return True
    
    return False

def delete_part_of_code(code: str, name: str) -> str:
    """This function delete line of code that are not expected"""
    # delete the line of code that should not be present
    new_code = []
    for subcode in code.split("\n"):
        if name not in subcode:
            new_code.append(subcode)

    return "\n".join(new_code)


def prepare_code(code: str, **kwargs) -> str:
    """This function prepare the code to test"""
    # check for unexpected code line
    for i in ["MMCCorePlus()", "loadSystemConfiguration"]:
        code = delete_part_of_code(code, i)

    # Fix indentation problems
    formatted_code = code.format(
        ", ".join(kwargs.keys()) if kwargs else "",
        "\n".join('t' + i for i in code.split('\n'))
    )


    return formatted_code