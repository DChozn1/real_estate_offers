from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.exceptions import HTTPException

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///offers.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Offer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    realtor_name = db.Column(db.String(100), nullable=False)
    offer_amount = db.Column(db.Float, nullable=False)
    is_cash = db.Column(db.Boolean, nullable=False)
    contingencies = db.Column(db.String(200), nullable=False)
    closing_time = db.Column(db.Integer, nullable=False)  # days to close
    is_valid = db.Column(db.Boolean, nullable=False, default=True)  # New field

    def __init__(self, realtor_name, offer_amount, is_cash, contingencies, closing_time, is_valid=True):
        self.realtor_name = realtor_name
        self.offer_amount = offer_amount
        self.is_cash = is_cash
        self.contingencies = contingencies
        self.closing_time = closing_time
        self.is_valid = is_valid

@app.route('/')
def index():
    return "Welcome to the Real Estate Offer Submission API"

@app.route('/submit_offer', methods=['POST'])
def submit_offer():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No input data provided"}), 400

    try:
        realtor_name = data['realtor_name']
        offer_amount = data['offer_amount']
        is_cash = data['is_cash']
        contingencies = data['contingencies']
        closing_time = data['closing_time']
    except KeyError as e:
        return jsonify({"error": f"Missing field: {e.args[0]}"}), 400

    is_valid = True
    if offer_amount <= 0 or closing_time <= 0:
        is_valid = False

    try:
        new_offer = Offer(
            realtor_name=realtor_name,
            offer_amount=offer_amount,
            is_cash=is_cash,
            contingencies=contingencies,
            closing_time=closing_time,
            is_valid=is_valid
        )
        db.session.add(new_offer)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to submit offer"}), 500

    return jsonify({"message": "Offer submitted successfully!"}), 201

@app.route('/offer_statistics', methods=['GET'])
def offer_statistics():
    offers = Offer.query.all()
    valid_offers = [offer for offer in offers if offer.is_valid]
    invalid_offers = [offer for offer in offers if not offer.is_valid]
    num_offers = len(valid_offers)
    num_cash_offers = len([offer for offer in valid_offers if offer.is_cash])
    num_over_list = len([offer for offer in valid_offers if offer.offer_amount > 500000])  # Example list price
    avg_closing_time = sum([offer.closing_time for offer in valid_offers]) / num_offers if num_offers else 0

    return jsonify({
        "num_offers": num_offers,
        "num_cash_offers": num_cash_offers,
        "num_over_list": num_over_list,
        "avg_closing_time": avg_closing_time,
        "num_invalid_offers": len(invalid_offers)
    })

@app.errorhandler(HTTPException)
def handle_exception(e):
    response = e.get_response()
    response.data = jsonify({"error": str(e)}).data
    response.content_type = "application/json"
    return response

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
