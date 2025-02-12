import gurobipy as gp
from gurobipy import GRB


# Parameters Section Begin
# Define model parameters
warehouses = ['A', 'B', 'C']
markets = [1, 2, 3, 4]

# Transportation costs from each warehouse to each market
transportation_cost = {
    ('A', 1): 2, ('A', 2): 3, ('A', 3): 1, ('A', 4): 2,
    ('B', 1): 3, ('B', 2): 1, ('B', 3): 2, ('B', 4): 3,
    ('C', 1): 4, ('C', 2): 2, ('C', 3): 3, ('C', 4): 1
}

# Storage costs for each warehouse
storage_cost = {
    'A': 50,
    'B': 60,
    'C': 70
}

# Market demands
demand = {
    1: 30,
    2: 20,
    3: 70,
    4: 80
}

# Maximum storage capacities for each warehouse
capacity = {
    'A': 100,
    'B': 200,
    'C': 300
}
# Parameters Section End


# ORExplainer DATA CODE GOES HERE


# ORExplainer DATA CODE ENDS HERE


# Create a Gurobi model
m = gp.Model("StorageAndDistribution")

# Decision Variables Section Begin
# Create decision variables x[i, j] for quantity shipped from warehouse i to market j
x = {(i, j): m.addVar(vtype=GRB.INTEGER, name=f"x_{i}_{j}")
     for i in warehouses for j in markets}
# Decision Variables Section End


# Objective Function Section Begin
# Set the objective function to minimize total transportation and storage costs
m.setObjective(
    gp.quicksum(
        transportation_cost[i, j] * x[i, j] for i in warehouses for j in markets
    ) + gp.quicksum(
        storage_cost[i] * gp.quicksum(x[i, j] for j in markets) for i in warehouses
    ),
    sense=GRB.MINIMIZE
)
# Objective Function Section End


# ORExplainer CONSTRAINTS CODE GOES HERE


# Constraints Section Begin
# Constraint: Meet the demand for each market
for j in markets:
    m.addConstr(
        gp.quicksum(x[i, j] for i in warehouses) == demand[j],
        name=f"Demand_{j}"
    )

# Constraint: Do not exceed the storage capacity for each warehouse
for i in warehouses:
    m.addConstr(
        gp.quicksum(x[i, j] for j in markets) <= capacity[i],
        name=f"Storage_{i}"
    )
# Constraints Section End


# ORExplainer CONSTRAINTS CODE MIDDLE HERE


# ORExplainer CONSTRAINTS CODE ENDS HERE


# Solving the Model Section Begin
# Solve the model
m.optimize()

# Output the results
if m.status == GRB.OPTIMAL:
    print(f"Minimum total cost: {m.objVal:.2f}")
    for i in warehouses:
        for j in markets:
            print(
                f"Quantity shipped from warehouse {i} to market {j}: {x[i, j].X}")
else:
    print("No optimal solution found.")
# Solving the Model Section End
