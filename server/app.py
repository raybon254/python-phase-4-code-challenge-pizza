#!/usr/bin/env python3
from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, make_response, jsonify
from flask_restful import Api, Resource
from flask_cors import CORS
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

CORS(app)

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)

class Restaurants(Resource):
    def get(self):
        restaurants = Restaurant.query.all()
        return make_response([restaurant.to_dict() for restaurant in restaurants], 200)


class RestaurantByID(Resource):
    def get(self, id):
        restaurant = Restaurant.query.get(id)
        if not restaurant:
            return make_response(jsonify({"error": "Restaurant not found"}), 404)
        return make_response(jsonify({
            "address": restaurant.address,
            "id": restaurant.id,
            "name": restaurant.name,
            "restaurant_pizzas": [rp.to_dict() for rp in restaurant.restaurant_pizzas]
        }), 200)
    
    def delete(self, id):
        restaurant = Restaurant.query.get(id)

        if not restaurant:
            return make_response(jsonify({"error": "Restaurant not found"}), 404)

        for rp in restaurant.restaurant_pizzas:
            db.session.delete(rp)

        db.session.delete(restaurant)
        db.session.commit()
        return make_response('', 204)
    
class Pizzas(Resource):
    def get(self):
        pizzas = Pizza.query.all()
        return make_response([pizza.to_dict() for pizza in pizzas], 200)
    
class RestaurantPizzas(Resource):
    def post(self):
        data = request.get_json()
        price = data.get('price')
        pizza_id = int(data.get('pizza_id'))
        restaurant_id = int(data.get('restaurant_id'))

        pizza = Pizza.query.get(pizza_id)
        restaurant = Restaurant.query.get(restaurant_id)

        if not pizza or not restaurant:
            return make_response(jsonify({"errors": ["Validation failed: Invalid pizza or restaurant"]}), 400)
        
        try:
            new_rp = RestaurantPizza(
                price=price,
                pizza_id=pizza_id,
                restaurant_id=restaurant_id
            )
            db.session.add(new_rp)
            db.session.commit()

        except ValueError as ve:
            return make_response(jsonify({"errors": ["validation errors"]}), 400)

        response_data = {
            "id": new_rp.id,
            "price": new_rp.price,
            "pizza_id": new_rp.pizza_id,
            "restaurant_id": new_rp.restaurant.id,
            "pizza": {
                "id": new_rp.pizza.id,
                "name": new_rp.pizza.name,
                "ingredients": new_rp.pizza.ingredients
            },
            "restaurant": {
                "id": new_rp.restaurant.id,
                "name": new_rp.restaurant.name,
                "address": new_rp.restaurant.address
            }
        }

        return make_response(jsonify(response_data), 201)


api.add_resource(Pizzas, '/pizzas')

api.add_resource(Restaurants, '/restaurants')
api.add_resource(RestaurantByID, '/restaurants/<int:id>')

api.add_resource(RestaurantPizzas, '/restaurant_pizzas')

@app.route("/")
def index():
    return "<h1>Code challenge</h1>"


if __name__ == "__main__":
    app.run(port=5555, debug=True)