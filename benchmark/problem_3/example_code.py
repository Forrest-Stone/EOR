import gurobipy as gp
from gurobipy import GRB


# Parameters Section Begin
# Define model parameters
intersections = ['A', 'B', 'C', 'D']

# Traffic flow (vehicles/hour) for each intersection
traffic_flow = {
    'A': 500,
    'B': 400,
    'C': 300,
    'D': 200
}

# Green channel setup cost (yuan/lane) for each intersection
setup_cost = {
    'A': 1000,
    'B': 800,
    'C': 600,
    'D': 400
}

# Maximum number of green channels
max_green_channels = 10

# Objective function weights
alpha = 1
beta = 10

# Traffic flow increase by one green channel
traffic_flow_increase_by_one_green_channel = 0.2
# Parameters Section End


# ORExplainer DATA CODE GOES HERE


# ORExplainer DATA CODE ENDS HERE


# Create a Gurobi model
m = gp.Model("TrafficOptimization")

# Decision Variables Section Begin
# Create decision variables x[i] for the number of green channels at intersection i
x = {i: m.addVar(vtype=GRB.INTEGER, name=f"x_{i}") for i in intersections}
# Decision Variables Section End

# Objective Function Section Begin
# Set the objective function to minimize traffic management costs and maximize traffic flow
m.setObjective(
    alpha * gp.quicksum(setup_cost[i] * x[i] for i in intersections) -
    beta * gp.quicksum(traffic_flow[i] * (1 + traffic_flow_increase_by_one_green_channel * x[i])
                       for i in intersections),
    sense=GRB.MINIMIZE
)
# Objective Function Section End


# ORExplainer CONSTRAINTS CODE GOES HERE


# Constraints Section Begin
# Constraint: Limit on the total number of green channels
m.addConstr(gp.quicksum(x[i] for i in intersections)
            <= max_green_channels, name="TotalGreenwaysLimit")

# Constraint: Fairness constraint (each intersection must have at least one green channel)
for i in intersections:
    m.addConstr(x[i] >= 1, name=f"FairnessConstraint_{i}")
# Constraints Section End


# ORExplainer CONSTRAINTS CODE MIDDLE HERE


# ORExplainer CONSTRAINTS CODE ENDS HERE


# Solving the Model Section Begin
# Solve the model
m.optimize()

# Output the results
if m.status == GRB.OPTIMAL:
    print(f"Optimal objective value: {m.ObjVal}")
    print("Green channel allocation plan:")
    for i in intersections:
        print(f"Intersection {i}: {x[i].X} green channels")
    print("Traffic flow:")
    for i in intersections:
        print(
            f"Intersection {i}: {traffic_flow[i] * (1 + 0.2 * x[i].X)} vehicles/hour")
    print("Traffic management costs:")
    print(sum(setup_cost[i] * x[i].X for i in intersections))
else:
    print("No optimal solution found.")
# Solving the Model Section End
