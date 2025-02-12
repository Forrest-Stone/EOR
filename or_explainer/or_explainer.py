"""A simplified implementation of ORExplainer framework with AutoGen.

The ORExplainer agent will interact with LLM-based agents.

Notes:

1. We assume the changeable part is just in the objective function and constraints, the decision variables are not be changed. According to differnet code impelmentation style, the parameters will be intergated in the obejective function and constraints or in a separate part.

So, if the code has the separate part for parameters, when parameters in obejective function and constraints are changed, we just need to change the data section. If the parameters are integrated in the obejective function and constraints, we need to change the objective function section and the constraint section.

2. We assume the code snippet is inserted into the source code correctly.  According to the code version, the changes are most happended in the data section if the code has data section. Others may happen in the objective function section and the constraint section. So, to make the code more readable and formatable, we auume the code has always defined the data section, so we simplify the evaluation only to "DATA CODE" and "CONSTRAINT CODE", where we would insert the newly added code or updated the old code.

Under our assumption, we have the follwoing types:
- Data Section: Only have update the data.
- Constraint Section: Only have add or delete the constraints.

"""
import json
import os
import re
from typing import Dict, List, Optional, Union

import autogen
from autogen.agentchat.agent import Agent
from autogen.code_utils import extract_code
from eventlet.timeout import Timeout
from termcolor import colored
from utils import graph_dist_computing, save_src_code

try:
    from gurobipy import GRB
except Exception:
    print("Note: Gurobi not loaded")

try:
    from pyomo.opt import TerminationCondition
except Exception:
    print("Note: Pyomo not loaded")


# %% System Messages
WRITER_SYSTEM_MSG = """

**Role:** You are a chatbot tasked with:
(1) Writing Python code for operations research-related projects.
(2) Explaining solutions using the Gurobi Python solver.

--- Problem Description: ---
{description}

--- Source Code: ---
{source_code}

--- Documentation: ---
{doc_str}

--- Example Q&A: ---
{example_qa}

--- Original Execution Result: ---
{execution_result}


**Task:**
You are provided with the original problem description and the correct code for an operations research problem. Based on the user's query, update the code accordingly. Your task may involve either deleting constraints or adding new data or constraints.


**Steps:**

1. Determine the Required Operations:

    - **Add Operation:** Generate new code for data or constraints to be added.
        - Insert the new data between the markers:
          "# ORExplainer DATA CODE GOES HERE" and "# ORExplainer DATA CODE ENDS HERE".
        - Insert the new constraints between the markers:
          "# ORExplainer CONSTRAINT CODE GOES HERE" and "# ORExplainer CONSTRAINT CODE ENDS HERE".

    - **Delete Operation:** Identify the relevant block within the constraints section that needs to be deleted.
        - The code to be deleted will be between the markers:
          "# ORExplainer CONSTRAINT CODE GOES HERE" and "# ORExplainer CONSTRAINT CODE ENDS HERE".

2. Return the Changes in JSON Format:

    - Use the keys "DELETE CONSTRAINT", "ADD CONSTRAINT", or "ADD DATA". Only these keys are allowed.
    - The values should be the Python code snippet to be deleted (exactly as it appears in the original code) or the new code to be added.
    - Include comments within the code snippets using the prefix "#".
    - Ensure the line breaks and indents of the code are correct.

3. Output Requirements:

    - Return only the JSON object with the changes.
    - Do not include any additional information in the response.
    - Do not add new decision variables.
    - Ensure the JSON is valid, properly formatted.


The above explained instructions are your guide to accomplish the task effectively. Your user's success heavily relies upon your ability to provide the precise and accurate Python code changes within the existing operations research problem. Good Luck!

"""


SAFEGUARD_SYSTEM_MSG = """

**Role:** You are a code safety evaluator.


**Task:** Review the provided source code to determine if it is safe to execute, ensuring it does not contain any malicious code that could compromise security or privacy.


**Instructions:**

--- Source Code: ---
{source_code}

**Question:**
Is the code safe to run?

**Answer:**
Respond with one word:
    `SAFE` if the code is secure.
    `DANGER` if the code poses any risk.

"""


# %% Constant strings to match code lines in the source code.
DATA_CODE_START = "# ORExplainer DATA CODE GOES HERE"
DATA_CODE_END = "# ORExplainer DATA CODE ENDS HERE"
CONSTRAINT_CODE_START = "# ORExplainer CONSTRAINTS CODE GOES HERE"
CONSTRAINT_CODE_MIDDLE = "# ORExplainer CONSTRAINTS CODE MIDDLE HERE"
CONSTRAINT_CODE_END = "# ORExplainer CONSTRAINTS CODE ENDS HERE"


# %% Prompt for ORExplainer
CODE_PROMPT = """

**Role:** You are a professional software developer tasked with handling code modification requests. Your role is to interpret these requests which describe changes needed in a source code.


**Task:** Your task is to return the changes to be made to the source code based on the user's query. The modifications should be returned in a JSON format containing only the necessary changes.


**JSON Format Requirements:**

    - Use the keys "DELETE CONSTRAINT", "ADD CONSTRAINT", or "ADD DATA". Only these keys are allowed.
    - The values should be the Python code snippet to be deleted (exactly as it appears in the original code) or the new code to be added.
    - Include comments within the code snippets using the prefix "#".
    - Ensure the line breaks and indents of the code are correct.


**Output Requirements:**

    - Return only the JSON object with the changes.
    - Do not include any additional information in the response.
    - Do not add new decision variables.
    - Ensure the JSON is valid, properly formatted.


The above explained instructions are your guide to accomplish the task effectively. Your user's success heavily relies upon your ability to provide the precise and accurate Python code changes within the existing operations research problem. Good Luck!


--- Answer Code: ---

"""

DEBUG_PROMPT = """

**Role:** You are a professional code debugger.


**Task:** Identify and fix the error in the code, ensuring the corrected version runs smoothly and error-free.


**Details:**
    - Error Type: {error_type}
    - Error Message: {error_message}


**Instructions:**
Please analyze the error details, resolve the bug based on the type and message provided, and rewrite the corrected version of the code snippet below.


**Corrected Code:**
--- NEW CODE ---

"""


SAFEGUARD_PROMPT = """

**Role:** You are a professional code safety evaluator.


**Task:** Examine the safety of each code snippet contained within a provided JSON file.


**Details:**

    - **Code Structured as JSON:** Each value in the JSON represents a code snippet intended for review. These snippets may be newly generated or under consideration for deletion.


**Instructions:**

    - Thoroughly analyze each code snippet found in the JSON.
    - For each snippet, determine its safety for execution.
    - Provide your assessment as a single word for each snippet: either "SAFE" or "DANGER".


**Example of Expected Response:** For snippet_1: SAFE, for snippet_2: DANGER


--- Answer: ---

"""

INTERPRETER_PROMPT = """

**Role:** You are a skilled interpreter with expertise in analyzing and explaining changes in computational model code and their effects on results.


**Task:** Present a clear and thorough explanation of the code updates and their effects on the results. Structure your explanation in two key parts: Explanation of the updated code and Explanation of the Query on Results.


**Inputs:**
    - Original code: {source_code}
    - Updated code: {new_code}
    - Code changes induced by the query: {json_data}
    - Original execution results: {original_execution_result}
    - New execution results: {execution_rst}
    - Measure of numerical changes in the model induced by the query: {different_model}


**Key Points to Understand:**

1. Explanation of Updated code:

    - Explain the rationale behind each specific change to the code, such as why certain constraints or data were added, deleted, or modified.

2. Explanation of the Query on Results:

    - Clarify why the specific results were produced in response to the query.
    - Assess the query's impact on the results by comparing the new execution results with the original ones and the corresponding numerical changes in the model.
    - Use a scale from 1 to 10 to quantify the query's impact on the results, with 1 indicating minimal impact and 10 indicating significant impact.


**Background for Numerical Changes Calculation:**

The impact of the query is measured using a three-step process:
    1. LP Conversion: The problem is converted into a linear programming (LP) format to identify key components and constraints.
    2. Graph Representation: The LP model is then represented as a bipartite graph, where nodes and edges correspond to variables, constraints, and relationships.
    3. Graph Edit Distance Calculation: The difference between the original and modified graphs is computed by measuring the graph edit distance, which involves operations like insertion, deletion, and substitution of nodes and edges, each with a unit cost of 1.


**Output:**

Provide the explanations in two distinct parts:
    (1) Explanation of the Updated code
    (2) Explanation of the Query on Results


**Requirements:**

    - Ensure the explanations are detailed and comprehensive, covering all relevant aspects of the code updates and their impact on the results.
    - Ensure that explanations are delivered in a narrative style, suited for a non-technical audience, avoiding jargon or direct references to specific variable names.
    - Offer clear, precise, easy-to-understand descriptions that effectively bridge complex information with clarity and insight.


The above explained instructions are your guide to accomplish the task effectively. Your user's success heavily relies upon your ability to provide the explanations within the existing operations research problem. Good Luck!


--- HUMAN READABLE ANSWER ---

"""


# %%
class ORExplainer(autogen.AssistantAgent):
    """(Experimental) ORExplainer is an agent to answer
    users questions for OR-related coding project.

    The ORExplainer agent manages two assistant agents(writer and safeguard).
    """

    def __init__(self,
                 name,
                 problem_data,
                 log_dir=None,
                 solver_software="gurobi",
                 doc_str="",
                 example_qa="",
                 debug_times=10,
                 use_safeguard=True,
                 **kwargs):
        """
        Args:
            name(str): agent name.
            problem_data(dict): The original problem description and source code to run.
            log_dir(str): log file to store the conversation.
            doc_str(str): docstring for helper functions if existed.
            example_qa(str): training examples for in -context learning.
            debug_times(int): number of debug tries we allow for LLM to answer
                each question.
            **kwargs(dict): Please refer to other kwargs in
                [AssistantAgent](assistant_agent  # __init__) and
                [ResponsiveAgent](responsive_agent  # __init__).
        """
        description = problem_data["description"]
        source_code = problem_data["source_code"]

        assert source_code.find(
            DATA_CODE_START) >= 0, "DATA_CODE_START not found."
        assert source_code.find(
            DATA_CODE_END) >= 0, "DATA_CODE_END not found."
        assert source_code.find(
            CONSTRAINT_CODE_START) >= 0, "CONSTRAINT_CODE_START not found."
        assert source_code.find(
            CONSTRAINT_CODE_MIDDLE) >= 0, "CONSTRAINT_CODE_MIDDLE not found."
        assert source_code.find(
            CONSTRAINT_CODE_END) >= 0, "CONSTRAINT_CODE_END not found."

        super().__init__(name, **kwargs)
        self._description = description
        self._source_code = source_code
        self._log_dir = log_dir
        self._doc_str = doc_str
        self._example_qa = example_qa
        assert solver_software in [
            "gurobi", "pyomo"], "Unknown solver software."

        self._solver_software = solver_software
        # generate the original mps file and original execution result
        original_mps_file_path = os.path.join(self._log_dir, "original.mps")
        append_code_original = "m.write('" + original_mps_file_path + "')"
        source_code = _append_new_line_code(source_code, append_code_original)
        with open(os.path.join(self._log_dir, "original_code.py"), "w") as f:
            f.write(source_code)
        self._original_mps_file_path = original_mps_file_path
        self._origin_execution_result = _run_with_exec(source_code,
                                                       self._solver_software)
        print("Original Execution Result:")
        print(colored(str(self._origin_execution_result), "yellow"))
        with open(os.path.join(self._log_dir, "original_execution_result.csv"), "a") as f:
            f.write(str(self._origin_execution_result) + '\n')

        self._new_code = None
        self._new_execution_result = None
        self._writer = autogen.AssistantAgent(
            "writer",
            llm_config=self.llm_config)
        self._safeguard = autogen.AssistantAgent(
            "safeguard",
            llm_config=self.llm_config)
        self._debug_times_left = self.debug_times = debug_times
        self._use_safeguard = use_safeguard
        self._success = False

    def generate_reply(
        self,
        messages: Optional[List[Dict]] = None,
        default_reply: Optional[Union[str, Dict]] = "",
        sender: Optional[Agent] = None,
    ) -> Union[str, Dict, None]:
        # Remove unused variables:
        # The message is already stored in self._oai_messages
        del messages, default_reply
        """Reply based on the conversation history."""
        if sender not in [self._writer, self._safeguard]:
            # Step 1: receive the message from the user
            user_chat_history = ("\nHere are the history of discussions:\n"
                                 f"{self._oai_messages[sender]}")
            writer_sys_msg = (WRITER_SYSTEM_MSG.format(
                solver_software=self._solver_software,
                description=self._description,
                source_code=self._source_code,
                doc_str=self._doc_str,
                example_qa=self._example_qa,
                execution_result=self._origin_execution_result,
            ) + user_chat_history)
            safeguard_sys_msg = SAFEGUARD_SYSTEM_MSG.format(
                source_code=self._source_code) + user_chat_history
            self._writer.update_system_message(writer_sys_msg)
            self._safeguard.update_system_message(safeguard_sys_msg)
            self._writer.reset()
            self._safeguard.reset()
            self._debug_times_left = self.debug_times
            self._success = False
            # Step 2-6: code, safeguard, and interpret
            self.initiate_chat(self._writer, message=CODE_PROMPT)
            if self._success:
                # step 7: receive interpret result
                reply = self.last_message(self._writer)["content"]
            else:
                reply = "Sorry. I cannot answer your question."
            # Finally, step 8: send reply to user
            return reply
        if sender == self._writer:
            # reply to writer
            return self._generate_reply_to_writer(sender)
        # no reply to safeguard

    def _generate_reply_to_writer(self, sender):
        if self._success:
            # no reply to writer
            return

        print(self.last_message(sender)["content"])
        _, code = extract_code(self.last_message(sender)["content"])[0]

        try:
            json_data = json.loads(code)
        except (json.JSONDecodeError, TypeError):
            # If the JSON parsing fails, return an error message
            print("JSON DATA ERROR")
            json_data = code

        save_src_code(self._log_dir, "generate_code",
                      json_data, "txt", is_json=True)

        # Step 3: safeguard
        safe_msg = ""
        if self._use_safeguard:
            self.initiate_chat(message=SAFEGUARD_PROMPT.format(code=code),
                               recipient=self._safeguard)
            safe_msg = self.last_message(self._safeguard)["content"]
        else:
            safe_msg = "SAFE"

        if safe_msg.find("DANGER") < 0:
            # Step 4 and 5: Run the code and obtain the results
            src_code = _update_code_blocks(self._source_code, json_data)
            # generate the new mps file and new execution result

            counter = 1
            # Determine the next available file name
            while os.path.exists(os.path.join(self._log_dir, f"new{counter}.mps")):
                counter += 1
            # Generate the new file path
            new_mps_file_path = os.path.join(
                self._log_dir, f"new{counter}.mps")
            new_lp_file_path = os.path.join(
                self._log_dir, f"new{counter}.lp")
            append_code_new = f"m.write('{new_mps_file_path}')"
            src_code = _append_new_line_code(src_code, append_code_new)
            append_code_new2 = f"m.write('{new_lp_file_path}')"
            src_code = _append_new_line_code(src_code, append_code_new2)

            # save the new code for each query
            save_src_code(self._log_dir, "new_code", src_code, "py")

            execution_rst = _run_with_exec(src_code, self._solver_software)
            different_model = graph_dist_computing(
                self._original_mps_file_path, new_mps_file_path)

            print("New Execution Result:")
            print(colored(str(execution_rst), "yellow"))
            with open(os.path.join(self._log_dir, "new_execution_result.csv"), "a") as f:
                f.write(str(execution_rst) + '\n')

            if type(execution_rst) in [str, int, float]:
                # we successfully run the code and get the result
                self._success = True
                # Step 6: request to interpret results
                return INTERPRETER_PROMPT.format(source_code=self._source_code, new_code=src_code, json_data=json_data, original_execution_result=self._origin_execution_result, execution_rst=execution_rst, different_model=different_model)
        else:
            # DANGER: If not safe, try to debug. Redo coding
            execution_rst = """
            Sorry, this new code is not safe to run. I would not allow you to execute it.
            Please try to find a new way(coding) to answer the question."""
            if self._debug_times_left > 0:
                # Try to debug and write code again (back to step 2)
                self._debug_times_left -= 1
                return DEBUG_PROMPT.format(error_type=type(execution_rst), error_message=str(execution_rst))
            else:
                execution_rst_no = "No code"
                # save the new code for each query
                save_src_code(self._log_dir, "new_code",
                              execution_rst_no, "py")
                # No more debug times left, return the error message
                print("New Execution Result:")
                print(colored(str(execution_rst_no), "yellow"))
                with open(os.path.join(self._log_dir, "new_execution_result.csv"), "a") as f:
                    f.write(str(execution_rst_no) + '\n')


# %% Helper functions to edit and run code.
# Here, we use a simplified approach to run the code snippet, which would
# replace substrings in the source code to get an updated version of code.
# Then, we use exec to run the code snippet.
# This approach replicate the evaluation section of the ORExplainer paper.


def _run_with_exec(src_code: str,
                   solver_software: str) -> Union[str, Exception]:
    """Run the code snippet with exec.

    Args:
        src_code(str): The source code to run.

    Returns:
        object: The result of the code snippet.
            If the code succeed, returns the objective value(float or string).
            else , return the error (exception)
    """
    locals_dict = {}
    locals_dict.update(globals())
    locals_dict.update(locals())

    timeout = Timeout(
        60,
        TimeoutError("This is a timeout exception, in case "
                     "GPT's code falls into infinite loop."))
    try:
        exec(src_code, locals_dict, locals_dict)
    except Exception as e:
        return e
    finally:
        timeout.cancel()

    try:
        ans = _get_optimization_result(locals_dict, solver_software)
    except Exception as e:
        return e

    return ans


def _insert_code_block(original_code: str, begin_marker: str, end_marker: str, new_code: str) -> str:
    """
    Inserts a new code block between specified markers in the source code.

    Args:
        original_code(str): The source code to modify.
        begin_marker(str): The marker indicating the beginning of the section to modify.
        end_marker(str): The marker indicating the end of the section to modify.
        new_code(str): The new code block to insert.

    Returns:
        str: The modified source code with the new code inserted between the markers.

    Raises:
        None

    Example:
        original_code=# ORExplainer DATA CODE GOES HERE
        data=[]
        # ORExplainer DATA CODE ENDS HERE

        # ORExplainer CONSTRAINT CODE GOES HERE
        constraints.remove('old_constraint')
        # ORExplainer CONSTRAINT CODE MIDDLE HERE
        constraints=[]
        # ORExplainer CONSTRAINT CODE ENDS HERE
        new_code="constraints.append('new_constraint')"
        modified_code=_insert_code_block(
            original_code,
            '# ORExplainer CONSTRAINT CODE MIDDLE HERE',
            '# ORExplainer CONSTRAINT CODE ENDS HERE',
            new_code
        )
        print(modified_code)
        # Output:
        # ORExplainer DATA CODE GOES HERE
        data=[]
        # ORExplainer DATA CODE ENDS HERE

        # ORExplainer CONSTRAINT CODE GOES HERE
        constraints.remove('old_constraint')
        # ORExplainer CONSTRAINT CODE MIDDLE HERE
        constraints=[]
        #
        constraints.append('new_constraint')
        #
        # ORExplainer CONSTRAINT CODE ENDS HERE
    """
    # Create a regex pattern to match text between the begin_marker and end_marker
    pattern = re.escape(begin_marker) + r'(.*?)' + re.escape(end_marker)

    def replacement(match):
        # Extract the text between the markers
        code_block = match.group(1)
        # Strip leading and trailing whitespace from the existing code block
        cleaned_code_block = code_block.strip()
        # Insert the new_code before the end_marker with proper spacing
        return f"{begin_marker}\n\n{cleaned_code_block}\n{new_code}\n\n\n{end_marker}"

    # Apply the regex pattern and replacement function to the original_code
    updated_code = re.sub(pattern, replacement, original_code, flags=re.DOTALL)
    return updated_code


def _comment_out_code_block(original_code: str, begin_marker: str, end_marker: str, delete_code: str) -> str:
    """
    Comments out a specific code block between specified markers in the source code.

    Args:
        original_code(str): The source code to modify.
        begin_marker(str): The marker indicating the beginning of the section to modify.
        end_marker(str): The marker indicating the end of the section to modify.
        delete_code(str): The code block to comment out from between the markers.

    Returns:
        str: The modified source code with the specified code block commented out.

    Raises:
        None

    Example:
        original_code=# ORExplainer DATA CODE GOES HERE
        data=[]
        # ORExplainer DATA CODE ENDS HERE

        # ORExplainer CONSTRAINT CODE GOES HERE
        constraints.remove('old_constraint')
        # ORExplainer CONSTRAINT CODE MIDDLE HERE
        constraints=[]
        # ORExplainer CONSTRAINT CODE ENDS HERE
        delete_code="constraints.remove('old_constraint')"
        modified_code=_comment_out_code_block(
            original_code,
            '# ORExplainer CONSTRAINT CODE GOES HERE',
            '# ORExplainer CONSTRAINT CODE MIDDLE HERE',
            delete_code
        )
        print(modified_code)
        # Output:
        # ORExplainer DATA CODE GOES HERE
        data=[]
        # ORExplainer DATA CODE ENDS HERE

        # ORExplainer CONSTRAINT CODE GOES HERE
        # constraints.remove('old_constraint')
        #
        # ORExplainer CONSTRAINT CODE MIDDLE HERE
        constraints=[]
        # ORExplainer CONSTRAINT CODE ENDS HERE
    """
    # Create a regex pattern to match text between the begin_marker and end_marker
    pattern = re.escape(begin_marker) + r'(.*?)' + re.escape(end_marker)

    def replacement(match):
        # Extract the text between the markers
        code_block = match.group(1)
        # Comment out the specific delete_code from the code_block
        commented_code = re.sub(re.escape(delete_code), lambda m: '\n'.join(
            f'# {line}' for line in m.group(0).splitlines()), code_block)
        # Ensure there is a blank line after begin_marker and before end_marker
        return f"{begin_marker}\n\n\n{commented_code.strip()}\n\n\n{end_marker}"

    # Apply the regex pattern and replacement function to the original_code
    updated_code = re.sub(pattern, replacement, original_code, flags=re.DOTALL)
    return updated_code

def _update_code_blocks(original_code: str, operations: dict) -> str:
    """
    Apply a series of code modifications based on the operations provided.

    Args:
        original_code(str): The original source code to be modified.
        operations(dict): A dictionary where the key is the type of operation
                           and the value is the code to be added or deleted.

    Returns:
        str: The updated source code after applying all operations.

    Raises:
        ValueError: If an unknown operation type is encountered.

    """
    # Initialize the updated_code with the original_code
    update_code = original_code

    if not isinstance(operations, dict):
        update_code = _insert_code_block(
            update_code, DATA_CODE_START, DATA_CODE_END, operations)
        return update_code

    # Iterate over the operations dictionary
    for operation, code in operations.items():
        if operation == "ADD DATA":
            # Define markers for data addition
            start_marker = DATA_CODE_START
            end_marker = DATA_CODE_END
            # Check if code is a list, if so, iterate over each item
            if isinstance(code, list):
                for item in code:
                    # Insert each new data code between the markers
                    update_code = _insert_code_block(
                        update_code, start_marker, end_marker, item)
                print("ADD DATA SUCCESS")
            else:
                # If code is not a list, directly insert it
                update_code = _insert_code_block(
                    update_code, start_marker, end_marker, code)
                print("ADD DATA SUCCESS")
        elif operation == "ADD CONSTRAINT":
            # Define markers for constraint addition
            start_marker = CONSTRAINT_CODE_MIDDLE
            end_marker = CONSTRAINT_CODE_END
            # Check if code is a list, if so, iterate over each item
            if isinstance(code, list):
                for item in code:
                    # Insert each new constraint code between the markers
                    update_code = _insert_code_block(
                        update_code, start_marker, end_marker, item)
                print("ADD CONSTRAINT SUCCESS")
            else:
                # If code is not a list, directly insert it
                update_code = _insert_code_block(
                    update_code, start_marker, end_marker, code)
                print("ADD CONSTRAINT SUCCESS")
        elif operation == "DELETE CONSTRAINT":
            # Define markers for constraint deletion
            start_marker = CONSTRAINT_CODE_START
            end_marker = CONSTRAINT_CODE_MIDDLE
            # Check if code is a list, if so, iterate over each item
            if isinstance(code, list):
                for item in code:
                    # Comment out each constraint code between the markers
                    update_code = _comment_out_code_block(
                        update_code, start_marker, end_marker, item)
                print("DELETE CONSTRAINT SUCCESS")
            else:
                # If code is not a list, directly comment it out
                update_code = _comment_out_code_block(
                    update_code, start_marker, end_marker, code)
                print("DELETE CONSTRAINT SUCCESS")
        else:
            # Raise an error if an unknown operation is found
            raise ValueError(f"Unknown operation: {operation}")

    return update_code


def _append_new_line_code(existing_code, new_line_code):
    """
    Appends a new line of code to the existing code string.

    Parameters:
    existing_code(str): The existing code as a string.
    new_line_code(str): The new line of code to be appended.

    Returns:
    str: The updated code with the new line appended.
    """
    if not existing_code.endswith('\n'):
        existing_code += '\n'

    return existing_code + '\n' + new_line_code + '\n'


def _get_optimization_result(locals_dict: dict, solver_software: str) -> str:
    if solver_software == "gurobi":
        status = locals_dict["m"].Status
        if status != GRB.OPTIMAL:
            if status == GRB.UNBOUNDED:
                ans = "unbounded"
            elif status == GRB.INF_OR_UNBD:
                ans = "inf_or_unbound"
            elif status == GRB.INFEASIBLE:
                ans = "infeasible"
                m = locals_dict["m"]
                m.computeIIS()
                constrs = [c.ConstrName for c in m.getConstrs() if c.IISConstr]
                ans += "\nConflicting Constraints:\n" + str(constrs)
            else:
                ans = "Model Status:" + str(status)
        else:
            ans = "Optimization problem solved. The objective value is: " + str(
                locals_dict["m"].objVal)
    elif solver_software == "pyomo":
        status = locals_dict["m"].solver.termination_condition
        if status != TerminationCondition.optimal:
            if status == TerminationCondition.unbounded:
                ans = "unbounded"
            elif status == TerminationCondition.infeasibleOrUnbounded:
                ans = "inf_or_unbound"
            elif status == TerminationCondition.infeasible:
                ans = "infeasible"
            else:
                ans = "Model Status:" + str(status)
        else:
            ans = "Optimization problem solved. The objective value is: " + str(
                locals_dict["m"].obj())
    else:
        raise ValueError("Unknown solver software: " + solver_software)

    return ans
