import gurobipy as gp
from gurobipy import GRB


# Parameters Section Begin
# Define model parameters
data_centers = ['A', 'B', 'C']

# Minimum and maximum number of servers for each data center
min_servers = {
    'A': 100,
    'B': 50,
    'C': 30
}
max_servers = {
    'A': 500,
    'B': 400,
    'C': 300
}

# Energy consumption per server (kW)
energy_consumption_per_server = {
    'A': 2,
    'B': 3,
    'C': 4
}

# Data storage capacity per server (PB)
storage_per_server = 0.1

# Data storage requirement (PB)
storage_requirement = 10
# Parameters Section End


# ORExplainer DATA CODE GOES HERE


# ORExplainer DATA CODE ENDS HERE


# Create a Gurobi model
m = gp.Model("DataCenterOptimization")

# Decision Variables Section Begin
# Create decision variables x[i] for number of servers in data center i
x = {i: m.addVar(vtype=GRB.INTEGER, name=f"x_{i}")
     for i in data_centers}
# Decision Variables Section End


# Objective Function Section Begin
# Set the objective function to minimize total energy consumption
m.setObjective(
    gp.quicksum(
        energy_consumption_per_server[i] * x[i]
        for i in data_centers
    ),
    sense=GRB.MINIMIZE
)
# Objective Function Section End


# ORExplainer CONSTRAINTS CODE GOES HERE


# Constraints Section Begin
# Constraint: The total number of servers must meet the data storage requirement
m.addConstr(
    gp.quicksum(x[i] for i in data_centers) *
    storage_per_server >= storage_requirement,
    name="StorageRequirement"
)

# Constraint: The number of servers in each data center must be within its operational range
for i in data_centers:
    m.addConstr(
        x[i] >= min_servers[i],
        name=f"MinServers_{i}"
    )
    m.addConstr(
        x[i] <= max_servers[i],
        name=f"MaxServers_{i}"
    )
# Constraints Section End


# ORExplainer CONSTRAINTS CODE MIDDLE HERE


# ORExplainer CONSTRAINTS CODE ENDS HERE


# Solve the Model Section Begin
# Solve the model
m.optimize()

# Output the results
if m.status == GRB.OPTIMAL:
    print(f"Minimum total energy consumption: {m.ObjVal} kW")
    for i in data_centers:
        print(f"Number of servers in data center {i}: {x[i].X}")
else:
    print("No optimal solution found.")
# Solving the Model Section End
