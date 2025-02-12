import gurobipy as gp
from gurobipy import GRB


# Parameters Section Begin
# Define model parameters
projects = ['ForestConservation', 'WaterResourceProtection',
            'ClimateChange', 'WildlifeConservation']

# Lower and upper bounds for each project (million dollars)
bounds = {
    'ForestConservation': (0, 5),
    'WaterResourceProtection': (0, 6),
    'ClimateChange': (0, 7),
    'WildlifeConservation': (0, 8)
}
# Parameters Section End


# ORExplainer DATA CODE GOES HERE


# ORExplainer DATA CODE ENDS HERE


# Create a Gurobi model
m = gp.Model("EnvironmentalProjectAllocation")


# Decision Variables Section Begin
# Create decision variables for investment amount in each project
x = {p: m.addVar(lb=bounds[p][0], ub=bounds[p][1],
                 vtype=GRB.INTEGER, name=f"x_{p}")
     for p in projects}
# Decision Variables Section End


# Objective Function Section Begin
# Set the objective function to maximize the total investment amount
m.setObjective(
    gp.quicksum(x[p] for p in projects),
    sense=GRB.MAXIMIZE
)
# Objective Function Section End


# ORExplainer CONSTRAINTS CODE GOES HERE


# Constraints Section Begin
# Constraint: The sum of investments in Forest Conservation and Water Resource Protection should not exceed 10 million dollars
m.addConstr(x['ForestConservation'] +
            x['WaterResourceProtection'] <= 10, name="Constraint1")

# Constraint: The sum of investments in Water Resource Protection and Climate Change should be at least 8 million dollars
m.addConstr(x['WaterResourceProtection'] +
            x['ClimateChange'] >= 8, name="Constraint2")

# Constraint: The difference between investments in Climate Change and Wildlife Conservation should be between -2 and 2 million dollars
m.addConstr(x['ClimateChange'] - x['WildlifeConservation']
            <= 2, name="Constraint3_1")
m.addConstr(x['ClimateChange'] - x['WildlifeConservation']
            >= -2, name="Constraint3_2")

# Constraint: The investment in Wildlife Conservation should be at least 3 million dollars more than the investment in Forest Conservation
m.addConstr(x['WildlifeConservation'] -
            x['ForestConservation'] >= 3, name="Constraint4")
# Constraints Section End


# ORExplainer CONSTRAINTS CODE MIDDLE HERE


# ORExplainer CONSTRAINTS CODE ENDS HERE


# Solving the Model Section Begin
# Solve the model
m.optimize()

# Output the results
if m.status == GRB.OPTIMAL:
    print(f"Maximum total investment amount: {m.ObjVal} million dollars")
    print("Optimal resource allocation:")
    for p in projects:
        print(f"{p} = {x[p].X} million dollars")
else:
    print("No optimal solution found.")
# Solving the Model Section End
