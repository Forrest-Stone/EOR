import gurobipy as gp
from gurobipy import GRB


# Parameters Section Begin
# List of universities
universities = ['A', 'B', 'C', 'D']

# Resource demand and supply
# Resource demand
resource_demand = {
    'A': 200,
    'B': 300,
    'C': 250,
    'D': 250}

# Resource supply
resource_supply = {
    'A': 300,
    'B': 200,
    'C': 250,
    'D': 250
}

# Distance matrix
distance_matrix = {
    'A': {'A': 0, 'B': 5, 'C': 3, 'D': 4},
    'B': {'A': 5, 'B': 0, 'C': 2, 'D': 1},
    'C': {'A': 3, 'B': 2, 'C': 0, 'D': 6},
    'D': {'A': 4, 'B': 1, 'C': 6, 'D': 0},
}
# Parameters Section End


# ORExplainer DATA CODE GOES HERE


# ORExplainer DATA CODE ENDS HERE


# Create a Gurobi model
m = gp.Model("LibraryResourceSharing")

# Decision Variables Section Begin
# Add decision variables for the quantity of resources provided by university i to university j
x = {(i, j): m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"x_{i}_{j}")
     for i in universities for j in universities}
# Decision Variables Section End


# Objective Function Section Begin
# Objective function: Minimize total exchange cost
m.setObjective(
    gp.quicksum(
        distance_matrix[i][j] * x[(i, j)]
        for i in universities for j in universities
    ),
    sense=GRB.MINIMIZE
)
# Objective Function Section End


# ORExplainer CONSTRAINTS CODE GOES HERE


# Constraints Section Begin
# Constraint: Resource demands of each university must be met
for j in universities:
    m.addConstr(
        gp.quicksum(x[(i, j)] for i in universities) == resource_demand[j],
        name=f"Demand_{j}"
    )

# Constraint: Resource supply provided by each university must not exceed its available supply quantity
for i in universities:
    m.addConstr(
        gp.quicksum(x[(i, j)] for j in universities) <= resource_supply[i],
        name=f"Supply_{i}"
    )
# Constraints Section End


# ORExplainer CONSTRAINTS CODE MIDDLE HERE


# ORExplainer CONSTRAINTS CODE ENDS HERE


# Solving the Model Section Begin
# Solve the model
m.optimize()

# Output the results
if m.status == GRB.OPTIMAL:
    print("Minimum total exchange cost:", m.ObjVal)
    for i in universities:
        for j in universities:
            if x[(i, j)].X > 0:
                print(
                    f"University {i} provides {x[(i, j)].X} resources to University {j}")
else:
    print("No optimal solution found.")
# Solving the Model Section End
