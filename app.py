from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import datetime
import jwt
import os

#Init app
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
# Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Init db
db = SQLAlchemy(app)
# Init ma
ma = Marshmallow(app)


###### Product Table ########
# Product Class/Model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    qty = db.Column(db.Integer, nullable=False)
    purchased = db.Column(db.Boolean)

    seller_id = db.Column(db.Integer, db.ForeignKey('seller.id'),nullable=False)



    def __init__(self, name, price, qty, purchased, seller_id):
        self.name = name
        self.price = price
        self.qty = qty
        self.purchased = purchased
        self.seller_id = seller_id

    def toString(self):
        return ({'name':self.name, 'price':self.price, 'qty':self.qty, 'purchased':self.purchased, 'seller_id':self.seller_id})

# Product Schema
class ProductSchema(ma.Schema):
    class Meta:
        fields = ('name', 'price', 'qty', 'purchased', 'seller_id' )

# Init schema
product_schema = ProductSchema(strict=True)
products_schema = ProductSchema(many=True, strict=True)

# Create a Product
@app.route('/product', methods=['POST'])
def add_products():
    name = request.json['name']
    price = request.json['price']
    qty = request.json['qty']
    purchased = request.json['purchased']
    seller_id = request.json['seller_id']

    new_product = Product(name, price, qty, purchased, seller_id)

    db.session.add(new_product)
    db.session.commit()

    return product_schema.jsonify(new_product)

# Get all products
@app.route('/product', methods=['GET'])
def get_products():
    all_products = Product.query.all()
    result = products_schema.dump(all_products)
    return jsonify(result.data)

# Get one products
@app.route('/product/<id>', methods=['GET'])
def get_product(id):
    product = Product.query.filter_by(seller_id = id).all()
    v = [products.toString() for products in product]
    return jsonify(product = v)

# Update a Product
@app.route('/product/<id>', methods=['PUT'])
def update_products(id):
    product = Product.query.get(id)

    price = request.json['price']
    qty = request.json['qty']
    purchased = request.json['purchased']

    product.price = price
    product.qty = qty
    product.purchased = purchased

    db.session.commit()

    return product_schema.jsonify(product)

# Delete products
@app.route('/product/<id>', methods=['DELETE'])
def delete_product(id):
    product = Product.query.get(id)
    db.session.delete(product)

    db.session.commit()
    
    return product_schema.jsonify(product)

###### Product Table ########


###### Seller Table ########
# Seller Model/Class
class Seller(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fname = db.Column(db.String(100), nullable=False)
    lname =db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    address = db.Column(db.String(30), nullable=False)
    seller_email = db.Column(db.String(100), nullable=False)
    seller_password = db.Column(db.String(100), nullable=False)

    product = db.relationship('Product', backref='seller', cascade = 'all, delete-orphan', lazy = 'dynamic')

    def __init__(self, fname, lname, phone, address, seller_email, seller_password):
        self.fname = fname
        self.lname = lname
        self.phone = phone
        self.address = address
        self.seller_email = seller_email
        self.seller_password = seller_password

# Seller Schema
class SellerSchema(ma.Schema):
    class Meta:
        fields = ('fname', 'lname', 'phone', 'address', 'seller_email', 'seller_password')

# Init schema
seller_schema = SellerSchema(strict=True)
sellers_schema = SellerSchema(many=True, strict=True)


    # def post(self):
    #     json_data = request.get_json(force=True)
    #     if not json_data:
    #            return {'message': 'No input data provided'}, 400
    #     # Validate and deserialize input
    #     data, errors = category_schema.load(json_data)
    #     if errors:
    #         return errors, 422
    #     category = Category.query.filter_by(name=data['name']).first()
    #     if category:
    #         return {'message': 'Category already exists'}, 400
    #     category = Category(
    #         name=json_data['name']
    #         )

    #     db.session.add(category)
    #     db.session.commit()

    #     result = category_schema.dump(category).data

    #     return { "status": 'success', 'data': result }, 201

# Add a Seller
@app.route('/seller', methods=['POST'])
def add_seller():
    data = request.get_json()

    fname = data['fname']
    lname = data['lname']
    phone = data['phone']
    address = data['address']
    seller_email = data['seller_email']
    seller_password = data['seller_password']
    seller_password = generate_password_hash(seller_password, method='sha256')

    new_seller = Seller(fname, lname, phone, address, seller_email, seller_password)

    db.session.add(new_seller)
    db.session.commit()

    return seller_schema.jsonify(new_seller)

# Get all sellers
@app.route('/seller', methods=['GET'])
def get_sellers():
    all_sellers = Seller.query.all()
    result = sellers_schema.dump(all_sellers)
    return jsonify(result.data)

# Update a Seller
@app.route('/seller/<id>', methods=['PUT'])
def update_seller(id):
    seller = Seller.query.get(id)

    phone = request.json['phone']
    address = request.json['address']
    seller_password = request.json['seller_password']
    

    seller.phone = phone
    seller.address = address
    seller.seller_password = seller_password

    db.session.commit()

    return seller_schema.jsonify(seller)

# Delete sellers
@app.route('/seller/<id>', methods=['DELETE'])
def delete_seller(id):
    seller = Seller.query.get(id)
    db.session.delete(seller)

    db.session.commit()
    
    return seller_schema.jsonify(seller)

# Login Seller
@app.route('/seller/login')
def sellerLogin():
    auth = request.authorization

    if not auth or not auth.username or not auth.password:
        return jsonify('Could not verify', 401, {'WW-Authenticate' : 'Basic realm="Login required!"'})

    seller = Seller.query.filter_by(seller_email=auth.username).first()

    if not seller:
        return jsonify({'message' : 'Invalid User'})

    if check_password_hash(seller.seller_password, auth.password):
        token = jwt.encode({'id' : seller.id, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])

        return jsonify({'token' : token.decode('UTF-8')})

    return jsonify({'message' : 'Invalid Password'})


###### Seller Table ########

###### Buyer Table ########
# Buyer Model/Class
class Buyer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fname = db.Column(db.String(100), nullable=False)
    lname =db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)    
    address = db.Column(db.String(30), nullable=False)
    buyer_email = db.Column(db.String(100), nullable=False)
    buyer_password = db.Column(db.String(100), nullable=False)

    def __init__(self, fname, lname, phone, address, buyer_email, buyer_password):
        self.fname = fname
        self.lname = lname
        self.phone = phone
        self.address = address
        self.buyer_email = buyer_email
        self.buyer_password = buyer_password

# Buyer Schema
class BuyerSchema(ma.Schema):
    class Meta:
        fields = ('fname', 'lname', 'phone', 'address', 'buyer_email', 'buyer_password')

# Init schema
buyer_schema = BuyerSchema(strict=True)
buyers_schema = BuyerSchema(many=True, strict=True)

# Add a Buyer
@app.route('/buyer', methods=['POST'])
def add_buyer():
    fname = request.json['fname']
    lname = request.json['lname']
    phone = request.json['phone']
    address = request.json['address']
    buyer_email = request.json['buyer_email']
    buyer_password = request.json['buyer_password']
    buyer_password = generate_password_hash(buyer_password, method='sha256')

    new_buyer = Buyer(fname, lname, phone, address, buyer_email, buyer_password)

    db.session.add(new_buyer)
    db.session.commit()

    return buyer_schema.jsonify(new_buyer)

# Get all buyers
@app.route('/buyer', methods=['GET'])
def get_buyers():
    all_buyers = Buyer.query.all()
    result = buyers_schema.dump(all_buyers)
    return jsonify(result.data)

# Update a Buyer
@app.route('/buyer/<id>', methods=['PUT'])
def update_buyer(id):
    buyer = Buyer.query.get(id)

    phone = request.json['phone']
    address = request.json['address']
    buyer_password = request.json['buyer_password']
    

    buyer.phone = phone
    buyer.address = address
    buyer.buyer_password = buyer_password

    db.session.commit()

    return seller_schema.jsonify(buyer)

# Delete buyers
@app.route('/buyer/<id>', methods=['DELETE'])
def delete_buyer(id):
    product = Product.query.get(id)
    db.session.delete(product)

    db.session.commit()
    
    return product_schema.jsonify(product)
###### Buyer Table ########


###### Transaction Table ########
# Transaction Model/Class
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime, nullable=False)
    amount =db.Column(db.String(100), nullable=False)

    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    product = db.relationship('Product', backref=db.backref('posts', lazy=True))

    buyer_id = db.Column(db.Integer, db.ForeignKey('buyer.id'), nullable=False)
    buyer = db.relationship('Buyer', backref=db.backref('posts', lazy=True))
    
    def __init__(self, date_created, amount, product_id, buyer_id):
        self.date_created = date_created
        self.amount = amount
        self.product_id = product_id
        self.buyer_id = buyer_id

# Transaction Schema
class TransactionSchema(ma.Schema):
    class Meta:
        fields = ('id', 'date_created', 'amount', 'product_id', 'buyer_id')

# Init schema
transaction_schema = TransactionSchema(strict=True)
transaction_schema = TransactionSchema(many=True, strict=True)
###### Transaction Table ########


#Run Server
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    # app.run(debug=True)