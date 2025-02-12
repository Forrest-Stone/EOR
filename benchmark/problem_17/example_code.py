import gurobipy as gp
from gurobipy import GRB


# Parameters Section Begin
# Define model parameters
# Total number of available workers
total_workers = 100

# Minimum and maximum workers for each task
# Minimum workers for wheat harvesting as a percentage of total workers
min_workers_wheat = 0.3

# Maximum workers for cow milking as a percentage of total workers
max_workers_cow = 0.4

# Minimum workers for chicken feeding
min_workers_chicken = 20

# Wage cost per worker (dollars/day)
wage_cost_per_worker = 10
# Parameters Section End


# ORExplainer DATA CODE GOES HERE


# ORExplainer DATA CODE ENDS HERE


# Create a Gurobi model
m = gp.Model("WorkerAllocation")

# Decision Variables Section Begin
# Create decision variables for the number of workers allocated to each task
x1 = m.addVar(vtype=GRB.INTEGER, name="x1_wheat_harvesting")
x2 = m.addVar(vtype=GRB.INTEGER, name="x2_cow_milking")
x3 = m.addVar(vtype=GRB.INTEGER, name="x3_chicken_feeding")
# Decision Variables Section End

# Objective Function Section Begin
# Set the objective function to minimize total wage costs
total_workers_var = x1 + x2 + x3
m.setObjective(
    wage_cost_per_worker * total_workers_var,
    sense=GRB.MINIMIZE
)
# Objective Function Section End


# ORExplainer CONSTRAINTS CODE GOES HERE


# Constraints Section Begin
# Constraint: The total number of workers does not exceed the maximum available
m.addConstr(total_workers_var <= total_workers, name="TotalWorkerLimit")

# Constraint: Number of workers for wheat harvesting should be at least 30% of the total number of workers
m.addConstr(x1 >= min_workers_wheat * total_workers_var,
            name="WheatHarvestingWorkerMinimum")

# Constraint: Number of workers for cow milking should be at most 40% of the total number of workers
m.addConstr(x2 <= max_workers_cow * total_workers_var,
            name="CowMilkingWorkerMaximum")

# Constraint: Number of workers for chicken feeding should be at least 20
m.addConstr(x3 >= min_workers_chicken, name="ChickenFeedingWorkerMinimum")
# Constraints Section End


# ORExplainer CONSTRAINTS CODE MIDDLE HERE


# ORExplainer CONSTRAINTS CODE ENDS HERE


# Solving the Model Section Begin
# Solve the model
m.optimize()

# Output the results
if m.status == GRB.OPTIMAL:
    print(f"Minimum total wage costs: ${m.ObjVal}")
    print(f"Optimal worker allocation:")
    print(f"Wheat Harvesting: {x1.X} workers")
    print(f"Cow Milking: {x2.X} workers")
    print(f"Chicken Feeding: {x3.X} workers")
else:
    print("No optimal solution found.")
# Solving the Model Section End
