"""A simplified implementation of ORExplainer framework with AutoGen.

The ORExplainer agent will interact with LLM-based agents.


"""
import os
from typing import Dict, List, Optional, Union

import autogen
from autogen.agentchat.agent import Agent
from autogen.code_utils import extract_code
from eventlet.timeout import Timeout
from termcolor import colored
from utils import save_src_code

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


**Task:** You are provided with the original problem description and the correct code for an operations research problem. Based on the user's query, update the code accordingly.


**Output:**
Return the updated code to answer the user's question.

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


# %% Prompt for ORExplainer

CODE_PROMPT = """

Answer Code:

"""

DEBUG_PROMPT = """

**Role:** You are a professional code debugger.


**Task:** Identify and fix the error in the code, ensuring the corrected version runs smoothly and error-free.

**Details:**
    - Error Type: {error_type}
    - Error Message: {error_message}


**Corrected Code:**
--- NEW CODE ---

"""


SAFEGUARD_PROMPT = """

**Role:** You are a professional code safety evaluator.


**Task:** Assess the safety of the code snippet.


**Details:**

    - Code: {code}


--- Answer: ---
SAFE or DANGER

"""

INTERPRETER_PROMPT = """

**Role:** You are a skilled interpreter with expertise in analyzing and explaining changes in computational model code and their effects on results.


**Task:** Present a clear and thorough explanation of the code updates and their effects on the results.


**Inputs:**
    - New execution results: {execution_rst}
    - Original execution results: {original_execution_result}


**Output:**
Return the clear and concise explanations.


--- HUMAN READABLE ANSWER - --
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
                 debug_times=3,
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

        super().__init__(name, **kwargs)
        self._description = description
        self._source_code = source_code
        self._log_dir = log_dir
        self._doc_str = doc_str
        self._example_qa = example_qa
        assert solver_software in [
            "gurobi", "pyomo"], "Unknown solver software."

        self._solver_software = solver_software
        # generate the original execution result
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

        save_src_code(self._log_dir, "generate_code",
                      code, "txt", is_json=True)

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
            src_code = code

            # save the new code for each query
            save_src_code(self._log_dir, "new_code", src_code, "py")
            execution_rst = _run_with_exec(src_code, self._solver_software)

            print("New Execution Result:")
            print(colored(str(execution_rst), "yellow"))
            with open(os.path.join(self._log_dir, "new_execution_result.csv"), "a") as f:
                f.write(str(execution_rst) + '\n')

            if type(execution_rst) in [str, int, float]:
                # we successfully run the code and get the result
                self._success = True
                # Step 6: request to interpret results
                return INTERPRETER_PROMPT.format(original_execution_result=self._origin_execution_result, execution_rst=execution_rst)
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
