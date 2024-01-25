from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response
from flask_sqlalchemy import SQLAlchemy
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

class Itinerary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    num_days = db.Column(db.Integer, nullable=False)  # New field
    description = db.Column(db.Text, nullable=False)


@app.route('/')
def index():
    return redirect(url_for('home'))

# Register page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')

        # Check if the username or email already exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            return "User with this username or email already exists!"

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password=hashed_password, email=email)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        # Check if the user exists and the password is correct
        if not user or not check_password_hash(user.password, password):
            return "Invalid username or password!"

        # The user has been authenticated, save their id in the session
        session['user_id'] = user.id

        return redirect(url_for('home'))

    return render_template('login.html')

# Home page
@app.route('/home')
def home():
    # Check if the user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Get the user's itineraries
    itineraries = Itinerary.query.filter_by(user_id=session['user_id']).all()

    return render_template('home.html', itineraries=itineraries)


# Create itinerary page
@app.route('/create_itinerary', methods=['GET', 'POST'])
def create_itinerary():
    if request.method == 'POST':
        destination = request.form['destination']
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
        num_days = (end_date - start_date).days + 1  # Calculate number of days
        description = request.form['description']

        new_itinerary = Itinerary(user_id=session['user_id'], destination=destination, start_date=start_date, end_date=end_date, num_days=num_days, description=description)
        db.session.add(new_itinerary)
        db.session.commit()

        flash('Itinerary created!')
        return redirect(url_for('home'))

    return render_template('create_itinerary.html')


# Delete itinerary
@app.route('/delete_itinerary/<int:id>', methods=['POST'])
def delete_itinerary(id):
    # Check if the user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))

    itinerary = Itinerary.query.get(id)
    db.session.delete(itinerary)
    db.session.commit()
    return redirect(url_for('home'))

## Suggestions page
@app.route('/suggestions')
def suggestions():
    # Check if the user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Here you can add your own suggestions
    suggestions = [
        {'destination': 'Paris , The city of love', 'description': 'Explore the iconic landmarks of Paris with visits to the Eiffel Tower, Louvre Museum, and Notre-Dame Cathedral. Immerse yourself in the vibrant culture of Paris by attending a cabaret show at the Moulin Rouge, taking a leisurely stroll along the Champs-Élysées, and discovering the charm of its picturesque neighborhoods.'},
        {'destination': 'Rome, The eternal city', 'description': 'Uncover the splendors of Rome, where the iconic Colosseum narrates tales of ancient glory. Traverse the historic Roman Forum, a living testament to the enduring legacy of the city, and be captivated by the artistic wonders of Vatican City, home to St. Peters Basilica and the timeless Sistine Chapel. Wander through the charming Trastevere districts cobblestone streets, explore the mysterious Roman Catacombs, and savor the elegance of the Spanish Steps. Immerse yourself in the art of Italian cuisine with a delightful cooking class, weaving together history, culture, and culinary delights in the heart of Rome.'},
        {'destination': 'Barcelona, a Symphony of Colors', 'description': 'Embark on a sensory journey through Barcelona, where the Gothic quarters reveal architectural treasures and the iconic Sagrada Familia captivates with its unique beauty. Stroll along the vibrant La Rambla, absorbing the lively atmosphere of the city, and relish the sun-kissed beaches. Experience the passion of Spain with a flamenco show, be enchanted by the Magic Fountain of Montjuïc, and pedal through the green oasis of Vondelpark. Delve into the allure of the Red Light District, and explore the vibrant hues of the Flower Market.'},
        {'destination': 'Prague, the Fairytale Capital', 'description': 'Embark on a captivating journey in Prague, where the historic charm of Prague Castle, the timeless allure of Charles Bridge, and the enchanting rhythms of Old Town Square with the Astronomical Clock await. Dive into the soul of the city with a scenic cruise on the Vltava River, a leisurely walk through Petřín Park, and an exploration of the rich cultural tapestry in the historic Jewish Quarter, creating an unforgettable symphony of history and leisure.'},
        {'destination': 'Amsterdam, the City of Canals', 'description': 'Immerse yourself in the cultural gems of the city at the Anne Frank House, Van Gogh Museum, and Rijksmuseum, then soak in the charm with a canal cruise and a stroll through the Jordaan District. Dive into local life with a bike ride through Vondelpark, an exploration of the Red Light District, and a visit to the vibrant Flower Market, creating a perfect blend of art, history, and unique atmosphere of Amsterdam.'},
        {'destination': 'Dubrovnik, the Pearl of the Adriatic', 'description': 'Uncover the charm of Dubrovnik with a visit to the historic City Walls, Old Town, and the elegant Rector Palace. Immerse yourself in the vibrancy of the city by strolling along Stradun (Placa) and embarking on a captivating Game of Thrones tour to explore filming locations, creating a perfect blend of rich history and cinematic allure.'},
        {'destination': 'Edinburgh, the Regal Enclave', 'description': 'Experience the essence of Edinburgh by exploring the historic Edinburgh Castle, wandering down the Royal Mile, and hiking up to Arthur Seat for breathtaking views. Immerse yourself in the city mystique by climbing Calton Hill, joining a ghost tour in the Old Town, and, during the season, attending the world-renowned Edinburgh Festival Fringe, creating an unforgettable blend of history, nature, and cultural vibrancy.'}
    ]

    return render_template('suggestions.html', suggestions=suggestions)

# Download itineraries as PDF
@app.route('/download_itineraries')
def download_itineraries():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    itineraries = Itinerary.query.filter_by(user_id=session['user_id']).all()

    if not itineraries:
        flash('No itineraries to download.')
        return redirect(url_for('home'))

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"itineraries_{timestamp}.pdf"
    output_path = os.path.join(os.getcwd(), filename)
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter

    y = height - 50  # Start from the top of the page

    for itinerary in itineraries:
        c.drawString(30, y, f"Destination: {itinerary.destination}")
        y -= 15  # Move down for the next line
        c.drawString(30, y, f"Start Date: {itinerary.start_date}")
        y -= 15
        c.drawString(30, y, f"End Date: {itinerary.end_date}")
        y -= 15
        c.drawString(30, y, f"Number of Days: {itinerary.num_days}")  # New line
        y -= 15
        c.drawString(30, y, f"Description: {itinerary.description}")
        y -= 20  # Add some extra space between itineraries

    c.save()

    flash("PDF has been saved to {}".format(output_path))
    return redirect(url_for('home'))

# Logout option
@app.route('/logout')
def logout():
    # Remove the user id from the session
    session.pop('user_id', None)

    return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
