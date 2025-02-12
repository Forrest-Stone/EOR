import gurobipy as gp
from gurobipy import GRB


# Parameters Section Begin
# Define platforms and their reach per advertising campaign
platforms = ['Facebook', 'Twitter', 'Instagram']
reach_per_campaign = {
    'Facebook': 2000,
    'Twitter': 1500,
    'Instagram': 1000
}

# Cost per advertising campaign (dollars)
cost_per_campaign = {
    'Facebook': 1000,
    'Twitter': 1000,
    'Instagram': 1000
}

# Number of advertising campaigns constraints
min_reach = 10000
max_campaigns = 10
# Parameters Section End


# ORExplainer DATA CODE GOES HERE


# ORExplainer DATA CODE ENDS HERE


# Create a Gurobi model
m = gp.Model("AdvertisingAllocation")

# Decision Variables Section Begin
# Create decision variables for the number of campaigns on each platform
campaigns = {p: m.addVar(
    vtype=GRB.INTEGER, name=f"campaigns_{p}", lb=0) for p in platforms}
# Decision Variables Section End


# Objective Function Section Begin
# Set the objective function to minimize the total cost
m.setObjective(
    gp.quicksum(campaigns[p] * cost_per_campaign[p] for p in platforms),
    sense=GRB.MINIMIZE
)
# Objective Function Section End


# ORExplainer CONSTRAINTS CODE GOES HERE


# Constraints Section Begin
# Constraint: Reach at least 10000 potential customers within 7 days
m.addConstr(
    gp.quicksum(campaigns[p] * reach_per_campaign[p]
                for p in platforms) >= min_reach,
    name="MinReachConstraint"
)

# Constraint: The company can only advertise a maximum of 10 times
m.addConstr(
    gp.quicksum(campaigns[p] for p in platforms) <= max_campaigns,
    name="MaxCampaignsConstraint"
)
# Constraints Section End


# ORExplainer CONSTRAINTS CODE MIDDLE HERE


# ORExplainer CONSTRAINTS CODE ENDS HERE


# Solving the Model Section Begin
# Solve the model
m.optimize()

# Output the results
if m.status == GRB.OPTIMAL:
    print("Optimal solution found.")
    print(f"Minimum total cost: ${m.objVal}")
    for p in platforms:
        print(f"Number of advertising campaigns on {p}: {campaigns[p].X}")
else:
    print("No optimal solution found.")
# Solving the Model Section End
