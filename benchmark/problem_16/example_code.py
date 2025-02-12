import gurobipy as gp
from gurobipy import GRB


# Parameters Section Begin
# Define service types, costs, expected effects, and service times
service_types = ['S1', 'S2', 'S3']

# The costs for each type of service
costs = {
    'S1': 50,
    'S2': 80,
    'S3': 100
}

# The expected effects for each type of service
expected_effects = {
    'S1': 70,
    'S2': 90,
    'S3': 95
}

# The service times for each type of service
service_times = {
    'S1': 30,
    'S2': 50,
    'S3': 70
}

# Budget and time constraints
# The daily budget for providing services
daily_budget = 500

# The maximum service time allowed each day (in minutes)
max_service_time = 480

# The maximum number of times each service can be provided
max_service_counts = {
    'S1': 10,
    'S2': 10,
    'S3': 10
}
# Parameters Section End


# ORExplainer DATA CODE GOES HERE


# ORExplainer DATA CODE ENDS HERE


# Create a Gurobi model
m = gp.Model("CareerGuidanceOptimization")

# Decision Variables Section Begin
# Create decision variables x[service] for the number of times each service is provided
x = {service: m.addVar(vtype=GRB.INTEGER, lb=0, ub=max_service_counts[service], name=f"x_{service}")
     for service in service_types}
# Decision Variables Section End


# Objective Function Section Begin
# Set the objective function to maximize the expected effect
m.setObjective(
    gp.quicksum(expected_effects[service] * x[service]
                for service in service_types),
    sense=GRB.MAXIMIZE
)
# Objective Function Section End


# ORExplainer CONSTRAINTS CODE GOES HERE


# Constraints Section Begin
# Constraint: The total cost of services must not exceed the daily budget
m.addConstr(
    gp.quicksum(costs[service] * x[service]
                for service in service_types) <= daily_budget,
    name="BudgetConstraint"
)

# Constraint: The total service time must not exceed the maximum service time
m.addConstr(
    gp.quicksum(service_times[service] * x[service]
                for service in service_types) <= max_service_time,
    name="TimeConstraint"
)

# Constraint: Each service type can be provided no more than 10 times
for service in service_types:
    m.addConstr(
        x[service] <= max_service_counts[service],
        name=f"MaxServiceConstraint_{service}"
    )
# Constraints Section End


# ORExplainer CONSTRAINTS CODE MIDDLE HERE


# ORExplainer CONSTRAINTS CODE ENDS HERE


# Solving the Model Section Begin
# Solve the model
m.optimize()

# Output the results
if m.status == GRB.OPTIMAL:
    print(f"Maximized expected effect: {m.ObjVal}")
    print("Optimal service provision counts:")
    for service in service_types:
        print(f"{service}: {x[service].X} times")
else:
    print("No optimal solution found.")
# Solving the Model Section End
