import gurobipy as gp
from gurobipy import GRB


# Parameters Section Begin
# Define model parameters
# List of activities
activities = ['A', 'B', 'C', 'D']

# Cost of each activity
costs = {
    'A': 100,
    'B': 200,
    'C': 300,
    'D': 400
}

# Satisfaction score for each activity
satisfaction_scores = {
    'A': 50,
    'B': 80,
    'C': 120,
    'D': 150
}

# Total budget available
budget = 1000

# Maximum number of activities that can be chosen
max_activities = 5

# Maximum number of times an activity can be chosen
max_per_activity = 2
# Parameters Section End


# ORExplainer DATA CODE GOES HERE


# ORExplainer DATA CODE ENDS HERE


# Create a Gurobi model
m = gp.Model("TravelItineraryOptimization")

# Decision Variables Section Begin
# Create decision variables a, b, c, d for the number of times activities A, B, C, D are chosen
activity_vars = {act: m.addVar(vtype=GRB.INTEGER, name=f"activity_{act}", lb=0, ub=max_per_activity)
                 for act in activities}
# Decision Variables Section End


# Objective Function Section Begin
# Set the objective function to maximize total satisfaction
m.setObjective(
    gp.quicksum(satisfaction_scores[act] *
                activity_vars[act] for act in activities),
    sense=GRB.MAXIMIZE
)
# Objective Function Section End


# ORExplainer CONSTRAINTS CODE GOES HERE


# Constraints Section Begin
# Constraint: The total cost of activities must not exceed the budget
m.addConstr(
    gp.quicksum(costs[act] * activity_vars[act]
                for act in activities) <= budget,
    name="BudgetConstraint"
)

# Constraint: The total number of activities chosen must not exceed the maximum number of activities
m.addConstr(
    gp.quicksum(activity_vars[act] for act in activities) <= max_activities,
    name="TotalActivitiesConstraint"
)
# Constraints Section End


# ORExplainer CONSTRAINTS CODE MIDDLE HERE


# ORExplainer CONSTRAINTS CODE ENDS HERE


# Solving the Model Section Begin
# Solve the model
m.optimize()

# Output the results
if m.status == GRB.OPTIMAL:
    print(f"Maximized total satisfaction: {m.objVal}")
    for act in activities:
        print(f"Activity {act} chosen {activity_vars[act].x} times")
else:
    print("No optimal solution found.")
# Solving the Model Section End
