import gurobipy as gp
from gurobipy import GRB


# Parameters Section Begin
# Define model parameters
base_stations = [1, 2, 3, 4, 5]

# Total spectrum resources for each base station in MHz
spectrum_resources = {
    1: 100,
    2: 120,
    3: 150,
    4: 200,
    5: 220
}

# Expected throughput per MHz for each base station
throughput_per_mhz = {
    1: 50,
    2: 60,
    3: 75,
    4: 100,
    5: 110
}
# Parameters Section End


# ORExplainer DATA CODE GOES HERE


# ORExplainer DATA CODE ENDS HERE


# Create a Gurobi model
m = gp.Model("SpectrumAllocationOptimization")

# Decision Variables Section Begin
# Create decision variables f[i] for spectrum resources allocated to base station i
allocated_resources = {i: m.addVar(vtype=GRB.CONTINUOUS, name=f"allocated_resources_{i}")
                       for i in base_stations}
# Decision Variables Section End


# Objective Function Section Begin
# Set the objective function to maximize total throughput
m.setObjective(
    gp.quicksum(
        throughput_per_mhz[i] * allocated_resources[i]
        for i in base_stations
    ),
    sense=GRB.MAXIMIZE
)
# Objective Function Section End


# ORExplainer CONSTRAINTS CODE GOES HERE


# Constraints Section Begin
# Constraint: Each base station must retain at least 10% of the spectrum resources
for i in base_stations:
    m.addConstr(
        allocated_resources[i] >= 0.1 * spectrum_resources[i],
        name=f"MinResourceConstraint_{i}"
    )

# Constraint: The spectrum resource allocation for each base station cannot exceed 90% of its total resources
for i in base_stations:
    m.addConstr(
        allocated_resources[i] <= 0.9 * spectrum_resources[i],
        name=f"MaxResourceConstraint_{i}"
    )

# Constraint: The difference in spectrum resource allocation between base stations cannot exceed 10%
for i in base_stations:
    for j in base_stations:
        if i < j:
            m.addConstr(
                allocated_resources[i] -
                allocated_resources[j] <= 0.1 * spectrum_resources[i],
                name=f"ResourceDifferenceConstraint_{i}_{j}_1"
            )
            m.addConstr(
                allocated_resources[j] -
                allocated_resources[i] <= 0.1 * spectrum_resources[j],
                name=f"ResourceDifferenceConstraint_{i}_{j}_2"
            )
# Constraints Section End


# ORExplainer CONSTRAINTS CODE MIDDLE HERE


# ORExplainer CONSTRAINTS CODE ENDS HERE


# Solving the Model Section Begin
# Solve the model
m.optimize()

# Output the results
if m.status == GRB.OPTIMAL:
    print("Optimal solution found. Maximum total throughput is:",
          round(m.ObjVal, 2), "Mbps")
    for i in base_stations:
        print(
            f"Spectrum resource allocation for Base Station {i}: {round(allocated_resources[i].X, 2)} MHz")
else:
    print("No optimal solution found.")
# Solving the Model Section End
