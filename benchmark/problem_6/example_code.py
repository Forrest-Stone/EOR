import gurobipy as gp
from gurobipy import GRB


# Parameters Section Begin
# Define model parameters
energy_sources = ['Coal', 'NaturalGas', 'Wind']

# Capacities of each energy source (in MW)
capacities = {
    'Coal': 5000,
    'NaturalGas': 4000,
    'Wind': 3000
}

# Unit costs of each energy source (in CNY/MWh)
unit_costs = {
    'Coal': 20,
    'NaturalGas': 25,
    'Wind': 15
}

# Total energy demand of the city (in MWh)
total_demand = 8000
# Parameters Section End


# ORExplainer DATA CODE GOES HERE


# ORExplainer DATA CODE ENDS HERE


# Create a Gurobi model
m = gp.Model("EnergyOptimization")

# Decision Variables Section Begin
# Create decision variables x[i] for supply of energy source i
x = {i: m.addVar(lb=0, ub=capacities[i], name=f"x_{i}")
     for i in energy_sources}
# Decision Variables Section End

# Objective Function Section Begin
# Set the objective function to minimize total cost
m.setObjective(
    gp.quicksum(unit_costs[i] * x[i] for i in energy_sources),
    sense=GRB.MINIMIZE
)
# Objective Function Section End


# ORExplainer CONSTRAINTS CODE GOES HERE


# Constraints Section Begin
# Constraint: Total supply meets the city's demand
m.addConstr(gp.quicksum(x[i] for i in energy_sources)
            == total_demand, name="TotalDemand")

# Constraint: The supply of wind power accounts for at least 20% of the total supply
m.addConstr(x['Wind'] >= 0.2 * gp.quicksum(x[i]
            for i in energy_sources), name="WindShare")
# Constraints Section End


# ORExplainer CONSTRAINTS CODE MIDDLE HERE


# ORExplainer CONSTRAINTS CODE ENDS HERE


# Solving the Model Section Begin
# Solve the model
m.optimize()

# Output the results
if m.status == GRB.OPTIMAL:
    print(f"Minimum total cost: {m.ObjVal} CNY")
    for i in energy_sources:
        print(f"Supply of {i}: {x[i].X} MW")
else:
    print("No optimal solution found.")
# Solving the Model Section End
