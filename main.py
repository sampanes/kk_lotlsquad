<<<<<<< HEAD
=======
import json
from email.policy import default
>>>>>>> 82ad35d4209be7e8a9bd02e8575811f8a6b5d34f
from flask import Flask, render_template, request, redirect, flash, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from datetime import datetime, date
from flask_login import (
    LoginManager,
    UserMixin,
    login_required,
    current_user,
    login_user,
    logout_user,
)
from numpy import product
from werkzeug.utils import secure_filename
from PIL import Image
import pymysql
from sqlalchemy.sql import func

pymysql.install_as_MySQLdb()
from sqlalchemy import and_, or_, not_
import auth
from flask_cors import CORS
from flask_admin.contrib.sqla import ModelView
from flask_admin import Admin
import stripe

app = Flask(__name__)
app.config[
    "SECRET_KEY"
] = "Ywurow503985403924482jfsoakldfjasdltu394qipoafjo48950wjsfpas;lkr04589"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.sqlite"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_PERMANENT"] = True
app.config["SESSION_TYPE"] = "filesystem"
app.config['STRIPE_PUBLIC_KEY'] = 'pk_test_51Maq2FIcCIyr3xbcANbSwtE2B3SQb6WRwXWIGv8HcIwVdCAzdsuj70G3kyMCx95j2qFc3bMU0O724stq92HefEBs00xbmO8BsL'
app.config['STRIPE_SECRET_KEY'] = 'sk_test_51Maq2FIcCIyr3xbc7Pf7DIQFupgbmsgp4FlZOrec4Byg6qaulgLlFiJ6nckQwRnTVDdUS2nKKLNDv2NpGbQUI5XT00XeggezUz'


stripe.api_key =  app.config['STRIPE_SECRET_KEY']
db = SQLAlchemy(app)
Migrate(app, db)
CORS(app)
login_manager = LoginManager()

now = datetime.now()
login_manager.init_app(app)
login_manager.login_view = "login"
admin = Admin(app)


@login_manager.user_loader
def load_user(userid):
    return User.query.get(userid)


# Products (id, name, description, category, stock,
# created, modified, unit_price, visibility [true, false])

basdir = os.path.abspath(os.path.dirname(__file__))
Upload_dir = basdir + "/static/images/"
Allowed = ["JPG", "jpg", "PNG", "png"]


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    role = db.Column(db.String(100), default="user")
    product = db.relationship("Orders", backref="user", lazy=True)
    visibility = db.Column(db.String(255), default="True")


class Products(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    additional_description = db.Column(db.String(1000))
    category = db.Column(db.String(255), nullable=False)
    sub_category = db.Column(db.String(255))
    sub_cat_size = db.Column(db.String(255), default="")
    sub_cat_gender = db.Column(db.String(255), default="")
    flour = db.Column(db.String(255), default="")
    homo = db.Column(db.String(255), default="")
    hetero = db.Column(db.String(255), default="")
    stock = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Integer, nullable=False)
    visibility = db.Column(db.Boolean(), default=1)
    image = db.Column(db.String(255))
    image2= db.Column(db.String(255))
    image3 = db.Column(db.String(255))
    created = db.Column(db.TIMESTAMP(), server_default=func.now())
    modified = db.Column(
        db.TIMESTAMP(), server_default=func.now(), onupdate=func.current_timestamp()
    )
    owner_id = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    orderitems = db.relationship("OrderItems", backref="products", lazy=True)

    tags = db.Column(db.String(255))


# Orders table (id, user_id, created, total_price, address,
# payment_method, money_received)
class Orders(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    total_price = db.Column(db.Integer)
    address = db.Column(db.String(500))
    status = db.Column(db.String(255), default="Pending")
    receipt = db.Column(db.String(255))
    phone = db.Column(db.String(255), default="000 000 000")
    created = db.Column(db.DateTime, default=date.today())
    orderitems = db.relationship("OrderItems", backref="orders", lazy=True)



# OrderItems table (id, order_id, product_id, quantity, unit_price)


class OrderItems(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    order_id = db.Column(
        db.Integer, db.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    product_id = db.Column(
        db.Integer, db.ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    quantity = db.Column(db.Integer)
    unit_price = db.Column(db.Integer)






def MergeDict(dict1, dict2):
    if isinstance(dict1, list) and isinstance(dict2, list):
        return dict1 + dict2
    elif isinstance(dict1, dict) and isinstance(dict2, dict):
        return dict(list(dict1.items()) + list(dict2.items()))


@app.route("/")
def Home():
    try:
        cart_data = session["SHOP"]
    except:
        cart_data = {}

    row_per_page = 10
    page = request.args.get("page", 1, type=int)
    product = Products.query.paginate(page=page, per_page=row_per_page)
    return render_template(
        "index.html", product=product, cart_data=cart_data, category="home"
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()
        if user:
            if auth.verify(password, user.password):
                login_user(user)
                return redirect("/")
            else:
                flash("Incorrect Password!")
                return redirect("/login")
        else:
            flash("No User found with this Email")
            return redirect("/login")
    return render_template("login.html")


@app.route("/signup", methods=["POST", "GET"])
def singup():
    if request.method == "POST":
        user_name = request.form.get("user_name")
        email = request.form.get("email")
        password = request.form.get("password")
        r_password = request.form.get("r_password")

        user = User.query.filter_by(name="Admin", email="admin@gmail.com").first()

        if not user:
            hashed_password_admin = auth.hash("a@#$)($#$*admin@3435(*$%")
            admin = User(
                name="Admin",
                email="admin@gmail.com",
                password=hashed_password_admin,
                role="admin",
            )


            db.session.add(admin)
            db.session.commit()

        if not user_name:
            return {"name_err": "Name is required"}

        if not password:
            return {"password": "Password required"}
        if password != r_password:
            return {"password": "password not matched"}
        user = User.query.filter_by(name=user_name).first()

        if user:
            return {"user": "User Already Exists!"}
        email_checkup = User.query.filter_by(email=email).first()

        if email_checkup:
            return {"email": "Email Already Exists!"}

        print("done1")
        hashed_password = auth.hash(password)
        user_to_add = User(
            name=user_name,
            email=email,
            password=hashed_password,
        )
        db.session.add(user_to_add)
        db.session.commit()
        return {"msg": "created"}
    return render_template("signup.html")


@app.route("/admin_password_reset", methods = ['POST','GET'])
@login_required
def admin_password_reset():
    if current_user.name != "Admin" or current_user.email != "admin@gmail.com":
        flash("Please login as a admin to Access this page")
        return redirect("/login")
    if request.method == "POST":
        password = request.form.get('password')
        current_password = request.form.get('c_password')
        adm = User.query.filter_by(name="Admin", email="admin@gmail.com").first()
        if auth.verify(current_password, adm.password):
            adm.password = auth.hash(password)
            db.session.commit()
            flash("Admin password changed successfully")
            return redirect("/admin_dashboard")
        else:
            flash("Current password is incorrect")
            return redirect("/admin_password_reset")
    return render_template("dashboard/pages/password_reset.html")


@app.route("/admin_dashboard")
@login_required
def admin_dashboard():
    if current_user.name != "Admin" or current_user.email != "admin@gmail.com":
        flash("Please login as a admin to Access this page")
        return redirect("/login")
    product = Products.query.all()
    cat = "dashboard"
    return render_template("dashboard/index.html", product=product, cat=cat)


@app.route("/add_post", methods=["GET", "POST"])
@login_required
def add_post():
    if current_user.name != "Admin" and current_user.email != "admin@gmail.com":
        flash("Please login as a admin to Access this page")
        return redirect("/login")
    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        additional_description = request.form.get("additional_description")
        category = request.form.get("category")
        sub_category = request.form.get("sub-category")
        stock = request.form.get("stock")
        unit_price = request.form.get("unit_price")
        visibility = request.form.get("visibility")
        tag = request.form.get("tags")
        file = request.files["image"]
        file2 = request.files['image2']
        file3 = request.files['image3']

        filename = secure_filename(file.filename)
        filename2 = secure_filename(file2.filename)
        filename3 = secure_filename(file3.filename)

        if category == "Axolotls":
            size = request.form.get("size")
            gender = request.form.get("gender")

            # to add new option for select, add same line as below, request.form.get('name comming from html file')
            rfp= request.form.get('rfp')
            gdp = request.form.get('gdp')
            empty = request.form.get('none')
            flour = ""
            if empty:
                rfp = None
                gdp = None
            else:
                if rfp:
                    flour += rfp + ","

                if gdp:
                    flour += gdp + ","
            #homozygous
            leucistic = request.form.get('leucistic')
            melanoid = request.form.get('melanoid')
            hypomelanistic = request.form.get('hypomelanistic')
            albino = request.form.get('albino')
            copper = request.form.get('copper')
            axanthic = request.form.get('axanthic')

            homo = ""
            if leucistic:
                homo +=  leucistic + ","

            if melanoid:
                homo +=  melanoid + ","

            if hypomelanistic:
                homo +=  hypomelanistic + ","

            if albino:
                homo +=  albino + ","

            if copper:
                homo +=  copper + ","

            if axanthic:
                homo +=  axanthic + ","

            #heterozygous
            h_leucistic = request.form.get('h_leucistic')
            h_melanoid = request.form.get('h_melanoid')
            h_hypomelanistic = request.form.get('h_hypomelanistic')
            h_albino = request.form.get('h_albino')
            h_copper = request.form.get('h_copper')
            h_axanthic = request.form.get('h_axanthic')

            hetro = ""
            if h_leucistic:
                hetro +=  h_leucistic + ","

            if h_melanoid:
                hetro +=  h_melanoid + ","

            if h_hypomelanistic:
                hetro +=  h_hypomelanistic + ","

            if h_albino:
                hetro +=  h_albino + ","

            if h_copper:
                hetro +=  h_copper + ","

            if h_axanthic:
                hetro +=  h_axanthic + ","

            if visibility.lower() == "true":
                visibility = 1
            else:
                visibility = 0
            data = Products(
                name=name,
                description=description,
                additional_description=additional_description,
                category=category,
                sub_category=sub_category,
                sub_cat_size=size,
                sub_cat_gender=gender,
                flour = flour,
                homo = homo,
                hetero = hetro,
                stock=stock,
                unit_price=unit_price,
                visibility=visibility,
                image=filename,
                image2 = filename2,
                image3 = filename3,
                owner_id=current_user.id,
                tags=tag,
            )

            print(filename.split(".")[1])

            try:
                if str(filename.split(".")[1]) not in Allowed or str(filename2.split(".")[1]) not in Allowed or str(filename3.split(".")[1]) not in Allowed :

                    flash(
                        "Our website does not support that type of extension, Please update your Product Image"
                    )
            except:
                pass

            file.save(os.path.join(Upload_dir, filename))

            if file2:
                file2.save(os.path.join(Upload_dir, filename2))
            if file3:
                file3.save(os.path.join(Upload_dir, filename3))
            db.session.add(data)
            db.session.commit()
            return redirect("/add_post")

        else:

            if visibility.lower() == "true":
                visibility = 1
            else:
                visibility = 0
            data = Products(
                name=name,
                description=description,
                additional_description=additional_description,
                category=category,
                sub_category=sub_category,
                stock=stock,
                unit_price=unit_price,
                visibility=visibility,
                image=filename,
                owner_id=current_user.id,
                tags=tag,
            )

            print(filename.split(".")[1])
            if str(filename.split(".")[1]) not in Allowed:
                flash(
                    "Our website does not support that type of extension, Please update your Product Image"
                )
            file.save(os.path.join(Upload_dir, filename))
            print(file)
            db.session.add(data)
            db.session.commit()
            return redirect("/add_post")
            # print(name,description, stock, unit_price, visibility)
    return render_template("dashboard/pages/tables.html", cat="add_post")


@app.route("/delete/<id>")
@login_required
def delete_item(id):
    product = Products.query.filter_by(id=id).first()
    db.session.delete(product)
    db.session.commit()
    return redirect("/admin_dashboard")


@app.route("/shop")
def shop():
    try:
        cart_data = session["SHOP"]
    except:
        cart_data = {}
    row_per_page = 10
    page = request.args.get("page", 1, type=int)
    product = Products.query.paginate(page=page, per_page=row_per_page)

    plushies = Products.query.filter_by(category="Plushies").all()
    Handmade = Products.query.filter_by(category="Handmade").all()
    Swag = Products.query.filter_by(category="Swag").all()
    Axolotls = Products.query.filter_by(category = "Axolotls").all()
    return render_template(
        "shop.html",
        product=product,
        cart_data=cart_data,
        plushies=plushies,
        handmade=Handmade,
        swag=Swag,
        axolotls = Axolotls,
        category="shop",
    )

@app.route("/filter", methods =["POST"])
def filter():
    size = request.form.get('size')
    gender = request.form.get('gender')
    homo = request.form.get('homo')
    flour = request.form.get('flour')
    heter = request.form.get('heter')

    all_id = []
    # flour
    # homo  hetero
    # Melanoid
    # Leucistic

    query_data = Products.query.all()

    flr = []
    for data in query_data:
        try:
            if heter in data.hetero.split(","):
                all_id.append(data.id)
        except:
            pass

        try:
            if homo in data.homo.split(","):
                if heter != "Melanoid" and heter != "Leucistic":
                    if homo == "Melanoid":
                        if "Leucistic" in data.homo.split(","):
                            all_id.append(data.id)
                    if homo == "Leucistic":
                        if "Melanoid" in data.homo.split(","):
                            all_id.append(data.id)
                all_id.append(data.id)
        except:
            pass

        try:
            if flour in data.flour.split(","):
                flr.append(data.id)
        except:
            pass




    all_id = list(dict.fromkeys(all_id))
    flr = list(dict.fromkeys(flr))
    row_per_page = 10
    page = request.args.get("page", 1, type=int)
    product = Products.query.filter(Products.id.in_(all_id)).filter(Products.id.in_(flr)).filter_by(sub_cat_size=size,sub_cat_gender=gender).paginate(
        page=page, per_page=row_per_page)

    # query = ""
    # if albino == "" and melanoid == "" and leucistic == "":
    #     print('wild is running')
    #     print(wild)
    #     product = Products.query.filter_by(sub_cat_size=size,sub_cat_gender=gender,sub_cat_homo=homo,sub_cat_wild=wild).paginate(
    #     page=page, per_page=row_per_page)
    #     print(query)
    #     for data in query:
    #         print(data)
    # if melanoid == "" and leucistic == "" and wild == "":
    #     print("albino is running")
    #     print(albino)
    #     product = Products.query.filter_by(sub_cat_size=size,sub_cat_gender=gender,sub_cat_homo=homo,sub_cat_albino = albino).paginate(
    #     page=page, per_page=row_per_page)
    #
    # if albino == "" and leucistic == "" and wild == "":
    #     print("melanoid is running")
    #     print(melanoid)
    #     product = Products.query.filter_by(sub_cat_size=size,sub_cat_gender=gender,sub_cat_homo=homo,sub_cat_melanoid = melanoid).paginate(
    #     page=page, per_page=row_per_page)
    #
    # if melanoid == "" and albino == "" and wild == "":
    #     print("leucistic is running")
    #     print(leucistic)
    #     product = Products.query.filter_by(sub_cat_size=size,sub_cat_gender=gender,sub_cat_homo=homo,sub_cat_leucistic = leucistic).paginate(
    #     page=page, per_page=row_per_page)
    #
    #
    #
    # print("size =",size,",","gender=",gender,",","homo=",homo,",","albino=",albino,",","melanoid=",melanoid,",","leucistic=",leucistic,",","wild=",wild,",","heter=",heter,",")
    try:
        cart_data = session["SHOP"]
    except:
        cart_data = {}


    plushies = Products.query.filter_by(category="Plushies").all()
    Handmade = Products.query.filter_by(category="Handmade").all()
    Swag = Products.query.filter_by(category="Swag").all()
    Axolotls = Products.query.filter_by(category = "Axolotls").all()
    return render_template(
        "shop.html",
        product=product,
        cart_data=cart_data,
        plushies=plushies,
        handmade=Handmade,
        swag=Swag,
        axolotls = Axolotls,
        cat='Axolotls',
    )

@app.route("/pro_cat/<cat>")
def pro_cat(cat):
    try:
        cart_data = session["SHOP"]
    except:
        cart_data = {}
    row_per_page = 10
    page = request.args.get("page", 1, type=int)
    product = Products.query.filter_by(category=cat).paginate(
        page=page, per_page=row_per_page
    )
    plushies = Products.query.filter_by(category="Plushies").all()
    Handmade = Products.query.filter_by(category="Handmade").all()
    Swag = Products.query.filter_by(category="Swag").all()
    Axolotls = Products.query.filter_by(category = "Axolotls").all()
    return render_template(
        "shop.html",
        product=product,
        cart_data=cart_data,
        plushies=plushies,
        handmade=Handmade,
        swag=Swag,
        axolotls = Axolotls,
        cat=cat,
    )


@app.route("/sub_cat/<cat>/<sub_cat>")
def sub_cat(cat, sub_cat):
    try:
        cart_data = session["SHOP"]
    except:
        cart_data = {}
    row_per_page = 10
    page = request.args.get("page", 1, type=int)
    product = Products.query.filter_by(category=cat, sub_category=sub_cat).paginate(
        page=page, per_page=row_per_page
    )
    plushies = Products.query.filter_by(category="Plushies").all()
    Handmade = Products.query.filter_by(category="Handmade").all()
    Swag = Products.query.filter_by(category="Swag").all()
    Axolotls = Products.query.filter_by(category = "Axolotls").all()

    return render_template(
        "shop.html",
        product=product,
        cart_data=cart_data,
        plushies=plushies,
        handmade=Handmade,
        swag=Swag,
        axolotls = Axolotls,
        cat=cat,
        sub_cat=sub_cat,
    )


@app.route("/details/<id>")
def product_details(id):
    # row_per_page = 10
    # page = request.args.get('page', 1, type=int)

    product = Products.query.filter_by(id=id).first()
    # user = User.query.all()
    return render_template("shop-details.html", product=product)


@app.route("/show_cart")
def show_cart():
    try:
        cart_data = session["SHOP"]
    except:
        cart_data = {}

    total_price = 0
    for key in cart_data:
        total_price += cart_data[key]["t_price"]

    print(cart_data)
    return render_template(
        "shopping-cart.html", cart_data=cart_data, total_price=total_price
    )


@app.route("/cart", methods=["GET", "POST"])
def add_to_cart():
    if request.method == "POST":
        product_id = request.form.get("product_id")
        product = Products.query.filter_by(id=product_id).first()

        DictItems = {
            product_id: {
                "name": product.name,
                "price": product.unit_price,
                "t_price": product.unit_price,
                "description": product.description,
                "image": product.image,
                "quantity": 1,
            }
        }
        if "SHOP" in session:
            if product_id in session["SHOP"]:
                print("item id alreadys exists")
            else:
                session["SHOP"] = MergeDict(session["SHOP"], DictItems)
        else:
            session["SHOP"] = DictItems

        if "SHOP" in session:
            print(session["SHOP"])

        data = session["SHOP"]

        datas = len(data)
        return {"value": datas}


@app.route("/cart+", methods=["POST", "GET"])
def cart():
    if request.method == "POST":
        car_val = int(request.form.get("item_value"))
        price = float(request.form.get("price"))
        id = request.form.get("product_id")
        prod_price = float(request.form.get("prod_price"))


        product = Products.query.filter_by(id=id).first()
        if car_val >= product.stock:
            if "SHOP" in session:
                session["SHOP"][id]["quantity"] = car_val
                # session['SHOP'][id]['price'] = prod_price
                session["SHOP"][id]["t_price"] = prod_price
                session.modified = True

            cart_data = session['SHOP']
            total_grand_price = 0
            for key in cart_data:
                total_grand_price += cart_data[key]["t_price"]

            return {
                "val": car_val,
                "total_price": total_grand_price,
                "prod_p": prod_price,
                "grand_total": price,
            }

        car_val += 1
        price += product.unit_price
        print("___________________________________________")
        print(price)
        prod_price += product.unit_price
        if "SHOP" in session:
            session["SHOP"][id]["quantity"] = car_val
            # session['SHOP'][id]['price'] = prod_price
            session["SHOP"][id]["t_price"] = prod_price
            price = session["SHOP"][id]["t_price"]
            session.modified = True


        cart_data = session['SHOP']
        total_grand_price = 0
        for key in cart_data:
            total_grand_price += cart_data[key]["t_price"]



        return {
            "val": car_val,
            "total_price": total_grand_price,
            "prod_p": prod_price,
            "grand_total": price + 5,
        }


@app.route("/cart-", methods=["GET", "POST"])
def car_minus():
    if request.method == "POST":
        car_val = int(request.form.get("item_value"))
        price = float(request.form.get("price"))
        id = request.form.get("product_id")
        prod_price = float(request.form.get("prod_price"))

        product = Products.query.filter_by(id=id).first()
        car_val -= 1
        if car_val == 0:
            if "SHOP" in session:
                session["SHOP"][id]["quantity"] = 1
                session["SHOP"][id]["price"] = prod_price
                session.modified = True

            cart_data = session['SHOP']
            total_grand_price = 0
            for key in cart_data:
                total_grand_price += cart_data[key]["t_price"]
            return {
                "val": 1,
                "total_price": total_grand_price,
                "prod_p": prod_price,
                "grand_total": price,
            }
        price -= product.unit_price
        prod_price -= product.unit_price
        if "SHOP" in session:
            session["SHOP"][id]["quantity"] = car_val
            session["SHOP"][id]["t_price"] = prod_price
            price = session["SHOP"][id]["t_price"]
            session.modified = True

        cart_data = session['SHOP']
        total_grand_price = 0
        for key in cart_data:
            total_grand_price += cart_data[key]["t_price"]

        return {
            "val": car_val,
            "total_price": total_grand_price,
            "prod_p": prod_price,
            "grand_total": price,
        }


@app.route("/cart_item_delete/<key>")
def delete_session_item(key):
    if "SHOP" in session:
        session["SHOP"].pop(key)
        session.modified = True
    return redirect("/show_cart")


@app.route("/checkout", methods=["GET"])
@login_required
def checkout():
    try:
        product = session["SHOP"]
    except:
        product = {}

    total_price = 0.0
    for key in product:
        total_price += product[key]["t_price"]

    print(product)
    return render_template("checkout.html", product=product, total_price=total_price, app = app)

@app.route("/order_profile")
def order_profile():
    orders = db.session.query(Orders, OrderItems, Products).join(OrderItems, Orders.id == OrderItems.order_id).join(
        Products, OrderItems.product_id == Products.id).filter(Orders.user_id == current_user.id).all()

    print(orders)

    total_amount = 0
    amount = Orders.query.filter_by(user_id = current_user.id).all()
    for data in amount:
        total_amount += data.total_price


    return render_template("profile.html" , order = orders, total_amount = total_amount, app = app)


@app.route("/confirmation/<id>")
@login_required
def confirmation(id):
    try:
        print(session["SHOP"])
    except Exception as e:
        print(e)

    order = (
        db.session.query(OrderItems, Products)
        .join(Products, OrderItems.product_id == Products.id, isouter=True)
        .filter(OrderItems.order_id == id)
        .all()
    )

    orders = db.session.query(Orders, OrderItems, Products).join(OrderItems, Orders.id == OrderItems.order_id).join(Products, OrderItems.product_id == Products.id ).filter(Orders.user_id == current_user.id).all()

    for value in orders:
        print(value)

    total_price = 0
    for r in order:
        print(r[1].name, r[0].quantity, r[0].unit_price, r[1].image)
        total_price += r[0].unit_price
    data = Orders.query.filter_by(id=id).first()
    # session.pop("SHOP", None)
    # session.modified = True
    return render_template(
        "order_confirmation.html", order=order, data=data, total_price=total_price
    )


@app.route("/about")
def about():
    return render_template("")


@app.route("/update/<id>", methods=["POST", "GET"])
@login_required
def update(id):
    if current_user.name != "Admin" or current_user.email != "admin@gmail.com":
        flash("Please login as a admin to Access this page")
        return redirect("/login")
    update = "yes"
    product = Products.query.filter_by(id=id).first()
    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        category = request.form.get("category")
        sub_category = request.form.get("sub-category")
        stock = request.form.get("stock")
        unit_price = request.form.get("unit_price")
        visibility = request.form.get("visibility")
        tag = request.form.get("tags")
        additional_desc = request.form.get("additional_description")
        file = request.files["image"]
        print(file.filename)
        if file.filename == "":
            filename = product.image
        else:
            filename = secure_filename(file.filename)
            print(filename.split(".")[1])
            if str(filename.split(".")[1]) not in Allowed:
                pass
                # flash("Our website does not support that type of extension, Please update your Product Image")
            file.save(os.path.join(Upload_dir, filename))

        if visibility.lower() == "true":
            visibility = 1
        else:
            visibility = 0
        product.name = name
        product.description = description
        product.category = category
        product.stock = stock
        product.unit_price = unit_price
        product.visibility = visibility
        product.tags = tag
        product.additional_description = additional_desc
        product.image = filename
        db.session.commit()
        return redirect("/admin_dashboard")
    return render_template(
        "/dashboard/pages/tables.html", update=update, product=product, cat="Update"
    )


@app.route("/history")
@login_required
def history():
    if current_user.name != "Admin" or current_user.email != "admin@gmail.com":
        flash("Please login as a admin to Access this page")
        return redirect("/login")
    row_per_page = 10
    page = request.args.get("page", 1, type=int)


    order = Orders.query.order_by(Orders.created.desc()).paginate(
        page=page, per_page=row_per_page
    )
    return render_template(
        "dashboard/pages/orders_history.html", order=order, cat="history"
    )


@app.route("/search", methods=["GET", "POST"])
def Search():
    row_per_page = 10
    page = request.args.get("page", 1, type=int)
    result = request.form["search"]
    print(result)
    product = Products.query.filter(
        or_(Products.tags.contains(result), Products.name.contains(result))
    ).paginate(page=page, per_page=row_per_page)
    plushies = Products.query.filter_by(category="Plushies").all()
    Handmade = Products.query.filter_by(category="Handmade").all()
    Swag = Products.query.filter_by(category="Swag").all()
    Axolotls = Products.query.filter_by(category="Axolotls").all()
    return render_template(
        "shop.html",
        product=product,
        result=result,
        plushies=plushies,
        handmade=Handmade,
        axolotls = Axolotls,
        swag=Swag,
    )


@app.route("/gallery")
def gallery():
    try:
        cart_data = session["SHOP"]
    except:
        cart_data = {}
    return render_template("gallery.html", category="gallery", cart_data= cart_data)


@app.route("/care_guide")
def Care_guide():
    try:
        cart_data = session["SHOP"]
    except:
        cart_data = {}
    return render_template("care_guide.html", category="guide", cart_data = cart_data)

@app.route("/glossary")
def Glossary():
    try:
        cart_data = session["SHOP"]
    except:
        cart_data = {}

    with open('json/glossary_items.json') as f:
        glossary_items = json.load(f)
        
    return render_template("glossary.html", cart_data= cart_data, glossary_items=glossary_items)

@app.route("/contact")
def contact():
    return render_template("contact.html", category="contact")


@app.route("/blog")
def blog():
    return render_template("blog.html")


@app.route("/blog_details")
def blog_details():
    return render_template("details.html")


@app.route("/logout")
@login_required
def user_logout():
    logout_user()
    return redirect("/")


@app.route("/check_out_complete")
def checkout_complete():
    return render_template('payment.html', app = app)


@app.route('/charge', methods=['POST'])
def charge():
    # Amount in cents
    amount = int(float(request.form['price']))
    print(amount)
    name = request.form['first_name']
    email = request.form['email']
    address = request.form['address']
    address2 = request.form['address2']
    Phone = request.form['state']
    complete_address = address + " " + address2
    order = Orders.query.filter_by(user_id = current_user.id, id=7).first()

    try:
        product = session['SHOP']

        try:
            customer = stripe.Customer.create(
                email=request.form['stripeEmail'],
                source=request.form['stripeToken'],
            )

            charge = stripe.Charge.create(
                customer=customer.id,
                amount=amount,
                currency='usd',
                description='Axolotl Payement'
            )
            url = charge.receipt_url
        except Exception as e:
            flash(f"An error occurred: {str(e)}", "error")
            return  redirect(url_for("checkout"))

        data = Orders(
            user_id = current_user.id,
            total_price = amount,
            address = complete_address,
            phone = Phone,
            receipt = url
        )
        db.session.add(data)
        db.session.commit()
        db.session.refresh(data)



        for value in product:
            Items = OrderItems(
                order_id = data.id,
                product_id = value,
                quantity = product[value]['quantity'],
                unit_price = product[value]['price']
            )
            db.session.add(Items)
            db.session.commit()

        for value in product:
            print()
            P_data = Products.query.filter_by(id = value).first()
            P_data = Products.query.filter_by(id = value).first()
            P_data.stock -= product[value]['quantity']
            db.session.commit()

        session.pop('SHOP', None)
        session.modified = True
        return render_template('charge.html', amount=amount, url = url)
    except Exception as e:
        flash(f" Transaction failed. Please try again.{e}")
        return redirect(url_for("checkout"))

@app.route("/testing")
def testing():
    data = Products.query.all()

    searable = []
    for data in data:
        if data.name == "abc":
            searable.append(data.id)



    print(searable)
    # session.query(Record).filter(Record.id.in_(seq)).all()
    data = Products.query.filter(Products.id.in_(searable)).filter_by(sub_cat_size="7+").paginate(page=1, per_page=2)
    print(data)
    for data in data:
        print(data)

    return "done"



# Press the green button in the gutter to run the script.
if __name__ == "__main__":
    app.run(debug=True)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
