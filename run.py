from poll import app, db
from poll.models import Poll, User, Choice  

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True) 