from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a stronger one
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///talentrade.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ----------------------- MODELS -----------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(100))
    skills_have = db.Column(db.String(300))
    skills_want = db.Column(db.String(300))


# ----------------------- ROUTES -----------------------
@app.route('/')
def home():
    skills = get_skills()
    return render_template("home.html", skills=skills)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Optional: Check if user exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return "User already exists."

        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id
        return redirect(url_for('profile'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email, password=password).first()
        if user:
            session['user_id'] = user.id
            return redirect(url_for('profile'))
        else:
            return "Invalid credentials. Try again."
    return render_template('login.html')

@app.route('/profile')
def profile():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    user = User.query.get(user_id)
    user_data = {
        "username": user.username,
        "email": user.email,
        "have": user.skills_have.split(',') if user.skills_have else [],
        "want": user.skills_want.split(',') if user.skills_want else []
    }
    return render_template("profile.html", user=user_data)

@app.route('/register-skill', methods=["GET", "POST"])
def register_skill():
    skills = get_skills()
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    if request.method == "POST":
        skill_have = request.form.getlist("skill_have")
        skill_want = request.form.getlist("skill_want")
        user = User.query.get(user_id)
        user.skills_have = ",".join(skill_have)
        user.skills_want = ",".join(skill_want)
        db.session.commit()
        return redirect(url_for('profile'))

    return render_template("register_skill.html", skills=skills)

@app.route('/help')
def help():
    return render_template("help.html")

@app.route('/match')
def match():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    current_user = User.query.get(user_id)

    if not current_user.skills_have or not current_user.skills_want:
        return render_template("match.html", match_results=None)

    have_set = set(current_user.skills_have.split(','))
    want_set = set(current_user.skills_want.split(','))

    other_users = User.query.filter(User.id != current_user.id).all()

    # Build list of teachers who can teach skills you want
    matching_teachers = []
    for u in other_users:
        if u.skills_have:
            shared_skills = want_set.intersection(set(u.skills_have.split(',')))
            if shared_skills:
                matching_teachers.append({
                    "user": u,
                    "shared_skills": list(shared_skills)
                })

    # Build list of learners who want skills you have
    matching_learners = []
    for u in other_users:
        if u.skills_want:
            needed_skills = have_set.intersection(set(u.skills_want.split(',')))
            if needed_skills:
                matching_learners.append({
                    "user": u,
                    "shared_skills": list(needed_skills)
                })

    return render_template("match.html", match_results={
        "teachers": matching_teachers,
        "learners": matching_learners
    })

# ----------------------- HELPER -----------------------
def get_skills():
    return [
        "Graphic Design", "Python Coding", "Public Speaking", "Singing", "Photography",
        "Excel & Analytics", "Acting & Theatre", "Creative Writing", "C", "C++", "Java"
    ]


# -------------------- INIT DB ------------------------
@app.cli.command("initdb")
def initdb():
    db.create_all()
    print("✅ Database initialized!")


# -------------------- RUN APP ------------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)