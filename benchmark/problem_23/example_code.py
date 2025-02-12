import gurobipy as gp
from gurobipy import GRB


# Parameters Section Begin
# Define model parameters
production_lines = ['x1', 'x2', 'x3', 'x4']

# Operating costs per hour for each production line
operating_costs = {
    'x1': 50,
    'x2': 100,
    'x3': 200,
    'x4': 300
}

# Maximum operating time limits for each production line (hours)
max_operating_time = {
    'x1': 700,
    'x2': 600,
    'x3': 800,
    'x4': 900
}
# Parameters Section End


# ORExplainer DATA CODE GOES HERE


# ORExplainer DATA CODE ENDS HERE


# Create a Gurobi model
m = gp.Model("SteelMillOptimization")

# Decision Variables Section Begin
# Create decision variables for operating times (hours)
x = {i: m.addVar(vtype=GRB.INTEGER, name=f"x_{i}", lb=0,
                 ub=max_operating_time[i])
     for i in production_lines}
# Decision Variables Section End

# Objective Function Section Begin
# Set the objective function to minimize the total operating cost
m.setObjective(
    gp.quicksum(operating_costs[i] * x[i] for i in production_lines),
    sense=GRB.MINIMIZE
)
# Objective Function Section End


# ORExplainer CONSTRAINTS CODE GOES HERE


# Constraints Section Begin
# Constraint: The total operating time of x1 and x2 cannot exceed 500 hours
m.addConstr(x['x1'] + x['x2'] <= 500, name="Constraint1")

# Constraint: The total operating time of x2 and x3 must be at least 300 hours
m.addConstr(x['x2'] + x['x3'] >= 300, name="Constraint2")

# Constraint: The difference in operating time between x3 and x4 cannot exceed 100 hours
m.addConstr(x['x3'] - x['x4'] <= 100, name="Constraint3a")
m.addConstr(x['x4'] - x['x3'] <= 100, name="Constraint3b")

# Constraint: The difference in operating time between x4 and x1 must be at least 50 hours
m.addConstr(x['x4'] - x['x1'] >= 50, name="Constraint4")
# Constraints Section End


# ORExplainer CONSTRAINTS CODE MIDDLE HERE


# ORExplainer CONSTRAINTS CODE ENDS HERE


# Solving the Model Section Begin
# Solve the model
m.optimize()

# Output the results
if m.status == GRB.OPTIMAL:
    print(f"Minimum total cost: {round(m.ObjVal)} dollars")
    print("Optimal production line operating times (hours):")
    for i in production_lines:
        print(f"{i} = {x[i].X}")
else:
    print("No optimal solution found.")
# Solving the Model Section End
