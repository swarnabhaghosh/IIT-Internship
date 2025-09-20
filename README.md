### 1. `db.py` 

This file's only job is to **manage the database**, just stores and retrieves information.

- **What it does:**

1. `init_db()`: The first time the app runs, this function builds the database. It creates the tables and fills them with the default rules: how many bays exist (10), which aircraft types fit where, and how much revenue each parking spot generates.
2. `add_flight()`: When you add a new flight from the app, this function saves it to the `flights` table.
3. `get_...()`** functions**: These are used to read information. For example, `get_flights()` fetches the list of all flights you've added.
4. `reset_system()`: This function wipes all the data clean so you can start over.

---

### ## 2. `solver.py` 

It takes all the data and solves the complex puzzle of where to park the planes.

- **What it does:**

1. `detect_overlaps()`: First, it looks at the list of all flights and finds every pair that will be on the ground at the same time, creating a list of potential conflicts.
2. `solve_assignment()`: This is the main function. It builds a mathematical model of the problem with a clear goal and a set of rules:

- **Goal**: Maximize total revenue.
- **Rule 1**: A plane can't be assigned to a bay it's not compatible with.
- **Rule 2**: A plane can only be in one bay.
- **Rule 3**: Two planes that have a time conflict cannot share the same bay.
3. It then hands this puzzle to the **PuLP library**, which finds the single best ("optimal") solution. The results are then sent back to the app.

---

### ## 3. `app.py` (The Operations Dashboard)

This file creates the **web interface** you see and interact with. It acts as the bridge between you, the database, and the solver.

- **Workflow:**

1. **Display Data**: It calls `db.py` to get the current list of flights and displays them in a table on the screen.
2. **Get Your Input**: It shows the sidebar form where you can add new flights. When you click "Add Flight", it sends that information to `db.py` to be saved.
3. **Run the Scheduler**: When you click the "Run Scheduler" button, it wakes up the Chief Strategist (`solver.py`). It gathers all the latest data from the `db.py` file and hands it over to the `solve_assignment` function.
4. **Show the Results**: It gets the final plan back from the solver and displays the status, total revenue, and the final list of assignments on your screen.