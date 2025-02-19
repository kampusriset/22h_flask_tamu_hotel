import os

class Config:
    SECRET_KEY = 'kuncirahasiasaya'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///hotel.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False 