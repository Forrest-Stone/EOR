import gurobipy as gp
from gurobipy import GRB


# Parameters Section Begin
# Define model parameters
processes = ['x1', 'x2', 'x3', 'x4']

# Unit water recovery rate for each process
unit_water_recovery_rate = {
    'x1': 0.8,
    'x2': 0.7,
    'x3': 0.9,
    'x4': 0.6
}

# Water consumption limits for each process (liters)
water_consumption_limits = {
    'x1': (0, 5000),
    'x2': (0, 4000),
    'x3': (0, 6000),
    'x4': (0, 7000)
}
# Parameters Section End


# ORExplainer DATA CODE GOES HERE


# ORExplainer DATA CODE ENDS HERE


# Create a Gurobi model
m = gp.Model("TextileWaterAllocation")

# Decision Variables Section Begin
# Create decision variables for the amount of water resources allocated to each process
x = {i: m.addVar(vtype=GRB.INTEGER,
                 lb=water_consumption_limits[i][0], ub=water_consumption_limits[i][1], name=i)
     for i in processes}
# Decision Variables Section End

# Objective Function Section Begin
# Set the objective function to maximize the overall water recovery rate
m.setObjective(
    gp.quicksum(unit_water_recovery_rate[i] * x[i] for i in processes),
    GRB.MAXIMIZE
)
# Objective Function Section End


# ORExplainer CONSTRAINTS CODE GOES HERE


# Constraints Section Begin
# Constraint: The total water consumption of x1 and x2 cannot exceed 5000 liters
m.addConstr(x['x1'] + x['x2'] <= 5000, "WaterAllocationLimitX1X2")

# Constraint: The total water consumption of x2 and x3 must be at least 3000 liters
m.addConstr(x['x2'] + x['x3'] >= 3000, "WaterAllocationRequirementX2X3")

# Constraint: The difference in water consumption between x3 and x4 cannot exceed 1000 liters
m.addConstr(x['x3'] - x['x4'] <= 1000, "WaterDifferenceLimitationX3X4")
m.addConstr(x['x4'] - x['x3'] <= 1000, "WaterDifferenceLimitationX4X3")

# Constraint: The difference in water consumption between x4 and x1 must be at least 500 liters
m.addConstr(x['x4'] - x['x1'] >= 500, "WaterDifferenceRequirementX4X1")
# Constraints Section End


# ORExplainer CONSTRAINTS CODE MIDDLE HERE


# ORExplainer CONSTRAINTS CODE ENDS HERE


# Solving the Model Section Begin
# Solve the model
m.optimize()

# Output the results
if m.status == GRB.OPTIMAL:
    print(f"Maximized overall water recovery rate: {m.ObjVal:.2f}")
    for i in processes:
        print(f"{i} = {x[i].X} liters")
else:
    print("No optimal solution found.")
# Solving the Model Section End
