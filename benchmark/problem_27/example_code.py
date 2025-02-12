import gurobipy as gp
from gurobipy import GRB


# Parameters Section Begin
# Define model parameters
# List of products
products = ['Dessert', 'Beverage']

# Production cost for each product
production_cost_per_unit = {
    'Dessert': 10,
    'Beverage': 5
}

# Selling price for each product
selling_price_per_unit = {
    'Dessert': 20,
    'Beverage': 10
}

# Expected sales volume for each product
expected_sales_volume = {
    'Dessert': 1000,
    'Beverage': 2000
}

# Production time and raw materials required for each product
# Production time per unit
production_time_per_unit = {
    'Dessert': 0.02,
    'Beverage': 0.01
}

# Raw materials per unit
raw_materials_per_unit = {
    'Dessert': 2,
    'Beverage': 1
}

# Daily constraints
# Total production time available per day in hours
total_production_time = 10

# Total raw materials available per day in units
total_raw_materials = 5000
# Parameters Section End


# ORExplainer DATA CODE GOES HERE


# ORExplainer DATA CODE ENDS HERE


# Create a Gurobi model
m = gp.Model("ProductionPlanningOptimization")

# Decision Variables Section Begin
# Create decision variables x[p] for the production quantity of product p
x = {p: m.addVar(vtype=GRB.CONTINUOUS, name=f"x_{p}")
     for p in products}
# Decision Variables Section End


# Objective Function Section Begin
# Set the objective function to maximize profit
m.setObjective(
    gp.quicksum(
        (selling_price_per_unit[p] - production_cost_per_unit[p]) * x[p]
        for p in products
    ),
    sense=GRB.MAXIMIZE
)
# Objective Function Section End


# ORExplainer CONSTRAINTS CODE GOES HERE


# Constraints Section Begin
# Constraint: Production time must not exceed available time
m.addConstr(
    gp.quicksum(production_time_per_unit[p] * x[p]
                for p in products) <= total_production_time,
    name="ProductionTimeConstraint"
)

# Constraint: Raw materials must not exceed available quantity
m.addConstr(
    gp.quicksum(raw_materials_per_unit[p] * x[p]
                for p in products) <= total_raw_materials,
    name="RawMaterialsConstraint"
)

# Constraints: Production volume must not exceed expected sales volume
for p in products:
    m.addConstr(
        x[p] <= expected_sales_volume[p],
        name=f"SalesVolumeConstraint_{p}"
    )
# Constraints Section End


# ORExplainer CONSTRAINTS CODE MIDDLE HERE


# ORExplainer CONSTRAINTS CODE ENDS HERE


# Solving the Model Section Begin
# Solve the model
m.optimize()

# Output the results
if m.status == GRB.OPTIMAL:
    print(f"Maximized profit: {m.ObjVal}")
    for p in products:
        print(f"Production volume for {p}: {x[p].X}")
else:
    print("No optimal solution found.")
# Solving the Model Section End
