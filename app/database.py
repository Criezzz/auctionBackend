from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings
import pymysql

# Database URL from environment variables
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Create database if it doesn't exist (MySQL only)
if SQLALCHEMY_DATABASE_URL.startswith("mysql"):
    # Extract database name from URL
    db_name = SQLALCHEMY_DATABASE_URL.split("/")[-1].split("?")[0]
    # Create connection URL without database
    base_url = SQLALCHEMY_DATABASE_URL.rsplit("/", 1)[0]
    
    try:
        # Parse connection details
        # Format: mysql+pymysql://user:password@host:port/database
        parts = base_url.replace("mysql+pymysql://", "").split("@")
        user_pass = parts[0].split(":")
        host_port = parts[1].split(":")
        
        user = user_pass[0]
        password = user_pass[1] if len(user_pass) > 1 else ""
        host = host_port[0]
        port = int(host_port[1]) if len(host_port) > 1 else 3306
        
        # Connect and create database
        connection = pymysql.connect(host=host, user=user, password=password, port=port)
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        connection.close()
        print(f"Database '{db_name}' ready")
    except Exception as e:
        print(f"Warning: Could not auto-create database: {e}")
        print("Please create the database manually or check your MySQL connection")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.DEBUG  # Show SQL queries only in debug mode
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
