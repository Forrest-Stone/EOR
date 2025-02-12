import gurobipy as gp
from gurobipy import GRB


# Parameters Section Begin
# Define model parameters
# Define the set of distribution centers
distribution_centers = ['A', 'B']

# Define the set of cities
cities = [1, 2, 3, 4]

# Transportation costs from each distribution center to each city
transport_costs = {
    ('A', 1): 2, ('A', 2): 3, ('A', 3): 4, ('A', 4): 5,
    ('B', 1): 3, ('B', 2): 2, ('B', 3): 5, ('B', 4): 4
}

# Transportation capacity of each distribution center
supply_capacity = {
    'A': 100,
    'B': 200
}

# Drug demands for each city
city_demand = {
    1: 50,
    2: 80,
    3: 70,
    4: 100
}
# Parameters Section End


# ORExplainer DATA CODE GOES HERE


# ORExplainer DATA CODE ENDS HERE


# Create a Gurobi model
m = gp.Model("ColdChainTransportation")

# Decision Variables Section Begin
# Create decision variables for the quantity of drugs transported from each distribution center to each city
transport_quantity = {(i, j): m.addVar(vtype=GRB.CONTINUOUS, name=f"transport_{i}_{j}")
                      for i in distribution_centers for j in cities}
# Decision Variables Section End

# Objective Function Section Begin
# Set the objective function to minimize total transportation cost
m.setObjective(
    gp.quicksum(transport_costs[i, j] * transport_quantity[i, j]
                for i in distribution_centers for j in cities),
    sense=GRB.MINIMIZE
)
# Objective Function Section End


# ORExplainer CONSTRAINTS CODE GOES HERE


# Constraints Section Begin
# Constraint: Transportation capacity constraints of distribution centers
for i in distribution_centers:
    m.addConstr(
        gp.quicksum(transport_quantity[i, j]
                    for j in cities) <= supply_capacity[i],
        name=f"SupplyCapacity_{i}"
    )

# Constraint: Drug demand satisfaction of cities
for j in cities:
    m.addConstr(
        gp.quicksum(transport_quantity[i, j]
                    for i in distribution_centers) == city_demand[j],
        name=f"DemandSatisfaction_{j}"
    )
# Constraints Section End


# ORExplainer CONSTRAINTS CODE MIDDLE HERE


# ORExplainer CONSTRAINTS CODE ENDS HERE


# Solving the Model Section Begin
# Solve the model
m.optimize()

# Output the results
if m.status == GRB.OPTIMAL:
    print("Minimized total transportation cost: {}".format(m.ObjVal))
    for i in distribution_centers:
        for j in cities:
            if transport_quantity[i, j].X > 0:
                print(
                    f"Quantity of drugs transported from distribution center {i} to city {j}: {transport_quantity[i, j].X}")
else:
    print("No optimal solution found.")
# Solving the Model Section End
