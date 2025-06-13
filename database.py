from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Create database instance
db = SQLAlchemy()
migrate = Migrate()