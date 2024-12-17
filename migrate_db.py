import os
import sqlite3
from app import app, db
from models import Order, Coupon, Product, Review, User

def migrate_database():
    with app.app_context():
        # Backup existing data
        conn = sqlite3.connect('store.db')
        cursor = conn.cursor()
        
        # Get existing data
        try:
            cursor.execute('SELECT * FROM product')
            products = cursor.fetchall()
            
            cursor.execute('SELECT * FROM user')
            users = cursor.fetchall()
            
            cursor.execute('SELECT id, customer_name, customer_phone, customer_address, product_id, quantity, size, color, total_price, profit, status, payment_status, order_date, delivery_date, notes FROM "order"')
            orders = cursor.fetchall()
            
            cursor.execute('SELECT * FROM review')
            reviews = cursor.fetchall()
        except sqlite3.OperationalError:
            products = []
            users = []
            orders = []
            reviews = []
        
        conn.close()
        
        # Delete existing database
        if os.path.exists('store.db'):
            os.remove('store.db')
        
        # Create new database with updated schema
        db.create_all()
        
        # Restore data
        try:
            # Restore products
            for product in products:
                p = Product(
                    id=product[0],
                    name=product[1],
                    description=product[2],
                    purchase_price=product[3],
                    selling_price=product[4],
                    stock=product[5],
                    image_filename=product[7] if len(product) > 7 else None,
                    created_at=product[8] if len(product) > 8 else None
                )
                db.session.add(p)
            
            # Restore users
            for user in users:
                u = User(
                    id=user[0],
                    username=user[1],
                    password_hash=user[2],
                    is_admin=user[3]
                )
                db.session.add(u)
            
            # Restore orders
            for order in orders:
                o = Order(
                    id=order[0],
                    customer_name=order[1],
                    customer_phone=order[2],
                    customer_address=order[3],
                    product_id=order[4],
                    quantity=order[5],
                    size=order[6],
                    color=order[7],
                    total_price=order[8],
                    profit=order[9],
                    status=order[10],
                    payment_status=order[11],
                    order_date=order[12],
                    delivery_date=order[13],
                    notes=order[14]
                )
                o.calculate_final_price()
                db.session.add(o)
            
            # Restore reviews
            for review in reviews:
                r = Review(
                    id=review[0],
                    product_id=review[1],
                    rating=review[2],
                    comment=review[3],
                    created_at=review[4]
                )
                db.session.add(r)
            
            db.session.commit()
            print("Database migration completed successfully!")
            
        except Exception as e:
            print(f"Error during migration: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    migrate_database()
