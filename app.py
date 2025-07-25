from flask import Flask
from dotenv import load_dotenv
import os

from extensions import db, migrate, ma
from modules.product.routes import register_product_routes

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI_PG')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db.init_app(app)
migrate.init_app(app, db)
ma.init_app(app)

register_product_routes(app)

   
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)
