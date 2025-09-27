import sqlite3, os, textwrap

# Create folder
BASE = "fantasy_cricket_project"
os.makedirs(BASE, exist_ok=True)

# --- Create SQLite DB ---
db_path = os.path.join(BASE, "fantasy_cricket.db")
if os.path.exists(db_path):
    os.remove(db_path)

conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("""CREATE TABLE stats(
    player TEXT PRIMARY KEY, matches INT, runs INT, hundreds INT, fifties INT, value INT, ctg TEXT
)""")
cur.execute("""CREATE TABLE match(
    player TEXT PRIMARY KEY, scored INT, faced INT, fours INT, sixes INT, bowled INT, maiden INT,
    given INT, wkts INT, catches INT, stumping INT, ro INT
)""")
cur.execute("""CREATE TABLE teams(
    name TEXT PRIMARY KEY, players TEXT, value INT
)""")

# Insert sample players
sample_stats = [
    ("Rohit Sharma", 250, 9200, 30, 45, 110, "BAT"),
    ("Virat Kohli", 260, 12040, 43, 60, 125, "BAT"),
    ("Jasprit Bumrah", 120, 150, 0, 0, 95, "BWL"),
    ("Ravindra Jadeja", 180, 3400, 2, 18, 100, "AR"),
    ("MS Dhoni", 350, 10500, 10, 55, 130, "WK")
]
cur.executemany("INSERT INTO stats VALUES(?,?,?,?,?,?,?)", sample_stats)

# Insert sample match data
sample_match = [
    ("Rohit Sharma", 88, 55, 8, 3, 0, 0, 0, 0, 0, 0, 0),
    ("Virat Kohli", 102, 95, 10, 0, 0, 0, 0, 0, 0, 0, 0),
    ("Jasprit Bumrah", 0, 0, 0, 0, 8, 1, 20, 3, 0, 0, 0),
    ("Ravindra Jadeja", 45, 30, 6, 1, 4, 0, 25, 1, 1, 0, 0),
    ("MS Dhoni", 48, 30, 3, 1, 0, 0, 0, 0, 1, 0, 0)
]
cur.executemany("INSERT INTO match VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", sample_match)

conn.commit()
conn.close()

# --- Write main.py ---
main_code = textwrap.dedent("""\
    import sqlite3, sys
    from tkinter import *
    from tkinter import messagebox, simpledialog

    DB = "fantasy_cricket.db"

    def get_conn():
        return sqlite3.connect(DB)

    def fetch_players(category=None):
        conn = get_conn(); cur = conn.cursor()
        if category and category != "ALL":
            cur.execute("SELECT player, value, ctg FROM stats WHERE ctg=?", (category,))
        else:
            cur.execute("SELECT player, value, ctg FROM stats")
        rows = cur.fetchall(); conn.close()
        return rows

    def save_team_to_db(name, players, total_value):
        conn = get_conn(); cur = conn.cursor()
        cur.execute("INSERT OR REPLACE INTO teams VALUES(?,?,?)", (name, ",".join(players), total_value))
        conn.commit(); conn.close()

    def load_team_from_db(name):
        conn = get_conn(); cur = conn.cursor()
        cur.execute("SELECT players FROM teams WHERE name=?", (name,))
        row = cur.fetchone(); conn.close()
        return row[0].split(",") if row else []

    def calculate_player_points(player):
        conn = get_conn(); cur = conn.cursor()
        cur.execute("SELECT scored, faced, fours, sixes, bowled, maiden, given, wkts, catches, stumping, ro FROM match WHERE player=?", (player,))
        row = cur.fetchone(); conn.close()
        if not row: return 0
        scored, faced, fours, sixes, bowled, maiden, given, wkts, catches, stumping, ro = row
        pts = 0
        pts += scored // 2
        if scored >= 50: pts += 5
        if scored >= 100: pts += 10
        sr = (scored / faced * 100) if faced else 0
        if 80 <= sr < 100: pts += 2
        if sr >= 100: pts += 4
        pts += fours + (sixes * 2)
        pts += wkts * 10
        if wkts >= 3: pts += 5
        if wkts >= 5: pts += 10
        if bowled > 0:
            econ = given / bowled
            if 3.5 <= econ <= 4.5: pts += 4
            if 2 <= econ < 3.5: pts += 7
            if econ < 2: pts += 10
        pts += (catches + stumping + ro) * 10
        return pts

    # GUI
    root = Tk(); root.title("Fantasy Cricket"); root.geometry("750x450")
    Label(root, text="Fantasy Cricket - Student Project", font=("Arial", 16)).pack()

    left = Frame(root); left.pack(side=LEFT, padx=10)
    cat_var = StringVar(value="ALL")
    for c in ["ALL","BAT","BWL","AR","WK"]:
        Radiobutton(left, text=c, variable=cat_var, value=c, command=lambda: load_players()).pack(anchor=W)
    players_list = Listbox(left, width=35, height=15); players_list.pack(pady=5)

    mid = Frame(root); mid.pack(side=LEFT, padx=10)
    selected_list = Listbox(mid, width=35, height=15); selected_list.pack(pady=5)

    pts_frame = Frame(mid); pts_frame.pack()
    lbl_avail = Label(pts_frame, text="Available Points: 1000"); lbl_avail.pack(side=LEFT,padx=5)
    lbl_used = Label(pts_frame, text="Used: 0"); lbl_used.pack(side=LEFT,padx=5)
    available_points = 1000

    def load_players():
        players_list.delete(0, END)
        for p,v,c in fetch_players(cat_var.get()):
            players_list.insert(END, f"{p} | {c} | {v}")

    def get_val(entry): return int(entry.split(" | ")[2])

    def update_pts():
        used = sum(get_val(selected_list.get(i)) for i in range(selected_list.size()))
        lbl_used.config(text=f"Used: {used}")
        lbl_avail.config(text=f"Available Points: {available_points - used}")

    def add_player():
        sel = players_list.curselection()
        if not sel: return
        entry = players_list.get(sel)
        if selected_list.size() >= 11:
            messagebox.showerror("Error","Max 11 players")
            return
        used = sum(get_val(selected_list.get(i)) for i in range(selected_list.size()))
        if used + get_val(entry) > available_points:
            messagebox.showerror("Error","Not enough points")
            return
        selected_list.insert(END, entry); update_pts()

    def remove_player():
        sel = selected_list.curselection()
        if sel: selected_list.delete(sel); update_pts()

    def save_team():
        if selected_list.size()==0: return
        name = simpledialog.askstring("Team Name","Enter name:")
        if not name: return
        players = [selected_list.get(i).split(" | ")[0] for i in range(selected_list.size())]
        total = sum(get_val(selected_list.get(i)) for i in range(selected_list.size()))
        save_team_to_db(name, players, total)
        messagebox.showinfo("Saved",f"Team {name} saved!")

    def load_team():
        name = simpledialog.askstring("Load Team","Enter team name:")
        if not name: return
        players = load_team_from_db(name)
        selected_list.delete(0,END)
        allp = {p:(v,c) for p,v,c in fetch_players("ALL")}
        for p in players:
            if p in allp: v,c = allp[p]; selected_list.insert(END,f"{p} | {c} | {v}")
        update_pts()

    def evaluate():
        total=0; details=[]
        for i in range(selected_list.size()):
            n=selected_list.get(i).split(" | ")[0]; pts=calculate_player_points(n)
            details.append(f"{n}: {pts} pts"); total+=pts
        messagebox.showinfo("Evaluation","\\n".join(details)+f"\\n\\nTotal: {total}")

    Button(mid,text="Add ->",command=add_player).pack(pady=2)
    Button(mid,text="<- Remove",command=remove_player).pack(pady=2)
    Button(mid,text="Save Team",command=save_team).pack(pady=2)
    Button(mid,text="Load Team",command=load_team).pack(pady=2)
    Button(mid,text="Evaluate",command=evaluate).pack(pady=2)

    load_players()
    root.mainloop()
""")

with open(os.path.join(BASE, "main.py"), "w") as f:
    f.write(main_code)

# --- Write README.md ---
readme = textwrap.dedent("""\
    # 🏏 Fantasy Cricket (Student Project)

    A simple Fantasy Cricket game built using **Python, Tkinter, and SQLite3**.

    ## Features
    - Create a new team (max 11 players)
    - Add/remove players with points budget
    - Save and load teams from DB
    - Evaluate team score based on sample match data

    ## How to Run
    ```bash
    python3 main.py
    ```

    ## Notes
    - This is a **student-style project** with sample data.
    - It does not fetch live cricket scores.
""")
with open(os.path.join(BASE, "README.md"), "w") as f:
    f.write(readme)

print(f"Project files created in folder: {BASE}")
