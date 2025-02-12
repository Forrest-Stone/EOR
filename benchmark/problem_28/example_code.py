import gurobipy as gp
from gurobipy import GRB


# Parameters Section Begin
# Define model parameters
aircraft_types = ['A', 'B']

# Passenger capacity per aircraft type
passenger_capacity = {
    'A': 500,
    'B': 200
}

# Operating cost per aircraft type (dollars)
operating_cost_per_aircraft = {
    'A': 10000,
    'B': 5000
}

# Minimum passenger demand
min_passenger_demand = 10000

# Maximum number of aircraft
max_aircraft_count = 50
# Parameters Section End


# ORExplainer DATA CODE GOES HERE


# ORExplainer DATA CODE ENDS HERE


# Create a Gurobi model
m = gp.Model("AirlineOptimization")

# Decision Variables Section Begin
# Create decision variables a and b for the number of large and small aircraft respectively
aircraft_count = {
    'A': m.addVar(vtype=GRB.INTEGER, name="aircraft_A"),
    'B': m.addVar(vtype=GRB.INTEGER, name="aircraft_B")
}
# Decision Variables Section End


# Objective Function Section Begin
# Set the objective function to minimize total operating cost
m.setObjective(
    gp.quicksum(
        operating_cost_per_aircraft[t] * aircraft_count[t]
        for t in aircraft_types
    ),
    sense=GRB.MINIMIZE
)
# Objective Function Section End


# ORExplainer CONSTRAINTS CODE GOES HERE


# Constraints Section Begin
# Constraint: Meet the passenger transportation demand
m.addConstr(
    gp.quicksum(passenger_capacity[t] * aircraft_count[t]
                for t in aircraft_types) >= min_passenger_demand,
    name="PassengerDemandConstraint"
)

# Constraint: The total number of aircraft cannot exceed the maximum allowed
m.addConstr(
    gp.quicksum(aircraft_count[t]
                for t in aircraft_types) <= max_aircraft_count,
    name="OperationalConstraint"
)
# Constraints Section End


# ORExplainer CONSTRAINTS CODE MIDDLE HERE


# ORExplainer CONSTRAINTS CODE ENDS HERE


# Solving the Model Section Begin
# Solve the model
m.optimize()

# Output the results
if m.status == GRB.OPTIMAL:
    print(f"Minimum total cost: {round(m.ObjVal)} dollars")
    for t in aircraft_types:
        print(f"Number of Type {t} aircraft: {aircraft_count[t].X}")
else:
    print("No optimal solution found.")
# Solving the Model Section End
