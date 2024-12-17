from app import app, db
from models import User, Category, Product, Slide
from werkzeug.security import generate_password_hash

def init_db():
    with app.app_context():
        # Drop all tables
        db.drop_all()
        
        # Create all tables
        db.create_all()
        
        # Create admin user
        admin = User(
            username='admin',
            email='admin@example.com',
            is_admin=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        
        # Create default categories
        categories = [
            Category(name='أقسام رجال', description='تشكيلة واسعة من الملابس الرجالية العصرية'),
            Category(name='أقسام نساء', description='أحدث صيحات الموضة النسائية'),
            Category(name='أقسام أطفال', description='ملابس أطفال مريحة وعملية')
        ]
        db.session.add_all(categories)
        
        # Create sample products
        products = [
            Product(
                name='ثوب رجالي كلاسيك',
                description='ثوب رجالي كلاسيكي فاخر',
                purchase_price=200,
                selling_price=350,
                stock=10,
                sizes='52,54,56,58,60',
                colors='أبيض,أسود,بيج',
                category=categories[0]  # رجال
            ),
            Product(
                name='عباية نسائية',
                description='عباية نسائية عصرية وأنيقة',
                purchase_price=150,
                selling_price=300,
                stock=15,
                sizes='S,M,L,XL',
                colors='أسود',
                category=categories[1]  # نساء
            ),
            Product(
                name='طقم أطفال',
                description='طقم أطفال مريح للمناسبات',
                purchase_price=100,
                selling_price=180,
                stock=20,
                sizes='2-3,4-5,6-7,8-9',
                colors='أزرق,أحمر,أخضر',
                category=categories[2]  # أطفال
            )
        ]
        db.session.add_all(products)
        
        # Create default slides
        slides = [
            Slide(
                title='تشكيلة رجالية جديدة',
                description='اكتشف أحدث التشكيلات الرجالية العصرية',
                active=True,
                order=1
            ),
            Slide(
                title='أزياء نسائية',
                description='تشكيلة متنوعة من الأزياء النسائية',
                active=True,
                order=2
            ),
            Slide(
                title='ملابس أطفال',
                description='تشكيلة واسعة من ملابس الأطفال',
                active=True,
                order=3
            )
        ]
        db.session.add_all(slides)
        
        # Commit changes
        db.session.commit()

if __name__ == '__main__':
    init_db()
    print('Database initialized successfully!')
