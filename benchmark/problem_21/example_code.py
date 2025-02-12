import gurobipy as gp
from gurobipy import GRB


# Parameters Section Begin
# Define model parameters
resources = ['Personnel', 'Funds']
marine_life = ['Dolphins', 'Turtles', 'Sharks', 'Corals', 'Seagrass']

# Resource requirements for each marine species
resource_requirements = {
    'Dolphins': [10, 15],
    'Turtles': [15, 10],
    'Sharks': [20, 20],
    'Corals': [25, 30],
    'Seagrass': [30, 25]
}

# Total resource availability
resource_availability = [100, 150]
# Parameters Section End


# ORExplainer DATA CODE GOES HERE


# ORExplainer DATA CODE ENDS HERE


# Create a Gurobi model
m = gp.Model("MarineReserveAllocation")

# Decision Variables Section Begin
# Create decision variables x[i, j] for resource i allocated to marine species j
x = {(i, j): m.addVar(vtype=GRB.INTEGER, name=f"x_{i}_{j}")
     for i in resources for j in marine_life}
# Decision Variables Section End

# Objective Function Section Begin
# Set the objective function to maximize the total population
m.setObjective(
    gp.quicksum(x[i, j] for i in resources for j in marine_life),
    sense=GRB.MAXIMIZE
)
# Objective Function Section End


# ORExplainer CONSTRAINTS CODE GOES HERE


# Constraints Section Begin
# Constraint: Resource allocation meets the conservation requirements of each marine species
for j in marine_life:
    for i in range(len(resources)):
        m.addConstr(x[resources[i], j] >= resource_requirements[j]
                    [i], name=f"Requirement_{j}_{resources[i]}")

# Constraint: The total allocation of resources cannot exceed their available quantities
for i in range(len(resources)):
    m.addConstr(gp.quicksum(x[resources[i], j] for j in marine_life)
                <= resource_availability[i], name=f"Availability_{resources[i]}")

# Constraint: Protection of corals and seagrass is particularly important, and their resource allocation should not be less than 50% of their requirements
for i in range(len(resources)):
    m.addConstr(x[resources[i], 'Corals'] >= 0.5 * resource_requirements['Corals']
                [i], name=f"Corals_Importance_{resources[i]}")
    m.addConstr(x[resources[i], 'Seagrass'] >= 0.5 * resource_requirements['Seagrass']
                [i], name=f"Seagrass_Importance_{resources[i]}")
# Constraints Section End


# ORExplainer CONSTRAINTS CODE MIDDLE HERE


# ORExplainer CONSTRAINTS CODE ENDS HERE


# Solving the Model Section Begin
# Solve the model
m.optimize()

# Output the results
if m.status == GRB.OPTIMAL:
    print("Maximized total population:", m.ObjVal)
    for i in resources:
        for j in marine_life:
            if x[i, j].X > 0:
                print(f"Number of {i} units allocated to {j}: {x[i, j].X}")
else:
    print("No optimal solution found.")
# Solving the Model Section End
