import gurobipy as gp
from gurobipy import GRB


# Parameters Section Begin
# Define model parameters
drugs = ['A', 'B']
raw_materials = [1, 2]

# Drug requirements for raw materials
drug_requirements = {
    'A': {1: 3, 2: 2},
    'B': {1: 2, 2: 5}
}

# Available raw materials
available_raw_materials = {
    1: 180,
    2: 200
}

# Production cost per unit (dollars/unit)
production_cost = {
    'A': 20,
    'B': 30
}

# Selling price per unit (dollars/unit)
selling_price = {
    'A': 50,
    'B': 70
}

# Minimum production requirements
min_production = {
    'A': 30,
    'B': 20
}

# Maximum production capacities
max_production = {
    'A': 60,
    'B': 40
}
# Parameters Section End


# ORExplainer DATA CODE GOES HERE


# ORExplainer DATA CODE ENDS HERE


# Create a Gurobi model
m = gp.Model("DrugProductionOptimization")

# Decision Variables Section Begin
# Create decision variables for the production quantity of each drug
production_quantity = {d: m.addVar(
    lb=0, name=f"production_{d}") for d in drugs}
# Decision Variables Section End

# Objective Function Section Begin
# Set the objective function to maximize total profit
m.setObjective(
    gp.quicksum((selling_price[d] - production_cost[d])
                * production_quantity[d] for d in drugs),
    sense=GRB.MAXIMIZE
)
# Objective Function Section End


# ORExplainer CONSTRAINTS CODE GOES HERE


# Constraints Section Begin
# Constraint: Raw material usage constraints
for rm in raw_materials:
    m.addConstr(
        gp.quicksum(drug_requirements[d][rm] * production_quantity[d]
                    for d in drugs) <= available_raw_materials[rm],
        name=f"RawMaterialConstraint_{rm}"
    )

# Constraint: Minimum production requirements
for d in drugs:
    m.addConstr(
        production_quantity[d] >= min_production[d],
        name=f"MinProductionConstraint_{d}"
    )

# Constraint: Maximum production capacities
for d in drugs:
    m.addConstr(
        production_quantity[d] <= max_production[d],
        name=f"MaxProductionConstraint_{d}"
    )
# Constraints Section End


# ORExplainer CONSTRAINTS CODE MIDDLE HERE


# ORExplainer CONSTRAINTS CODE ENDS HERE


# Solving the Model Section Begin
# Solve the model
m.optimize()

# Output the results
if m.status == GRB.OPTIMAL:
    print(f"Maximized total profit: ${m.ObjVal}")
    for d in drugs:
        print(
            f"Optimal production quantity for drug {d}: {production_quantity[d].X} units")
else:
    print("No optimal solution found.")
# Solving the Model Section End
