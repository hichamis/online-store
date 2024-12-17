from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    image_filename = db.Column(db.String(200))
    products = db.relationship('Product', backref='category', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    purchase_price = db.Column(db.Float, nullable=False)
    selling_price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    sizes = db.Column(db.String(200))  # Store as comma-separated values
    colors = db.Column(db.String(200))  # Store as comma-separated values
    is_featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    orders = db.relationship('Order', backref='product', lazy=True)
    reviews = db.relationship('Review', backref='product', lazy=True)
    images = db.relationship('ProductImage', backref='product', lazy=True,
                           cascade='all, delete-orphan',
                           order_by='ProductImage.order')

    @property
    def primary_image(self):
        primary = next((img for img in self.images if img.is_primary), None)
        return primary.filename if primary else None

    @property
    def all_images(self):
        return [img.filename for img in self.images]

    @property
    def average_rating(self):
        if not self.reviews:
            return 0
        return sum(review.rating for review in self.reviews) / len(self.reviews)

    @property
    def available_sizes(self):
        return [size.strip() for size in self.sizes.split(',')] if self.sizes else []

    @property
    def available_colors(self):
        return [color.strip() for color in self.colors.split(',')] if self.colors else []

class ProductImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ProductImage {self.filename}>'

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Coupon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    discount = db.Column(db.Float, nullable=False)
    valid_from = db.Column(db.DateTime, nullable=False)
    valid_until = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Coupon {self.code}>'

    def is_valid(self):
        now = datetime.now()
        return self.is_active and self.valid_from <= now <= self.valid_until

class Slide(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    image_filename = db.Column(db.String(255))
    link = db.Column(db.String(255))
    active = db.Column(db.Boolean, default=True)
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    customer_address = db.Column(db.Text, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    size = db.Column(db.String(10))
    color = db.Column(db.String(20))
    total_price = db.Column(db.Float, nullable=False)
    profit = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')
    payment_status = db.Column(db.String(20), default='pending')
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    delivery_date = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    shipping_cost = db.Column(db.Float, default=0.0)
    coupon_code = db.Column(db.String(20))
    discount = db.Column(db.Float, default=0.0)
    final_price = db.Column(db.Float)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    coupon_id = db.Column(db.Integer, db.ForeignKey('coupon.id'))
    is_new = db.Column(db.Boolean, default=True)
    user = db.relationship('User', backref='orders')
    coupon = db.relationship('Coupon', backref='orders')

    def calculate_total(self):
        """حساب السعر الإجمالي والربح للطلب"""
        if self.product:
            self.total_price = self.product.selling_price * self.quantity
            self.profit = (self.product.selling_price - self.product.purchase_price) * self.quantity
            self.final_price = self.total_price

    def calculate_final_price(self):
        """حساب السعر النهائي بعد تطبيق الخصم"""
        if self.coupon and self.coupon.is_valid():
            discount = self.total_price * (self.coupon.discount / 100)
            self.final_price = self.total_price - discount
        else:
            self.final_price = self.total_price
        return self.final_price

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    store_name = db.Column(db.String(100), default='متجر الملابس العربية')
    store_phone = db.Column(db.String(20), default='+213 123 456 789')
    store_email = db.Column(db.String(100), default='info@arabicstore.com')
    store_address = db.Column(db.String(200), default='الجزائر العاصمة، الجزائر')
    currency = db.Column(db.String(10), default='دج')
    primary_color = db.Column(db.String(7), default='#0d6efd')  # لون القوائم والأزرار
    secondary_color = db.Column(db.String(7), default='#6c757d')  # لون الخلفية الثانوية
    accent_color = db.Column(db.String(7), default='#198754')  # لون التأكيد والنجاح
    text_color = db.Column(db.String(7), default='#212529')  # لون النصوص

    @staticmethod
    def get_settings():
        """Get the store settings, create default if not exists"""
        settings = Settings.query.first()
        if not settings:
            settings = Settings()
            db.session.add(settings)
            db.session.commit()
        return settings
