import streamlit as st
import pandas as pd
from datetime import datetime
import db
from solver import detect_overlaps, solve_assignment

# Initialize Streamlit
st.set_page_config(page_title="Aircraft Parking Scheduler", layout="wide")
st.title("Aircraft Parking Scheduler (DB Version)")

# Session State
if "refresh" not in st.session_state:
    st.session_state.refresh = 0

if "reset_trigger" not in st.session_state:
    st.session_state.reset_trigger = False

if "depart_triggered" not in st.session_state:
    st.session_state.depart_triggered = None

# Initialize DB
db.init_db()

# Add New Flight
st.sidebar.header("Add New Flight")
with st.sidebar.form("new_flight"):
    fid = st.text_input("Flight Number / ID")
    airline = st.text_input("Airline")
    atype = st.text_input("Aircraft Type")
    arr_date = st.date_input("Arrival Date")
    arr_time = st.time_input("Arrival Time")
    dep_date = st.date_input("Departure Date")
    dep_time = st.time_input("Departure Time")
    submit = st.form_submit_button("Add Flight")

if submit:
    try:
        arr = datetime.combine(arr_date, arr_time)
        dep = datetime.combine(dep_date, dep_time)
        db.add_flight(fid.strip(), airline.strip(), atype.strip(), arr, dep)
        st.sidebar.success(f"Flight {airline}_{fid} added.")
        st.session_state.refresh += 1
    except ValueError as ve:
        st.sidebar.error(str(ve))
    except Exception as e:
        st.sidebar.error(f"Error: {e}")

# Reset System
if st.sidebar.button("Reset System"):
    db.reset_system()
    st.sidebar.success("System reset. All data cleared.")
    st.session_state.reset_trigger = True

if st.session_state.reset_trigger:
    st.session_state.refresh += 1
    st.session_state.reset_trigger = False

_ = st.session_state.refresh  # Force rerender

# Current Flights
st.subheader("Current Flights")
flights_raw = db.get_flights()

if flights_raw:
    flights_list = []
    for row in flights_raw:
        flights_list.append({
            "id": row[0],
            "airline_id": row[1],
            "airline": row[2],
            "atype": row[3],
            "arr": pd.to_datetime(row[4]),
            "dep": pd.to_datetime(row[5])
        })

    df_flights = pd.DataFrame(flights_list)
    df_flights["Arrival"] = df_flights["arr"].dt.strftime("%Y-%m-%d %H:%M")
    df_flights["Departure"] = df_flights["dep"].dt.strftime("%Y-%m-%d %H:%M")
    st.dataframe(df_flights[["id","airline_id","airline","atype","Arrival","Departure"]], use_container_width=True)

    st.write("**Mark flights as departed:**")

    # for f in flights_list:
    #     col1, col2 = st.columns([4,1])
    #     with col1:
    #         st.write(f"Flight {f['id']} ({f['airline']} - {f['atype']})")
    #     with col2:
    #         button_key = f"depart_{f['id']}"
    #         if st.button("Depart", key=button_key):
    #             db.delete_flight(f["id"])
    #             st.session_state.depart_triggered = f["id"]
    #             st.session_state.refresh += 1


    # # Force rerender if a flight was departed
    # if st.session_state.depart_triggered:
    #     st.session_state.depart_triggered = None
    #     st.rerun() if hasattr(st, "experimental_rerun") else None

    st.write("**Mark flights as departed:**")

    departed_flight = None

    for f in flights_list:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(f"Flight {f['id']} ({f['airline']} - {f['atype']})")
        with col2:
            button_key = f"depart_{f['id']}"
            if st.button("Depart", key=button_key):
                departed_flight = f["id"]

    # After the loop, handle departure
    if departed_flight:
        db.delete_flight(departed_flight)
        st.session_state.refresh += 1
        st.rerun()  # This now runs after the button processing


else:
    st.info("No flights added yet.")

# Run Scheduler
if st.button("Run Scheduler"):
    if not flights_raw:
        st.warning("⚠️ No flights to schedule.")
    else:
        bays = db.get_bays()
        comp = db.get_compatibility()
        revenue = db.get_revenue()
        overlaps = detect_overlaps(flights_list)
        result = solve_assignment(flights_list, bays, comp, revenue, overlaps)

        st.subheader("Solver Status")
        st.write(result["status"])

        st.subheader("Total Revenue")
        st.metric("Revenue", f"{result['total_revenue']:.2f}")

        st.subheader("Assignments")
        if result["assignments"]:
            df_out = pd.DataFrame(result["assignments"])
            st.dataframe(df_out, use_container_width=True)
        else:
            st.warning("No feasible assignments found!")
