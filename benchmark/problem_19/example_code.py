import gurobipy as gp
from gurobipy import GRB


# Parameters Section Begin
# Define model parameters
vehicle_types = ['X', 'Y']

# Vehicle capacities (tons)
capacity = {
    'X': 10,
    'Y': 20
}

# Vehicle operating costs (dollars per hour)
operating_cost = {
    'X': 20,
    'Y': 30
}

# Time required to transport one ton of goods (hours per ton)
time_per_ton = {
    'X': 1,
    'Y': 0.5
}

# Minimum demand (tons)
min_demand = 100

# Maximum total operating hours
max_operating_hours = 24
# Parameters Section End


# ORExplainer DATA CODE GOES HERE


# ORExplainer DATA CODE ENDS HERE


# Create a Gurobi model
m = gp.Model("VehicleSchedulingOptimization")

# Decision Variables Section Begin
# Create decision variables for the number of hours each vehicle type operates
operating_hours = {v: m.addVar(
    vtype=GRB.CONTINUOUS, name=f"operating_hours_{v}")
    for v in vehicle_types}
# Decision Variables Section End


# Objective Function Section Begin
# Set the objective function to minimize total operating cost
m.setObjective(
    gp.quicksum(
        operating_cost[v] * operating_hours[v]
        for v in vehicle_types
    ),
    sense=GRB.MINIMIZE
)
# Objective Function Section End


# ORExplainer CONSTRAINTS CODE GOES HERE


# Constraints Section Begin
# Constraint: The total amount of goods transported must meet the demand
m.addConstr(
    gp.quicksum(capacity[v] / time_per_ton[v] * operating_hours[v]
                for v in vehicle_types) >= min_demand,
    name="DemandConstraint"
)

# Constraint: The sum of operating hours for all vehicle types cannot exceed the available hours
m.addConstr(
    gp.quicksum(operating_hours[v]
                for v in vehicle_types) <= max_operating_hours,
    name="OperatingHoursConstraint"
)
# Constraints Section End


# ORExplainer CONSTRAINTS CODE MIDDLE HERE


# ORExplainer CONSTRAINTS CODE ENDS HERE


# Solving the Model Section Begin
# Solve the model
m.optimize()

# Output the results
if m.status == GRB.OPTIMAL:
    print(f"Minimum total cost: ${round(m.ObjVal)}")
    for v in vehicle_types:
        print(
            f"Optimal operating hours for vehicle type {v}: {round(operating_hours[v].X)} hours")
else:
    print("No optimal solution found.")
# Solving the Model Section End
