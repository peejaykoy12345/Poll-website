from poll import app, db, bcrypt
from poll.forms import QuestionForm, ChoiceForm, RegistrationForm, LoginForm
from poll.models import User, Poll, Choice, Vote
from flask import render_template, flash, url_for, redirect, request, abort
from flask_login import login_user, current_user, logout_user, login_required

def vote(poll_id, will_return):
    poll = Poll.query.get_or_404(poll_id)
    if not poll: abort(404)
    selected_choice_id = request.form.get('choice')
    if selected_choice_id:
        existing_vote = Vote.query.filter_by(user_id=current_user.id, poll_id=poll.id).first()
        if existing_vote:
            flash('You have already voted on this poll!', 'danger')
            return redirect(url_for('home'))
        choice = Choice.query.get(int(selected_choice_id))
        if choice:
            choice.votes += 1
            db.session.add(Vote(user_id=current_user.id, poll_id=poll.id, choice_id=choice.id))
            db.session.commit()
            flash(f'You voted for {choice.text}!', 'success')
        else:
            flash('Invalid choice selected!', 'danger')
    else:
        flash('Please select a choice to vote!', 'danger')
    if will_return:
        return redirect(url_for('home'))

@app.route("/", methods=['GET', 'POST'])
@app.route("/home", methods=['GET', 'POST'])
def home():
    page = request.args.get('page', 1, type=int)
    polls = Poll.query.order_by(Poll.date_posted.desc()).paginate(page=page, per_page=10)
    return render_template('home.html', title='Home', polls=polls)

@app.route('/register', methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email = form.email.data, password = hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Your account has been created!', 'sucess')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit(): 
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash("Login unsuccessful", 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/poll_create", methods=['GET', 'POST'])
@login_required
def poll_create():
    form = QuestionForm()
    if form.validate_on_submit():
        poll = Poll(question=form.question.data, user_id=current_user.id)
        choices_added = 0
        db.session.add(poll)
        db.session.flush()  

        for c in form.choices.data:
            choice_text = c['choice'].strip()
            if choice_text:
                choice = Choice(text=choice_text, poll_id=poll.id)
                db.session.add(choice)
                choices_added += 1
            else:
                flash('Choice cannot be empty!', 'danger')

        if choices_added == 0:
            db.session.rollback()  
            flash('You must add at least one choice!', 'danger')
            return render_template('post.html', title='Create Poll', form=form)

        db.session.commit()
        flash('Your poll has been created!', 'success')
        return redirect(url_for('home'))  
    return render_template('post.html', title='Create Poll', form=form)

@app.route("/poll/<int:poll_id>", methods=['GET', 'POST'])
@login_required
def view_poll(poll_id):
    poll = Poll.query.get_or_404(poll_id)
    if not poll: abort(404)
    if request.method == 'POST':
        vote(poll_id, True)
    return render_template('view_poll.html', title='Poll', poll=poll)

@app.route("/post/<int:poll_id>/delete", methods=['POST'])
@login_required
def delete_post(poll_id):
    poll = Poll.query.get_or_404(poll_id)
    if poll.author != current_user:
        abort(403)
    db.session.delete(poll)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('home'))