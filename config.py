import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'wms-secret-key-2024'
    
    # Database URL - supports PostgreSQL (Render) or SQLite (local)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///warehouse.db')
    
    # Fix for Render's postgres:// vs postgresql:// 
    if SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
