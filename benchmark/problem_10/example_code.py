import gurobipy as gp
from gurobipy import GRB


# Parameters Section Begin
# Define model parameters
areas = ['A', 'B', 'C', 'D']

# Construction costs (in thousands)
costs = {
    'A': 100,
    'B': 150,
    'C': 200,
    'D': 250
}

# Expected benefits (in thousands)
benefits = {
    'A': 70,
    'B': 120,
    'C': 160,
    'D': 200
}

# Budget (in thousands)
budget = 1000
# Parameters Section End


# ORExplainer DATA CODE GOES HERE


# ORExplainer DATA CODE ENDS HERE


# Create a Gurobi model
m = gp.Model("ParkConstructionOptimization")

# Decision Variables Section Begin
# Create decision variables x[area] for park construction in each area
x = {area: m.addVar(vtype=GRB.BINARY, name=f"x_{area}") for area in areas}
# Decision Variables Section End

# Objective Function Section Begin
# Set the objective function to maximize total expected benefits
m.setObjective(
    gp.quicksum(benefits[area] * x[area] for area in areas),
    sense=GRB.MAXIMIZE
)
# Objective Function Section End


# ORExplainer CONSTRAINTS CODE GOES HERE


# Constraints Section Begin
# Constraint: The construction costs for each area cannot exceed the budget
m.addConstr(gp.quicksum(costs[area] * x[area]
            for area in areas) <= budget, name="BudgetConstraint")

# Constraint: The difference in the number of parks between any two adjacent areas cannot exceed 1
for i in range(len(areas)):
    m.addConstr(x[areas[i]] - x[areas[(i+1) % len(areas)]] <= 1,
                name=f"AdjacentDifference_{areas[i]}_{areas[(i+1) % len(areas)]}")
    m.addConstr(x[areas[(i+1) % len(areas)]] - x[areas[i]] <= 1,
                name=f"AdjacentDifference_{areas[(i+1) % len(areas)]}_{areas[i]}")
# Constraints Section End


# ORExplainer CONSTRAINTS CODE MIDDLE HERE


# ORExplainer CONSTRAINTS CODE ENDS HERE


# Solving the Model Section Begin
# Solve the model
m.optimize()

# Output the results
if m.status == GRB.OPTIMAL:
    print(f"Optimal solution found. Total expected benefits: {m.ObjVal}")
    for area in areas:
        if x[area].X > 0.5:  # Since x[area] is a binary variable, if it is greater than 0.5, it is considered that a park is built in that area
            print(f"Build a park in area {area}")
else:
    print("No optimal solution found.")
# Solving the Model Section End
