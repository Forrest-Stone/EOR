import gurobipy as gp
from gurobipy import GRB


# Parameters Section Begin
# Define model parameters
communities = ['x1', 'x2', 'x3', 'x4']

# The unit cost of each activity
unit_cost = {
    'x1': 50,
    'x2': 100,
    'x3': 200,
    'x4': 300
}

# The limits for the number of activities in each community
activity_bounds = {
    'x1': (0, 500),
    'x2': (0, 400),
    'x3': (0, 600),
    'x4': (0, 700)
}
# Parameters Section End


# ORExplainer DATA CODE GOES HERE


# ORExplainer DATA CODE ENDS HERE


# Create a Gurobi model
m = gp.Model("OnlineEducationPlatformOptimization")

# Decision Variables Section Begin
# Create decision variables for number of activities in each community
x = {c: m.addVar(lb=activity_bounds[c][0], ub=activity_bounds[c]
                 [1], vtype=GRB.INTEGER, name=c) for c in communities}
# Decision Variables Section End

# Objective Function Section Begin
# Set the objective function to minimize total cost
m.setObjective(gp.quicksum(unit_cost[c] * x[c]
                           for c in communities), GRB.MINIMIZE)
# Objective Function Section End


# ORExplainer CONSTRAINTS CODE GOES HERE


# Constraints Section Begin
# Constraint: The total number of activities in communities x1 and x2 cannot exceed 500
m.addConstr(x['x1'] + x['x2'] <= 500, "Constraint1")

# Constraint: The total number of activities in communities x2 and x3 must be at least 300
m.addConstr(x['x2'] + x['x3'] >= 300, "Constraint2")

# Constraint: The difference in activities between communities x3 and x4 cannot exceed 100
m.addConstr(x['x3'] - x['x4'] <= 100, "Constraint3")
m.addConstr(x['x3'] - x['x4'] >= -100, "Constraint4")

# Constraint: The difference in activities between communities x4 and x1 must be at least 50
m.addConstr(x['x4'] - x['x1'] >= 50, "Constraint5")
# Constraints Section End


# ORExplainer CONSTRAINTS CODE MIDDLE HERE


# ORExplainer CONSTRAINTS CODE ENDS HERE


# Solving the Model Section Begin
# Solve the model
m.optimize()

# Output the results
if m.status == GRB.OPTIMAL:
    print(f"Minimum total cost: ${round(m.objVal)}")
    print("Optimal resource allocation:")
    for c in communities:
        print(f"Number of activities for community {c}: {x[c].X}")
else:
    print("No optimal solution found.")
# Solving the Model Section End
