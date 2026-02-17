from flask import Flask, render_template, request, redirect, session, url_for
import os
import uuid

app = Flask(__name__)
app.secret_key = "supersecretkey"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USER_FILE = os.path.join(BASE_DIR, "users.txt")
EXPENSE_FILE = os.path.join(BASE_DIR, "expenses.txt")

# Create files if not exist
for file in [USER_FILE, EXPENSE_FILE]:
    if not os.path.exists(file):
        open(file, "w").close()


def read_expenses():
    expenses = []
    with open(EXPENSE_FILE, "r") as f:
        for line in f:
            parts = line.strip().split(",")

            if len(parts) != 6:
                continue

            exp_id, username, date, category, amount, description = parts

            if username == session.get("user"):
                expenses.append({
                    "id": exp_id,
                    "date": date,
                    "category": category,
                    "amount": float(amount),
                    "description": description
                })
    return expenses


@app.route("/")
def home():
    if "user" not in session:
        return redirect("/login")

    expenses = read_expenses()
    total = sum(e["amount"] for e in expenses)

    return render_template("index.html", expenses=expenses, total=total)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        with open(USER_FILE, "r") as f:
            for line in f:
                saved_user, _ = line.strip().split(",")
                if saved_user == username:
                    return "User already exists!"

        with open(USER_FILE, "a") as f:
            f.write(f"{username},{password}\n")

        return redirect("/login")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        with open(USER_FILE, "r") as f:
            for line in f:
                saved_user, saved_pass = line.strip().split(",")
                if saved_user == username and saved_pass == password:
                    session["user"] = username
                    return redirect("/")

        return "Invalid credentials!"

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")


@app.route("/add", methods=["GET", "POST"])
def add_expense():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        exp_id = str(uuid.uuid4())[:8]
        date = request.form["date"]
        category = request.form["category"]
        amount = request.form["amount"]
        description = request.form["description"]

        with open(EXPENSE_FILE, "a") as f:
            f.write(f"{exp_id},{session['user']},{date},{category},{amount},{description}\n")

        return redirect("/")

    return render_template("add_expense.html")


@app.route("/delete/<id>")
def delete_expense(id):
    if "user" not in session:
        return redirect("/login")

    lines = []
    with open(EXPENSE_FILE, "r") as f:
        for line in f:
            if not line.startswith(id):
                lines.append(line)

    with open(EXPENSE_FILE, "w") as f:
        f.writelines(lines)

    return redirect("/")


@app.route("/edit/<id>", methods=["GET", "POST"])
def edit_expense(id):
    if "user" not in session:
        return redirect("/login")

    expenses = read_expenses()
    expense = next((e for e in expenses if e["id"] == id), None)

    if request.method == "POST":
        new_lines = []
        with open(EXPENSE_FILE, "r") as f:
            for line in f:
                parts = line.strip().split(",")
                if parts[0] == id:
                    new_lines.append(
                        f"{id},{session['user']},{request.form['date']},{request.form['category']},{request.form['amount']},{request.form['description']}\n"
                    )
                else:
                    new_lines.append(line)

        with open(EXPENSE_FILE, "w") as f:
            f.writelines(new_lines)

        return redirect("/")

    return render_template("edit_expense.html", expense=expense)


@app.route("/summary")
def summary():
    if "user" not in session:
        return redirect("/login")

    expenses = read_expenses()
    category_data = {}

    for e in expenses:
        category_data[e["category"]] = category_data.get(e["category"], 0) + e["amount"]

    return render_template("summary.html", category_data=category_data)


if __name__ == "__main__":
    app.run(debug=True)

