import gurobipy as gp
from gurobipy import GRB


# Parameters Section Begin
# Define model parameters
foods = ['Chicken Breast', 'Brown Rice', 'Avocado']

# Protein compostion per 100 grams of each food
protein = {
    'Chicken Breast': 30,
    'Brown Rice': 3,
    'Avocado': 2
}

# Carbohydrate compostion per 100 grams of each food
carbs = {
    'Chicken Breast': 0,
    'Brown Rice': 23,
    'Avocado': 9
}

# Fat compostion per 100 grams of each food
fat = {
    'Chicken Breast': 3,
    'Brown Rice': 1,
    'Avocado': 15
}

# Price per 100 grams of each food
price = {
    'Chicken Breast': 15,
    'Brown Rice': 10,
    'Avocado': 20
}

# Nutritional requirements for protein, carbohydrates, and fat
protein_req = 60
carbs_req = 100
fat_req = 30
# Parameters Section End


# ORExplainer DATA CODE GOES HERE


# ORExplainer DATA CODE ENDS HERE


# Decision Variables Section Begin
# Create a Gurobi model
m = gp.Model("DietOptimization")

# Create decision variables for the intake of each type of food
x = {food: m.addVar(vtype=GRB.INTEGER, name=food) for food in foods}
# Decision Variables Section End

# Objective Function Section Begin
# Set the objective function to minimize the cost of food
m.setObjective(
    gp.quicksum(price[food] * x[food] for food in foods),
    GRB.MINIMIZE
)
# Objective Function Section End


# ORExplainer CONSTRAINTS CODE GOES HERE


# Constraints Section Begin
# Constraint: Protein requirement met
m.addConstr(
    gp.quicksum(protein[food] * x[food] for food in foods) >= protein_req,
    "ProteinRequirement"
)

# Constraint: Carbohydrate requirement met
m.addConstr(
    gp.quicksum(carbs[food] * x[food] for food in foods) >= carbs_req,
    "CarbsRequirement"
)

# Constraint: Fat requirement met
m.addConstr(
    gp.quicksum(fat[food] * x[food] for food in foods) >= fat_req,
    "FatRequirement"
)
# Constraints Section End


# ORExplainer CONSTRAINTS CODE MIDDLE HERE


# ORExplainer CONSTRAINTS CODE ENDS HERE


# Solving the Model Section Begin
# Solve the model
m.optimize()

# Output the results
if m.status == GRB.OPTIMAL:
    print(f"Optimal solution found. The lowest price is: {m.ObjVal} yuan")
    for food in foods:
        print(f"{food} Intake: {x[food].X} grams")
else:
    print("No optimal solution found.")
# Solving the Model Section End
