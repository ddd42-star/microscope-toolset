

def contains_instance_object(code: str) -> bool:
    """This function return True if the code from LLM contains the instane object of the CMMCorePlus class"""

    if "pymmcore_plus.CMMCorePlus().instance" in code or "CMMCorePlus.instance()" in code:
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
    #for i in ["MMCCorePlus()", "loadSystemConfiguration"]:
    #    code = delete_part_of_code(code, i)
    if contains_instance_object(code=code):
        code = delete_part_of_code(code, "CMMCorePlus()")
    if contains_configuration(code=code):
        code = delete_part_of_code(code, "loadSystemConfiguration")

    return code