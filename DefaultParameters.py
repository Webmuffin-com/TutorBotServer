# This is no longer used as if nothing specified, we assume it's in the conundrum
def get_default_scenario():
    prompt_parameter = ""
    return prompt_parameter

# We require at least this action plan to keep bot out of the weeks
def get_result_formatting():
    prompt_parameter = """
- Use the content in the CORPUS section of the prompt to provide guidance for completing the task.
- You should limit your responses to ideas and concepts presented in the CORPUS unless specified differently in the CONUNDRUM

Please format all responses in Markdown"""

    return prompt_parameter
