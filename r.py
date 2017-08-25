from flask import Flask, render_template, url_for, request, redirect, jsonify
from forms import LoginForm, SignUpForm, NewListForm,NewItemForm
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required

            ######################### initialisation ##########################
app = Flask('__name__')
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://kenny3:kenny4@localhost:5432/db_four'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.config['SECRET_KEY'] = 'not_really_secret'
app.config['WTF_CSRF_ENABLED'] = False


            ####################### LOGIN & LOGOUT ############################
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'index'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
@app.route('/auth/login', methods=['POST'])
def login():
    form = LoginForm()
    usr = User.query.filter_by(email=str(request.form['email'])).first()
    if usr:
        if usr.password == form.password.data:
            login_user(usr)
            response = jsonify({'MSG':'Login Successful'})
            response.status_code = 200
        else:
            response = jsonify({'ERR':'Incorrect Password'})
            response.status_code = 401
    else:
        response = jsonify({'ERR': 'User does not exist'})
        response.status_code = 404
    return response

@app.route('/auth/register', methods=['POST'])
def register():  
    form = SignUpForm()
    if form.validate_on_submit():
        usr = User(str(request.form['email']), str(request.form['password']))
        if usr:
            db.session.add(usr)
            db.session.commit()
            response = jsonify({'MSG':'Success'})
            response.status_code = 200
        else:
            response = jsonify({'ERR':'User object wasnt created.'})
            response.status_code = 400
    else:
        response = jsonify({'ERR': form.errors})
        response.status_code = 400
    return response

            ####################### MODELS ####################################
class User(db.Model, UserMixin):
    """This class represents the user table"""
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(16))
    lists = db.relationship('ShoppingList', backref='user', lazy='dynamic')

    def __init__(self, email, password):
        self.email = email
        self.password = password

class ShoppingList(db.Model):
    """This class represents the shopping_list table"""
    __tablename__ = 'shopping_list'
    id = db.Column(db.Integer, primary_key=True)
    list_name = db.Column(db.String(64), unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, list_name):
        self.list_name = list_name
    
    @property 
    def serialize(self):
        """Return object data in easily serializeable format"""
        return { 'list_name': self.list_name }

class Item(db.Model):
    """This class represents the item table"""
    __tablename__ = 'items'
    item_id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(32))
    quantity = db.Column(db.Integer)
    list_id = db.Column(db.Integer, db.ForeignKey('shopping_list.id'))#change to id

    def __init__(self, item_name, list_name, quantity=1):
        self.item_name = item_name
        self.list_name = list_name
        self.quantity = quantity
    
    @property 
    def serialize(self):
        """Return object data in easily serializeable format"""
        return { 'item_name': self.list_name, 'list_id': self.list_id }


            ###################### views and routing functions##################
@app.route('/shoppinglist', methods=['GET'])
def view_all_lists():
    all_sh_lists = ShoppingList.query.all()
    if all_sh_lists is not None:
        response = jsonify([obj.serialize for obj in all_sh_lists])
        response.status_code = 200
    else:
        response = jsonify({'ERR':'No lists returned.'})
        response.status_code = 404
    return response

@app.route('/shoppinglist', methods=['POST'])
def create_list():
    form = NewListForm()   
    new_list = ShoppingList(request.form['list_name'])
    if new_list is not None:
        db.session.add(new_list)
        db.session.commit()
        response = jsonify({'MSG': 'Success'})
        response.status_code = 201
    else:
        response = jsonify({'ERR':'List was not created'})                
        response.status_code = 400
    return response

@app.route('/shoppinglist/<id>', methods = ['DELETE'])
def delete_list(id):
    del_list = ShoppingList.query.filter_by(id=id).one()
    if del_list is not None:
        db.session.delete(del_list)
        db.session.commit()
        response = jsonify({'MSG':'Success'})
        response.status_code = 204
    else:
        response = jsonify({'ERR':'Requested list was not found'})
        response.status_code = 404
    return response

@app.route('/shoppinglist/<id>', methods=['GET'])
def view_list(id):
    list_items = Item.query.filter_by(id=id).all()
    if list_items is not None:
        response = jsonify(list_items)
        response.status_code = 200
    else:
        response = jsonify({'ERR':'List items not Found'})
        response.status_code = 400
    return response

@app.route('/shoppinglists/<id>/item/', methods=['POST'])
def add_item(id):
    form = NewItemForm()
    new_item = Item(request.form['item_name'], id)
    if new_item is not None:
        db.session.add(new_item)
        db.session.commit()
        response = jsonify({'MSG': 'Item added to list'})
        response.status_code = 201
    else:
        response.jsonify({'ERR':'Item wasnt added to list'})
        response.status_code = 400
    return response

@app.route('/shoppinglists/<id>/items/<item_id>', methods=['DELETE'])
def delete_item(id, item_id):
    del_item = Item.query.filter_by(id=id, item_id=item_id).one()
    if del_item is not None:
        db.session.delete(del_item)
        db.session.commit()
        response = jsonify({'MSG':'Success'})
        response.status_code = 204
    else:
        response = jsonify({'ERR':'Requested item was not found'})
        response.status_code = 404
    return response 

# -----------------------------------------------------------------------------------------------------------------------------------------------
db.create_all()
if __name__ == '__main__':
    app.run(debug=True)
