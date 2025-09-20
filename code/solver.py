from typing import List, Dict, Tuple
import pulp
from datetime import datetime, timedelta

def detect_overlaps(flights: List[Dict], buffer_minutes_by_type: Dict[str,int] = None) -> List[Tuple[str,str]]:
    """Return list of (a,b) flight id pairs that overlap considering buffer times per type."""
    buffer_minutes_by_type = buffer_minutes_by_type or {}
    overlaps = []
    n = len(flights)
    for i in range(n):
        a = flights[i]
        a_buf = timedelta(minutes=buffer_minutes_by_type.get(a["atype"], 0))
        a_start = a["arr"] - a_buf
        a_end   = a["dep"] + a_buf
        for j in range(i+1, n):
            b = flights[j]
            b_buf = timedelta(minutes=buffer_minutes_by_type.get(b["atype"], 0))
            b_start = b["arr"] - b_buf
            b_end   = b["dep"] + b_buf
            if (a_start < b_end) and (b_start < a_end):
                overlaps.append((a["id"], b["id"]))
    return overlaps

def solve_assignment(
    flights: List[Dict],
    bays: List[str],
    comp: Dict[Tuple[str,str], int],
    revenue: Dict[Tuple[str,str,str], float],
    overlaps: List[Tuple[str,str]],
    time_limit_seconds: int = 30
):
    prob = pulp.LpProblem("AircraftParking", pulp.LpMaximize)
    x = {}
    for f in flights:
        for b in bays:
            name = f"x_{f['id']}_{b}"
            x[(f['id'], b)] = pulp.LpVariable(name, cat="Binary")

    # Objective: maximize total revenue
    prob += pulp.lpSum(
        revenue.get((f["airline"], f["atype"], b), 0.0) * x[(f["id"], b)]
        for f in flights for b in bays
    ), "Total_Revenue"

    # Compatibility constraint
    for f in flights:
        for b in bays:
            if comp.get((f["atype"], b), 0) == 0:
                prob += x[(f["id"], b)] <= 0

    # Each flight assigned to at most one bay
    for f in flights:
        prob += pulp.lpSum(x[(f["id"], b)] for b in bays) <= 1

    # No overlapping flights in the same bay
    for (a1, a2) in overlaps:
        for b in bays:
            prob += x[(a1, b)] + x[(a2, b)] <= 1

    # Solve
    solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=time_limit_seconds)
    prob.solve(solver)

    status = pulp.LpStatus[prob.status]
    assignments = []
    for f in flights:
        for b in bays:
            val = pulp.value(x[(f["id"], b)])
            if val is not None and val > 0.5:
                assignments.append({
                    "flight_id": f["id"],
                    "airline": f["airline"],
                    "atype": f["atype"],
                    "bay": b,
                    "revenue": revenue.get((f["airline"], f["atype"], b), 0.0)
                })

    total_revenue = pulp.value(prob.objective)
    return {"status": status, "total_revenue": total_revenue, "assignments": assignments}
