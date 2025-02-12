import gurobipy as gp
from gurobipy import GRB


# Parameters Section Begin
# Define model parameters
regions = [1, 2, 3, 4]
centers = [1, 2]

# Garbage amount produced in each region (tons)
garbage_amount = {
    1: 100,
    2: 200,
    3: 150,
    4: 180
}

# Daily processing capacity for each processing center (tons)
center_capacity = {
    1: 400,
    2: 300
}

# Distances from the processing centers to the regions (km)
distances = {
    1: {1: 10, 2: 20, 3: 30, 4: 40},
    2: {1: 40, 2: 30, 3: 20, 4: 10}
}

# Unit processing cost for each processing center (yuan/ton)
processing_cost = {
    1: 10,
    2: 15
}

# Unit transportation cost (yuan/ton/km)
transport_cost_per_km = 1
# Parameters Section End


# ORExplainer DATA CODE GOES HERE


# ORExplainer DATA CODE ENDS HERE


# Create a Gurobi model
m = gp.Model("GarbageAllocationOptimization")

# Decision Variables Section Begin
# Create decision variables x[i, j] for amount of garbage from region i to processing center j
x = {(i, j): m.addVar(vtype=GRB.CONTINUOUS, name=f"x_{i}_{j}")
     for i in regions for j in centers}
# Decision Variables Section End


# Objective Function Section Begin
# Set the objective function to minimize total cost (transportation + processing)
m.setObjective(
    gp.quicksum(
        (processing_cost[j] + distances[j][i]
         * transport_cost_per_km) * x[i, j]
        for i in regions for j in centers
    ),
    sense=GRB.MINIMIZE
)
# Objective Function Section End


# ORExplainer CONSTRAINTS CODE GOES HERE


# Constraints Section Begin
# Constraint: The allocated garbage from each region must equal the amount of garbage produced in that region
for i in regions:
    m.addConstr(
        gp.quicksum(x[i, j] for j in centers) == garbage_amount[i],
        name=f"Region_{i}_Allocation"
    )

# Constraint: The amount of garbage processed by each processing center cannot exceed its daily processing capacity
for j in centers:
    m.addConstr(
        gp.quicksum(x[i, j] for i in regions) <= center_capacity[j],
        name=f"Center_{j}_Capacity"
    )

# Constraints Section End


# ORExplainer CONSTRAINTS CODE MIDDLE HERE


# ORExplainer CONSTRAINTS CODE ENDS HERE


# Solving the Model Section Begin
# Solve the model
m.optimize()

# Output the results
if m.status == GRB.OPTIMAL:
    print(f"Minimum total cost: {m.ObjVal:.2f} yuan")
    for i in regions:
        for j in centers:
            if x[i, j].X > 0:
                print(
                    f"Allocate {x[i, j].X:.2f} tons of garbage from region {i} to processing center {j}")
else:
    print("No optimal solution found.")
# Solving the Model Section End
