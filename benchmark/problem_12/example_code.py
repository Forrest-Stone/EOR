import gurobipy as gp
from gurobipy import GRB


# Parameters Section Begin
# Define model parameters
projects = ['A', 'B', 'C', 'D']

# Expected returns (in $10,000)
expected_returns = {
    'A': 100,
    'B': 150,
    'C': 200,
    'D': 250
}

# Funding requirement (in $10,000)
funding_requirements = {
    'A': 50,
    'B': 80,
    'C': 100,
    'D': 120
}

# Manpower requirement
manpower_requirements = {
    'A': 10,
    'B': 20,
    'C': 30,
    'D': 40
}
# Parameters Section End


# ORExplainer DATA CODE GOES HERE


# ORExplainer DATA CODE ENDS HERE


# Create a Gurobi model
m = gp.Model("StartupResourceAllocation")

# Decision Variables Section Begin
# Create binary decision variables y[p] for whether project p is selected
y = {p: m.addVar(vtype=GRB.BINARY, name=f"y_{p}") for p in projects}
# Decision Variables Section End


# Objective Function Section Begin
# Set the objective function to maximize total returns
m.setObjective(
    gp.quicksum(expected_returns[p] * y[p] for p in projects),
    sense=GRB.MAXIMIZE
)
# Objective Function Section End


# ORExplainer CONSTRAINTS CODE GOES HERE


# Constraints Section Begin
# Constraint: The total funding must be at least $200,000
m.addConstr(
    gp.quicksum(funding_requirements[p] * y[p] for p in projects) >= 200,
    name="TotalFundingConstraint"
)

# Constraint: The total manpower must not exceed 80 people
m.addConstr(
    gp.quicksum(manpower_requirements[p] * y[p] for p in projects) <= 80,
    name="TotalManpowerConstraint"
)
# Constraints Section End


# ORExplainer CONSTRAINTS CODE MIDDLE HERE


# ORExplainer CONSTRAINTS CODE ENDS HERE


# Solving the Model Section Begin
# Solve the model
m.optimize()

# Output the results
if m.status == GRB.OPTIMAL:
    print(f"Maximized total returns: ${m.ObjVal / 10000:.2f} million")
    print("Selected projects:")
    for p in projects:
        if y[p].X > 0.5:  # If y_p is greater than 0.5, consider the project as selected
            print(f"Project {p}")
else:
    print("No optimal solution found.")
# Solving the Model Section End
