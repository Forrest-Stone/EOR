import gurobipy as gp
from gurobipy import GRB


# Parameters Section Begin
# Define model parameters
production_lines = ['A', 'B']
tasks = [1, 2, 3]

# Minimum and maximum energy efficiency consumption (kw) for each task
min_energy_consumption = {
    1: 10,
    2: 15,
    3: 12
}
max_energy_consumption = {
    1: 20,
    2: 25,
    3: 22
}

# Energy consumption cost per unit (yuan/kw)
energy_cost_per_unit = {
    1: 5,
    2: 4,
    3: 6
}

# Production cost per unit (yuan/piece)
production_cost_per_unit = {
    1: 30,
    2: 35,
    3: 32
}

# Production quantity required for each task (pieces)
production_quantity = {
    1: 300,
    2: 200,
    3: 250
}

# Total production capacity for each production line (pieces)
production_capacity = {
    'A': 400,
    'B': 350
}
# Parameters Section End


# ORExplainer DATA CODE GOES HERE


# ORExplainer DATA CODE ENDS HERE


# Create a Gurobi model
m = gp.Model("ProductionLineOptimization")

# Decision Variables Section Begin
# Create decision variables x[i, j] for production quantity of production line i for completing production task j
x = {(i, j): m.addVar(vtype=GRB.INTEGER, name=f"x_{i}_{j}")
     for i in production_lines for j in tasks}
# Decision Variables Section End


# Objective Function Section Begin
# Set the objective function to minimize total energy consumption and production cost
m.setObjective(
    gp.quicksum(
        energy_cost_per_unit[j] * min_energy_consumption[j] *
        x[i, j] + production_cost_per_unit[j] * x[i, j]
        for i in production_lines for j in tasks
    ),
    sense=GRB.MINIMIZE
)
# Objective Function Section End


# ORExplainer CONSTRAINTS CODE GOES HERE


# Constraints Section Begin
# Constraint: The production quantity for each task must meet the demand
for j in tasks:
    m.addConstr(
        gp.quicksum(x[i, j]
                    for i in production_lines) == production_quantity[j],
        name=f"ProductionQuantityConstraint_{j}"
    )

# Constraint: The task allocation for each production line must not exceed its total production capacity
for i in production_lines:
    m.addConstr(
        gp.quicksum(x[i, j] for j in tasks) <= production_capacity[i],
        name=f"ProductionCapacityConstraint_{i}"
    )

# Constraint: The energy usage for each production task is within the minimum and maximum energy efficiency consumption standards
for i in production_lines:
    for j in tasks:
        m.addConstr(
            min_energy_consumption[j] * x[i,
                                          j] <= max_energy_consumption[j] * x[i, j],
            name=f"EnergyConsumptionConstraint_{i}_{j}"
        )
# Constraints Section End


# ORExplainer CONSTRAINTS CODE MIDDLE HERE


# ORExplainer CONSTRAINTS CODE ENDS HERE


# Solving the Model Section Begin
# Solve the model
m.optimize()

# Output the results
if m.status == GRB.OPTIMAL:
    print(
        f"Minimum total energy consumption and production cost: {m.ObjVal}")
    for i in production_lines:
        for j in tasks:
            print(
                f"Production line {i} completes production task {j} with a production quantity of: {x[i, j].X}")
else:
    print("No optimal solution found.")
# Solving the Model Section End
