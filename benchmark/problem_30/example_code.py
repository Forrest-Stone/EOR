import gurobipy as gp
from gurobipy import GRB


# Parameters Section Begin
# Define model parameters
# List of ship types
ship_types = ['A', 'B', 'C']

# Operating costs for each ship type
operating_costs = {
    'A': 30000,
    'B': 15000,
    'C': 7000
}

# Cargo capacities for each ship type
cargo_capacities = {
    'A': 1000,
    'B': 500,
    'C': 200
}

# Cargo demand to be met
demand = 20000

# Maximum number of ships that can be operated
max_ships = 60

# Maximum number of ships per type
max_per_type = {
    'A': 20,
    'B': 30,
    'C': 40
}
# Parameters Section End


# ORExplainer DATA CODE GOES HERE


# ORExplainer DATA CODE ENDS HERE


# Create a Gurobi model
m = gp.Model("CargoShipOptimization")

# Decision Variables Section Begin
# Create decision variables for the number of ships of each type
ship_vars = {ship: m.addVar(vtype=GRB.INTEGER, name=f"ship_{ship}",
                            lb=0, ub=max_per_type[ship]) for ship in ship_types}
# Decision Variables Section End


# Objective Function Section Begin
# Set the objective function to minimize total operating cost
m.setObjective(
    gp.quicksum(operating_costs[ship] * ship_vars[ship]
                for ship in ship_types),
    sense=GRB.MINIMIZE
)
# Objective Function Section End


# ORExplainer CONSTRAINTS CODE GOES HERE


# Constraints Section Begin
# Constraint: Meet the cargo demand
m.addConstr(
    gp.quicksum(cargo_capacities[ship] * ship_vars[ship]
                for ship in ship_types) >= demand,
    name="CargoDemandConstraint"
)

# Constraint: Total number of ships must not exceed the maximum
m.addConstr(
    gp.quicksum(ship_vars[ship] for ship in ship_types) <= max_ships,
    name="TotalShipsConstraint"
)
# Constraints Section End


# ORExplainer CONSTRAINTS CODE MIDDLE HERE


# ORExplainer CONSTRAINTS CODE ENDS HERE


# Solving the Model Section Begin
# Solve the model
m.optimize()

# Output the results
if m.status == GRB.OPTIMAL:
    print(f"Minimized total operating cost: {round(m.ObjVal)}")
    for ship in ship_types:
        print(f"Number of Type {ship} ships: {ship_vars[ship].X}")
else:
    print("No optimal solution found.")
# Solving the Model Section End
