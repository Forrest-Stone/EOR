import gurobipy as gp
from gurobipy import GRB


# Parameters Section Begin
# Define model parameters
# Selling prices and manufacturing costs for tables, chairs, and bookshelves
selling_price_tables = 200
selling_price_chairs = 50
selling_price_bookshelves = 150

# Manufacturing costs for tables, chairs, and bookshelves
manufacturing_cost_tables = 120
manufacturing_cost_chairs = 20
manufacturing_cost_bookshelves = 90

# Profit per item
profit_per_table = selling_price_tables - manufacturing_cost_tables
profit_per_chair = selling_price_chairs - manufacturing_cost_chairs
profit_per_bookshelf = selling_price_bookshelves - manufacturing_cost_bookshelves

# Warehouse space required for tables, chairs, and bookshelves
warehouse_space_tables = 5
warehouse_space_chairs = 2
warehouse_space_bookshelves = 3

# Total warehouse space available
total_warehouse_space = 500

# Minimum number of tables and bookshelves to produce
min_tables = 10
min_bookshelves = 20

# Maximum total number of items that can be produced
max_total_items = 200
# Parameters Section End


# ORExplainer DATA CODE GOES HERE


# ORExplainer DATA CODE ENDS HERE


# Create a Gurobi model
m = gp.Model("FurnitureProductionOptimization")

# Decision Variables Section Begin
# Create decision variables for the number of tables, chairs, and bookshelves produced
tables = m.addVar(vtype=GRB.INTEGER, name="tables")
chairs = m.addVar(vtype=GRB.INTEGER, name="chairs")
bookshelves = m.addVar(vtype=GRB.INTEGER, name="bookshelves")
# Decision Variables Section End


# Objective Function Section Begin
# Set the objective function to maximize total profit
m.setObjective(
    profit_per_table * tables + profit_per_chair *
    chairs + profit_per_bookshelf * bookshelves,
    sense=GRB.MAXIMIZE
)
# Objective Function Section End


# ORExplainer CONSTRAINTS CODE GOES HERE


# Constraints Section Begin
# Constraint: Total warehouse space usage must not exceed available space
m.addConstr(
    warehouse_space_tables * tables + warehouse_space_chairs * chairs +
    warehouse_space_bookshelves * bookshelves <= total_warehouse_space,
    name="WarehouseSpaceConstraint"
)

# Constraint: At least 10 tables must be produced
m.addConstr(
    tables >= min_tables,
    name="MinTablesConstraint"
)

# Constraint: At least 20 bookshelves must be produced
m.addConstr(
    bookshelves >= min_bookshelves,
    name="MinBookshelvesConstraint"
)

# Constraint: Total number of items produced must not exceed 200
m.addConstr(
    tables + chairs + bookshelves <= max_total_items,
    name="TotalItemsConstraint"
)
# Constraints Section End


# ORExplainer CONSTRAINTS CODE MIDDLE HERE


# ORExplainer CONSTRAINTS CODE ENDS HERE


# Solving the Model Section Begin
# Solve the model
m.optimize()

# Output the results
if m.status == GRB.OPTIMAL:
    print(f"Maximum total profit: {round(m.ObjVal)}")
    print(
        f"Optimal production plan: Tables = {round(tables.X)}, Chairs = {round(chairs.X)}, Bookshelves = {round(bookshelves.X)}")
else:
    print("No optimal solution found.")
# Solving the Model Section End
