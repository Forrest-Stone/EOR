# test OR-explainer installation
import os
import argparse
import autogen
from utils import read_problem
from or_explainer.or_explainer import ORExplainer


config_file_or_env = 'OAI_CONFIG_LIST'  # modify path
config_list = autogen.config_list_from_json(
    env_or_file=config_file_or_env,
    filter_dict={
        "model": {
            "gpt-4",
            "gpt-4o",
            "gpt-3.5-turbo",
            "llama3",
            "llama3.1-70b-8k",
            "gpt-4-0314",
            "gpt-4-32k-0314",
            "gpt-4-0613",
            "gpt-4-turbo",
        }
    }
)
default_llm_config = {
    "config_list": config_list,
    "cache_seed": 42,
    "temperature": 0,
    # "timeout": 120,
}
# print(default_llm_config)


def main():
    parser = argparse.ArgumentParser(description="Run the ORExplainer.")
    parser.add_argument(
        "--benchmark",
        type=str,
        default="benchmark",
        help="The benchmark name.",
    )
    parser.add_argument(
        "--problem",
        type=str,
        default="problem_1",
        help="The problem name.",
    )
    parser.add_argument(
        "--queries",
        type=str,
        default="queries.txt",
        help="The queries to start the conversation.",
    )
    parser.add_argument(
        "--log_dir",
        type=str,
        help="The log file to store the conversation.",
    )

    args = parser.parse_args()
    benchmark = args.benchmark.lower()
    problem = args.problem.lower()

    problem_dir = os.path.join(benchmark, problem)
    if not os.path.exists(problem_dir):
        print(
            f"The problem {problem} does not exist in the benchmark {benchmark}.")
        return

    problem_data = read_problem(problem_dir)

    # creat the log dir for the problem
    log_dir = args.log_dir
    if log_dir is None:
        log_dir = f"logs/all/gpt-4-turbo/0shot/{benchmark}/{problem}"
    print(f"Log dir: {log_dir}")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # In-context learning examples.
    example_qa = """
    """

    # Define the agents
    or_explainer_commander = ORExplainer(
        name="ORExplainer example",
        problem_data=problem_data,
        log_dir=log_dir,
        example_qa=example_qa,
        debug_times=3,
        llm_config=default_llm_config,
    )

    user = autogen.UserProxyAgent(
        name="user",
        max_consecutive_auto_reply=0,
        human_input_mode="NEVER",
        code_execution_config=False,
    )

    # read the queries
    if not os.path.exists(os.path.join(problem_dir, args.queries)):
        print(f"The queries file {args.queries} does not exist.")
        return
    with open(os.path.join(problem_dir, args.queries), "r") as f:
        queries = f.readlines()
        for query in queries:
            query = query.strip()
            # start the conversation
            if len(query) > 0:
                chat_ans = user.initiate_chat(
                    or_explainer_commander,
                    message=query,
                )
                with open(os.path.join(log_dir, "conversation.log"), "a") as f:
                    f.write(f"User: {query}\n\n")
                    f.write(f"ORExplainer: {chat_ans.summary}\n\n\n")


if __name__ == "__main__":
    main()
