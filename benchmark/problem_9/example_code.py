import gurobipy as gp
from gurobipy import GRB


# Parameters Section Begin
# Define model parameters
vehicle_types = ['Bus', 'Minibus']

# Capacity of each type of vehicle
vehicle_capacity = {
    'Bus': 50,
    'Minibus': 25
}

# Cost of each type of vehicle
vehicle_cost = {
    'Bus': 2000,
    'Minibus': 1200
}

# Total number of people requiring transportation
transportation_needs = 400

# Maximum number of buses and minibuses
max_buses = 10
max_minibuses = 20
# Parameters Section End


# ORExplainer DATA CODE GOES HERE


# ORExplainer DATA CODE ENDS HERE


# Create a Gurobi model
m = gp.Model("TravelAgencyTransportation")

# Decision Variables Section Begin
# Create decision variables x[i] for the number of each type of vehicle
x = {i: m.addVar(vtype=GRB.INTEGER, name=f"x_{i}") for i in vehicle_types}
# Decision Variables Section End

# Objective Function Section Begin
# Set the objective function to minimize total cost
m.setObjective(
    gp.quicksum(vehicle_cost[i] * x[i] for i in vehicle_types),
    sense=GRB.MINIMIZE
)
# Objective Function Section End


# ORExplainer CONSTRAINTS CODE GOES HERE


# Constraints Section Begin
# Constraint: The transportation needs must be met
m.addConstr(
    gp.quicksum(vehicle_capacity[i] * x[i]
                for i in vehicle_types) >= transportation_needs,
    name="PersonnelRequirement"
)

# Constraint: The number of buses must not exceed the maximum limit
m.addConstr(x['Bus'] <= max_buses, name="LargeBusLimit")

# Constraint: The number of minibuses must not exceed the maximum limit
m.addConstr(x['Minibus'] <= max_minibuses, name="MediumBusLimit")
# Constraints Section End


# ORExplainer CONSTRAINTS CODE MIDDLE HERE


# ORExplainer CONSTRAINTS CODE ENDS HERE


# Solving the Model Section Begin
# Solve the model
m.optimize()

# Output the results
if m.status == GRB.OPTIMAL:
    print("Minimum total cost: {} yuan".format(int(m.ObjVal)))
    print("Number of buses: {}".format(int(x['Bus'].X)))
    print("Number of minibuses: {}".format(int(x['Minibus'].X)))
else:
    print("No optimal solution found.")
# Solving the Model Section End
