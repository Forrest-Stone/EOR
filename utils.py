import json
import logging
from scipy.sparse import csr_matrix
import torch
import numpy as np
import networkx as nx
import mip
import math
import bert_score
from typing import Tuple
import os
import re


def find_matched_problems(base_dir, pattern):
    """
    Finds all problem paths that match the given pattern in the base directory, sorted by the numeric part of the directory name.

    Args:
        base_dir (str): The base directory containing the problem directories.
        pattern (str): The pattern to match the problem directories.

    Returns:
        list: A list of problem paths that match the pattern, sorted by the numeric part of the directory name.
    """
    matched_problems = []
    for entry in os.listdir(base_dir):
        entry_path = os.path.join(base_dir, entry)
        if os.path.isdir(entry_path) and pattern in entry:
            problem_num = int(re.search(r'\d+', entry).group())
            matched_problems.append((entry_path, problem_num))

    matched_problems.sort(key=lambda x: x[1])
    return [path for path, _ in matched_problems]


def read_problem(problem_dir):
    problem_data = {}
    with open(os.path.join(problem_dir, "description.txt"), "r") as f:
        description = f.read()
        problem_data["description"] = description

    with open(os.path.join(problem_dir, "example_code.py"), "r") as f:
        example_code = f.read()
        problem_data["source_code"] = example_code

    return problem_data


def save_src_code(file_path, base_filename, src_code, file_extension='py', is_json=False):
    # Ensure the file path exists
    os.makedirs(file_path, exist_ok=True)

    # Initialize the file counter
    file_counter = 1

    # Construct the initial filename with the specified extension
    filename = f"{base_filename}{file_counter}.{file_extension}"
    full_path = os.path.join(file_path, filename)

    # Increment the counter until a unique filename is found
    while os.path.exists(full_path):
        file_counter += 1
        filename = f"{base_filename}{file_counter}.{file_extension}"
        full_path = os.path.join(file_path, filename)

    # Save the src_code to the file
    with open(full_path, 'w') as file:
        if is_json:
            json.dump(src_code, file, indent=4)
        else:
            file.write(src_code)

    print(f"File saved as: {filename}")


def read_mps(mps_file_path):
    """
    Read an MPS file and construct an mip.Model

    Parameters
    ----------
    mps_file_path: str
        Path to the MPS file.

    Returns
    -------
    mdl : mip.Model
        The mip model object.
    """
    if isinstance(mps_file_path, mip.Model):
        return mps_file_path
    mdl = mip.Model()
    mdl.verbose = 0
    err_msg = ""
    with open(os.devnull, "w") as null_file:  # os.devnull "/tmp/t"
        old_stdout = os.dup(1)
        os.dup2(null_file.fileno(), 1)
        try:
            mdl.read(mps_file_path)
        except Exception as e:
            err_msg = e
            # Restore the original output stream
        os.dup2(old_stdout, 1)
        os.close(old_stdout)
    if err_msg:
        raise ValueError(f"read fail {err_msg} ")
    return mdl


def index_of_y_in_x(y, x):
    assert np.isin(y, x).all()
    index = np.argsort(x)
    sorted_x = x[index]
    sorted_index = np.searchsorted(sorted_x, y)
    return index[sorted_index]


def read_mps_and_drop_singleton(mps_file_path: str) -> mip.Model:
    """Read a model from an MPS file and format the constraints"""
    mdl = read_mps(mps_file_path)

    # convert model sense
    if mdl.sense == 'Maximize':
        mdl.sense = 'MAX'
    if mdl.sense == 'Minimize':
        mdl.sense = 'MIN'
    if mdl.sense == 'MAX':
        mdl.objective = mdl.objective * -1
        mdl.sense = 'MIN'

    # Creat new model
    cp_mdl = mip.Model(mdl.name, mdl.sense)

    # adding variables
    for v in mdl.vars:
        cp_mdl.add_var(name=v.name, lb=v.lb, ub=v.ub,
                       obj=v.obj, var_type=v.var_type)

    # adding constraints
    for c in mdl.constrs:
        orig_expr = c.expr
        nvar_in_c = len(orig_expr.expr.items())
        if nvar_in_c == 1:
            var, value = list(orig_expr.expr.items()).pop()
            bound = -orig_expr.const / value
            sense = orig_expr.sense
            if value < 0:
                if sense == '<':
                    sense = '>'
                elif sense == '>':
                    sense = '<'
            new_var = cp_mdl.var_by_name(var.name)
            if sense == '>':
                new_var.lb = max(new_var.lb, bound)
            elif sense == '<':
                new_var.ub = min(new_var.ub, bound)
            else:
                assert sense == '=', sense
                new_var.lb = new_var.ub = bound  # what if conflict? e.g., x=1, x=2
        elif nvar_in_c == 0:
            raise ValueError('Coefficient Error!')
        else:
            priority = c.priority
            if orig_expr.sense == '>':
                mult = -1
            else:
                mult = 1
            expr = mip.LinExpr(const=mult * orig_expr.const, sense='<')
            for (var, value) in orig_expr.expr.items():
                expr.add_term(cp_mdl.var_by_name(var.name), mult * value)
            cp_mdl.add_constr(lin_expr=expr, name=c.name, priority=priority)

    # setting objective function"s constant
    cp_mdl.objective_const = mdl.objective_const
    return cp_mdl


def print_mdl(mdl):
    logging.info("=== mdl is ")
    logging.info("obj:", mdl.objective)
    logging.info("s.t.:")
    for constr in mdl.constrs:
        logging.info(constr)
    for var in mdl.vars:
        logging.info("the bound of", var, "is", var.lb, var.ub)


def parse_mdl(mdl: mip.Model, only_names: bool = False) -> Tuple[np.ndarray, np.ndarray, csr_matrix, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    ref: https://stackoverflow.com/questions/73266140/how-to-read-an-mps-file-for-scipy-milp
    Reads a .mps and saves all the data of the MILP:

    min c^T * x

    s.t. b_l <= A*x <= b_u
          lb <=   x <= ub
    """
    # model parameters
    num_vars = len(mdl.vars)
    num_cons = len(mdl.constrs)

    # variable types and bounds
    # If no bounds are specified, CPLEX will automatically set the lower bound to 0 and the upper bound to +∞.
    lb = np.zeros(num_vars)
    ub = np.empty(num_vars)
    for i, var in enumerate(mdl.vars):
        assert var.idx == i
        lb[i] = var.lb
        ub[i] = var.ub
        # assert var.var_type == 'C'

    # objective
    var_nms = np.array([var.name for var in mdl.vars])
    con_nms = np.array([con.name for con in mdl.constrs])
    if only_names:
        return con_nms, var_nms
    var_nm_to_c = {}
    for var, weight in mdl.objective.expr.items():
        var_nm_to_c[var.name] = weight
    c = np.vectorize(lambda var: var_nm_to_c.get(var, 0))(
        var_nms).astype('float64')
    if mdl.sense != "MIN":
        c *= -1.0

    # constraint coefficient matrix
    b_l = -np.inf * np.ones(num_cons)
    b_u = np.inf * np.ones(num_cons)
    for i, con in enumerate(mdl.constrs):
        assert con.idx == i
        if con.expr.sense == "=":
            b_l[i], b_u[i] = con.rhs, con.rhs
        elif con.expr.sense == "<":
            b_u[i] = con.rhs
        elif con.expr.sense == ">":
            b_l[i] = con.rhs
        elif con.expr.sense == 'R':  # range constraint
            assert False, "not implemented yet"
        else:
            raise ValueError(f'ERROR: unkn {con.expr.sense}')

    row_ind = []
    col_ind = []
    data = []
    for i, con in enumerate(mdl.constrs):
        expr = con.expr.expr
        for var, coeff in expr.items():
            row_ind.append(con.name)
            col_ind.append(var.name)
            data.append(coeff)
    row_ind = index_of_y_in_x(row_ind, con_nms)
    col_ind = index_of_y_in_x(col_ind, var_nms)
    A = csr_matrix((data, (row_ind, col_ind)), shape=(num_cons, num_vars))
    b_u[b_u > 1e308] = np.inf
    b_l[b_l < -1e308] = -np.inf
    ub[ub > 1e308] = np.inf
    lb[lb < -1e308] = -np.inf
    lb[np.isclose(lb, -1e10)] = -np.inf
    return c, b_l, A, b_u, lb, ub, con_nms, var_nms


def subst_cost(a1, a2, G1=None, G2=None):
    if G1 is not None and G2 is not None:
        if isinstance(a1, tuple) and isinstance(a2, tuple):
            a1 = G1.edges[a1]
            a2 = G2.edges[a2]
        else:
            a1 = G1.nodes[a1]
            a2 = G2.nodes[a2]
    if a1.keys() != a2.keys():
        return np.inf
    mismatch = 0
    for k in a1:
        if k == "expltn":
            with torch.no_grad():
                P, R, F1 = bert_score.score(
                    [a1[k]],
                    [a2[k]],
                    lang="en",
                    verbose=False,
                    # model_type="microsoft/deberta-large-mnli",
                    num_layers=18,
                )
                delta = (1 - torch.clip(F1.mean(), min=-1, max=1).item()) / 2
            mismatch += delta
            assert -1e-3 < delta < 1 + 1e-3
        if a1[k] != a2[k]:
            mismatch += 1
    return mismatch


def del_or_ins_cost(attr, G=None):
    if G is not None:
        if isinstance(attr, tuple):
            attr = G.edges[attr]
        else:
            attr = G.nodes[attr]
    return len(attr)


def read_mps_and_build_graph(mps_fn: str, verbose: bool = False) -> nx.Graph():
    mdl = read_mps_and_drop_singleton(mps_fn)
    if mdl == 'Coefficient Error':
        raise ValueError('Coefficient Error!')
    else:
        if verbose:
            print_mdl(mdl)
        c, b_l, A, b_u, lb, ub, con_nms, var_nms = parse_mdl(mdl)
        A = A.tocoo()
        G = nx.Graph()
        nvar = len(var_nms)
        ncon = len(con_nms)
        for i in range(ncon):
            G.add_node(con_nms[i], low=b_l[i], up=b_u[i], )
        for j in range(nvar):
            G.add_node(var_nms[j], low=lb[j], up=ub[j], c=c[j])
        for i, j, d in zip(A.row, A.col, A.data):
            G.add_edge(con_nms[i], var_nms[j], A=d)
        return G


def get_graph_size(G):
    sz = 0
    for nds in G.nodes:
        sz += len(G.nodes[nds])
    for eds in G.edges:
        sz += len(G.edges[eds])
    return sz


def zero_cost_subst_filter(vertex_path, G1, G2):
    filtered_vertex_path = []
    for i in range(len(vertex_path)):
        # assuming vertex_path[i] is a tuple of two nodes
        node1, node2 = vertex_path[i]
        if node1 is None or node2 is None:
            # Insertion or deletion operation
            filtered_vertex_path.append((node1, node2))
        elif subst_cost(node1, node2, G1, G2) != 0:
            # Non-zero cost substitution operation
            filtered_vertex_path.append((node1, node2))
    return filtered_vertex_path


def zero_cost_subst_filter_edge(edge_path, G1, G2):
    filtered_edge_path = []
    for i in range(len(edge_path)):
        # assuming edge_path[i] is a tuple of two edges
        edge1, edge2 = edge_path[i]
        if edge1 is None or edge2 is None:
            # Insertion or deletion operation
            filtered_edge_path.append((edge1, edge2))
        elif subst_cost(edge1, edge2, G1, G2) != 0:
            # Non-zero cost substitution operation
            filtered_edge_path.append((edge1, edge2))
    return filtered_edge_path


def extract_path_info(path, G1, G2):
    path_info = []
    for i in range(len(path)):
        node1, node2 = path[i]
        info = {}
        if node1 is None:
            info['operation'] = 'insert'
            info['node'] = node2
            info['cost'] = del_or_ins_cost(node2, G2)
        elif node2 is None:
            info['operation'] = 'delete'
            info['node'] = node1
            info['cost'] = del_or_ins_cost(node1, G1)
        else:
            info['operation'] = 'substitute'
            info['node1'] = node1
            info['node2'] = node2
            info['cost'] = subst_cost(node1, node2, G1, G2)
        path_info.append(info)
    return path_info


def print_edge_path_info(edge_path, G1, G2):
    path_info = extract_path_info(edge_path, G1, G2)
    for info in path_info:
        if info['operation'] == 'insert':
            logging.info(
                f"Insert edge {info['edge']} with cost: {info['cost']}")
        elif info['operation'] == 'delete':
            logging.info(
                f"Delete edge {info['edge']} with cost: {info['cost']}")
        else:  # info['operation'] == 'substitute'
            logging.info(
                f"Substitute edge {info['edge1']} with edge {info['edge2']} with cost: {info['cost']}")


def graph_dist_computing(ref_fn: str, hyp_fn: str, verbose=False):
    """
    Construct a graph based on the node information of variables and constraints, and calculate the distance between nodes.

    Parameters
    ----------
    ref_fn : str
        Path to the reference MPS file
    hyp_fn : str
        Path to the hypothesis MPS file
    verbose : bool
        Whether to output detailed logs

    Returns
    -------
    dict : float
        The distance between the two models. (The smaller the value, the more similar the code)
    """
    try:
        G_ref = read_mps_and_build_graph(ref_fn, verbose=verbose)
    except Exception as e:
        logging.error(f'Fail graph: {ref_fn} {e} \n')
        return 100

    try:
        G_hyp = read_mps_and_build_graph(hyp_fn, verbose=verbose)
    except Exception as e:
        logging.error(f'Fail graph: {hyp_fn} {e} \n')
        return 100

    # computing graph edge distance
    dist = np.inf
    try:
        for _, _, dist_now in nx.algorithms.similarity.optimize_edit_paths(
                G_ref, G_hyp,
                node_subst_cost=subst_cost,
                node_del_cost=del_or_ins_cost,
                node_ins_cost=del_or_ins_cost,
                edge_subst_cost=subst_cost,
                edge_del_cost=del_or_ins_cost,
                edge_ins_cost=del_or_ins_cost,
                timeout=300,
        ):
            if dist_now < dist:
                dist = dist_now
        gsize = max(get_graph_size(G_ref), get_graph_size(G_hyp))
        dist /= gsize  # normalize
    except Exception as e:
        logging.error(e)

    return dist


def gen_obj_val(fn):
    if isinstance(fn, dict):
        return fn
    else:
        # return ORModelTools.solve(filename=fn)
        return fn


def solution_dist_computing(ref_fn: str, hyp_fn: str):
    """
    Calculate the distance between the solution results of two models
    """
    # solve
    try:
        obj_val1 = gen_obj_val(ref_fn)
    except Exception:
        obj_val1 = {
            "status": "UNKNOWN",
            "objective_value": 0
        }

    try:
        obj_val2 = gen_obj_val(hyp_fn)
    except Exception:
        return 1, float("inf")

    if obj_val1["status"] == "OPTIMAL":
        if obj_val2["status"] == "OPTIMAL":
            # Placeholder, to prevent division by zero
            eps = math.exp(-12)
            dist = abs((obj_val1["objective_value"] - obj_val2["objective_value"])
                       / (obj_val2["objective_value"] + eps))
            return min(dist, 1), abs((obj_val1["objective_value"] - obj_val2["objective_value"]))
        else:
            return 1, float("inf")
    else:
        if obj_val2["status"] == "OPTIMAL":
            return 1, float("inf")
        else:
            return 0, 0
