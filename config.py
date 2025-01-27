# config.py
import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your_secret_key')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///kindergarten.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False


# class Config:
#     SECRET_KEY = "your_secret_key"
#     SQLALCHEMY_DATABASE_URI = "sqlite:///payment_system.db"
#     SQLALCHEMY_TRACK_MODIFICATIONS = False