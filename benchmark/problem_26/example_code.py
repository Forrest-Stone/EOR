import gurobipy as gp
from gurobipy import GRB


# Parameters Section Begin
# Define model parameters
# Available funds
available_funds = 100000

# Risk and return rates
# Risk rates for personal and corporate loans
risk_personal_loan = 0.10
risk_corporate_loan = 0.20

# Return rates for personal and corporate loans
return_personal_loan = 0.05
return_corporate_loan = 0.15

# Risk exposure limits
risk_exposure_personal_loan_limit = 8000
risk_exposure_corporate_loan_limit = 10000

# Total risk exposure limit
total_risk_exposure_limit = 15000

# Allocation limits
minimum_personal_loan_allocation_ratio = 0.5
# Parameters Section End


# ORExplainer DATA CODE GOES HERE


# ORExplainer DATA CODE ENDS HERE


# Create a Gurobi model
m = gp.Model("BankLoanAllocation")

# Decision Variables Section Begin
# Create decision variables x for personal loans and y for corporate loans
x = m.addVar(vtype=GRB.INTEGER, name="x")  # Funds for personal loans
y = m.addVar(vtype=GRB.INTEGER, name="y")  # Funds for corporate loans
# Decision Variables Section End

# Objective Function Section Begin
# Set the objective function to maximize expected return
m.setObjective(
    return_personal_loan * x + return_corporate_loan * y,
    sense=GRB.MAXIMIZE
)
# Objective Function Section End


# ORExplainer CONSTRAINTS CODE GOES HERE


# Constraints Section Begin
# Constraint: Risk exposure limits for personal loans
m.addConstr(risk_personal_loan * x <=
            risk_exposure_personal_loan_limit, name="PersonalLoanRiskExposure")

# Constraint: Risk exposure limits for corporate loans
m.addConstr(risk_corporate_loan * y <=
            risk_exposure_corporate_loan_limit, name="CorporateLoanRiskExposure")

# Constraint: Total risk exposure limit
m.addConstr(risk_personal_loan * x + risk_corporate_loan *
            y <= total_risk_exposure_limit, name="TotalRiskExposure")

# Constraint: At least half of the funds allocated to personal loans
m.addConstr(x >= minimum_personal_loan_allocation_ratio *
            (x + y), name="PersonalLoanAllocationMinimum")

# Constraint: Total fund availability
m.addConstr(x + y <= available_funds, name="TotalFundAvailability")
# Constraints Section End


# ORExplainer CONSTRAINTS CODE MIDDLE HERE


# ORExplainer CONSTRAINTS CODE ENDS HERE


# Solving the Model Section Begin
# Solve the model
m.optimize()

# Output the results
if m.status == GRB.OPTIMAL:
    print(f"Maximized expected return: ${round(m.ObjVal)}")
    print(
        f"Optimal fund allocation: Personal loans = ${round(x.X)}, Corporate loans = ${round(y.X)}")
else:
    print("No optimal solution found.")
# Solving the Model Section End
