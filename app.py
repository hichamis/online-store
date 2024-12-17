from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, session, make_response, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from urllib.parse import urlparse
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from sqlalchemy import func, text
from sqlalchemy import inspect
from models import db, User, Product, Order, Review, Coupon, Category, Slide, Settings, ProductImage
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, IntegerField, FileField, SubmitField, SelectField, BooleanField, MultipleFileField, PasswordField
from wtforms.validators import DataRequired
from flask_wtf.file import FileAllowed, FileRequired
from flask_wtf.csrf import CSRFProtect
import csv
from io import StringIO
import traceback
import codecs

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///store.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# تكوين حماية CSRF
csrf = CSRFProtect(app)

# تهيئة قاعدة البيانات
db.init_app(app)

# تهيئة مدير تسجيل الدخول
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'الرجاء تسجيل الدخول للوصول إلى هذه الصفحة'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# تكوين الصور والمجلدات
STATIC_FOLDER = os.path.join(app.root_path, 'static')
UPLOADS_FOLDER = os.path.join(STATIC_FOLDER, 'uploads')
IMAGES_FOLDER = os.path.join(STATIC_FOLDER, 'images')

app.config['UPLOAD_FOLDER'] = UPLOADS_FOLDER
app.config['DEFAULT_PRODUCT_IMAGE'] = 'images/default-product.jpg'
app.config['DEFAULT_SLIDE_IMAGE'] = 'images/default-slide.jpg'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

# إنشاء المجلدات إذا لم تكن موجودة
for folder in [STATIC_FOLDER, UPLOADS_FOLDER, IMAGES_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"تم إنشاء المجلد: {folder}")

# إنشاء الصور الافتراضية إذا لم تكن موجودة
def create_default_image(filename, width=800, height=600, color='gray', text="No Image Available"):
    """إنشاء صورة افتراضية بالأبعاد والنص المحددين"""
    filepath = os.path.join(IMAGES_FOLDER, filename)
    if not os.path.exists(filepath) or os.path.getsize(filepath) < 100:  # إعادة إنشاء الصورة إذا كان حجمها أقل من 100 بايت
        try:
            from PIL import Image, ImageDraw, ImageFont
            img = Image.new('RGB', (width, height), color)
            draw = ImageDraw.Draw(img)
            
            # حساب حجم النص
            font_size = min(width, height) // 20
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            # وضع النص في وسط الصورة
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            x = (width - text_width) / 2
            y = (height - text_height) / 2
            
            # رسم النص
            draw.text((x, y), text, fill="white", font=font)
            
            # حفظ الصورة
            img.save(filepath, quality=95)
            app.logger.info(f"تم إنشاء الصورة الافتراضية: {filepath}")
        except Exception as e:
            app.logger.error(f"خطأ في إنشاء الصورة الافتراضية {filename}: {str(e)}")

# إنشاء الصور الافتراضية
create_default_image('default-product.jpg', text="No Product Image")
create_default_image('default-slide.jpg', width=1200, height=400, text="No Slide Image")

def get_product_image(product):
    """الحصول على مسار صورة المنتج"""
    if product:
        primary_image = next((img for img in product.images if img.is_primary), None)
        if primary_image:
            return url_for('static', filename=f'uploads/{primary_image.filename}')
        elif product.images:
            # إذا لم تكن هناك صورة رئيسية، استخدم أول صورة
            return url_for('static', filename=f'uploads/{product.images[0].filename}')
    return url_for('static', filename=app.config['DEFAULT_PRODUCT_IMAGE'])

def get_slide_image(slide):
    """الحصول على مسار صورة الشريحة"""
    if slide and slide.image_filename:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], slide.image_filename)
        if os.path.exists(os.path.join(app.root_path, 'static', 'uploads', slide.image_filename)):
            return url_for('static', filename=f'uploads/{slide.image_filename}')
    app.logger.warning(f"Slide image not found, using default: {slide.image_filename if slide else 'No slide'}")
    return url_for('static', filename=app.config['DEFAULT_SLIDE_IMAGE'])

def handle_image_upload(image_file):
    if image_file and allowed_file(image_file.filename):
        try:
            # تأكد من وجود مجلد الرفع
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])

            # تنظيف اسم الملف
            filename = secure_filename(image_file.filename)
            name, ext = os.path.splitext(filename)
            counter = 1
            
            # تجنب تكرار أسماء الملفات
            while os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
                filename = f"{name}_{counter}{ext}"
                counter += 1
            
            # حفظ الصورة
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)
            
            app.logger.info(f"Successfully uploaded image: {filename}")
            return filename
            
        except Exception as e:
            app.logger.error(f"Error uploading image: {str(e)}")
            return None
            
    app.logger.warning(f"Invalid image file: {image_file.filename if image_file else 'No file'}")
    return None

@app.context_processor
def utility_processor():
    return dict(
        get_product_image=get_product_image,
        get_slide_image=get_slide_image
    )

@app.context_processor
def inject_settings():
    settings = Settings.get_settings()
    return dict(store_settings=settings)

@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

# إعداد التسجيل
import logging
import sys
import os
import codecs
from logging.handlers import TimedRotatingFileHandler

# Force UTF-8 encoding for stdout
if sys.stdout.encoding != 'utf-8':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# إنشاء مجلد السجلات إذا لم يكن موجوداً
log_folder = os.path.join(app.root_path, 'logs')
if not os.path.exists(log_folder):
    os.makedirs(log_folder)

log_file = os.path.join(log_folder, 'store.log')

# تكوين السجل
formatter = logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
)

# Console handler with UTF-8 encoding
class UTF8StreamHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            stream.write(msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)

# Remove existing handlers
for handler in app.logger.handlers[:]:
    app.logger.removeHandler(handler)

# Add console handler
console_handler = UTF8StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.INFO)
app.logger.addHandler(console_handler)

# Add file handler
try:
    file_handler = TimedRotatingFileHandler(
        log_file,
        when='midnight',
        interval=1,
        backupCount=10,
        encoding='utf-8',
        delay=False
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
except Exception as e:
    print(f"Warning: Could not set up file logging: {str(e)}")

app.logger.setLevel(logging.INFO)
app.logger.info('تم بدء تشغيل المتجر')

# تأكد من وجود المجلدات
for folder in ['uploads', 'images']:
    folder_path = os.path.join(app.root_path, 'static', folder)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

# تكوين معالج الأخطاء
@app.errorhandler(Exception)
def handle_error(error):
    error_info = traceback.format_exc()
    app.logger.error(f'خطأ غير متوقع: {str(error)}\n{error_info}')
    return 'حدث خطأ في الخادم. تم تسجيل التفاصيل.', 500

# تأكد من وجود مجلد الرفع
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# إعداد قاعدة البيانات
with app.app_context():
    db.create_all()
    
    # إنشاء مستخدم مسؤول افتراضي إذا لم يكن موجوداً
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@example.com',
            is_admin=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        
    # إنشاء إعدادات افتراضية إذا لم تكن موجودة
    settings = Settings.query.first()
    if not settings:
        settings = Settings()
        db.session.add(settings)
        
    db.session.commit()

# Routes
@app.route('/')
def index():
    products = Product.query.filter_by(is_featured=True).all()
    slides = Slide.query.filter_by(active=True).order_by(Slide.order).all()
    settings = Settings.get_settings()
    return render_template('index.html', 
                         products=products, 
                         slides=slides, 
                         store_settings=settings)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', product=product)

@app.route('/product/<int:product_id>/review', methods=['POST'])
def add_review(product_id):
    product = Product.query.get_or_404(product_id)
    
    review = Review(
        product_id=product_id,
        name=request.form['name'],
        rating=int(request.form['rating']),
        comment=request.form['comment']
    )
    
    db.session.add(review)
    db.session.commit()
    
    flash('شكراً على تقييمك!', 'success')
    return redirect(url_for('product_detail', product_id=product_id))

@app.route('/cart/checkout', methods=['POST'])
def cart_checkout():
    if not session.get('cart'):
        flash('سلة التسوق فارغة', 'error')
        return redirect(url_for('index'))
    
    try:
        print("Starting checkout process...")
        # Get customer information
        customer_name = request.form['customer_name']
        customer_phone = request.form['customer_phone']
        customer_address = request.form['customer_address']
        coupon_code = request.form.get('applied_coupon')
        
        print(f"Customer info - Name: {customer_name}, Phone: {customer_phone}")
        print(f"Coupon code: {coupon_code}")
        
        # Process each item in the cart
        total_discount = 0
        coupon = None
        if coupon_code:
            coupon = Coupon.query.filter_by(code=coupon_code).first()
            if coupon and coupon.is_valid():
                total_discount = coupon.discount
                print(f"Valid coupon found. Discount: {total_discount}%")
            else:
                print("Coupon not found or invalid")
        
        print("Processing cart items...")
        for product_id, item in session['cart'].items():
            product = Product.query.get(int(product_id))
            if product:
                print(f"Processing product {product.id}: {product.name}")
                # Calculate price with discount
                original_price = product.selling_price * item['quantity']
                discount_amount = (original_price * total_discount) / 100
                final_price = original_price - discount_amount
                
                print(f"Price calculations - Original: {original_price}, Discount: {discount_amount}, Final: {final_price}")
                
                # Calculate profit
                cost_price = product.purchase_price * item['quantity']
                profit = final_price - cost_price
                
                print(f"Profit calculation - Cost: {cost_price}, Profit: {profit}")
                
                try:
                    # Create order for each product
                    order = Order(
                        customer_name=customer_name,
                        customer_phone=customer_phone,
                        customer_address=customer_address,
                        product_id=product.id,
                        quantity=item['quantity'],
                        size=item.get('size'),
                        color=item.get('color'),
                        total_price=original_price,  # Original price before discount
                        final_price=final_price,    # Price after discount
                        profit=profit,
                        status='pending',
                        payment_status='pending'
                    )
                    
                    print(f"Created order object: {order.__dict__}")
                    
                    # If coupon was applied, link it to the order
                    if coupon and total_discount > 0:
                        order.coupon_id = coupon.id
                        print(f"Applied coupon {coupon.id} to order")
                    
                    # Add to database
                    db.session.add(order)
                    print("Added order to session")
                    
                    # Update product stock
                    product.stock -= item['quantity']
                    print(f"Updated product stock. New stock: {product.stock}")
                    
                except Exception as order_error:
                    print(f"Error creating order: {str(order_error)}")
                    raise order_error
        
        print("Committing changes to database...")
        # Commit all changes
        db.session.commit()
        
        # Clear the cart
        session.pop('cart', None)
        print("Cart cleared")
        
        flash('تم تقديم طلبك بنجاح!', 'success')
        return redirect(url_for('index'))
        
    except Exception as e:
        db.session.rollback()
        print(f"ERROR in checkout: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        flash('حدث خطأ أثناء معالجة طلبك. الرجاء المحاولة مرة أخرى.', 'error')
        return redirect(url_for('view_cart'))

@app.route('/cart/apply-coupon', methods=['POST'])
def apply_coupon():
    data = request.get_json()
    coupon_code = data.get('coupon_code')
    
    print(f"Received coupon code: {coupon_code}")  # سجل للتصحيح
    
    if not coupon_code:
        return jsonify({'success': False, 'message': 'الرجاء إدخال كود الخصم'})
    
    # Get cart total
    cart = session.get('cart', {})
    total = 0
    for product_id, item in cart.items():
        product = Product.query.get(int(product_id))
        if product:
            total += product.selling_price * item['quantity']
    
    print(f"Cart total: {total}")  # سجل للتصحيح
    
    # Find and validate coupon
    coupon = Coupon.query.filter_by(code=coupon_code).first()
    
    print(f"Found coupon: {coupon}")  # سجل للتصحيح
    if coupon:
        print(f"Coupon valid from: {coupon.valid_from}")  # سجل للتصحيح
        print(f"Coupon valid until: {coupon.valid_until}")  # سجل للتصحيح
        print(f"Coupon is active: {coupon.is_active}")  # سجل للتصحيح
    
    if not coupon:
        return jsonify({'success': False, 'message': 'كود الخصم غير صالح'})
    
    if not coupon.is_valid():
        return jsonify({'success': False, 'message': 'كود الخصم منتهي الصلاحية'})
    
    # Calculate discount
    discount_amount = (total * coupon.discount) / 100
    final_total = total - discount_amount
    
    print(f"Discount amount: {discount_amount}")  # سجل للتصحيح
    print(f"Final total: {final_total}")  # سجل للتصحيح
    
    return jsonify({
        'success': True,
        'discount_amount': round(discount_amount, 2),
        'final_total': round(final_total, 2)
    })

@app.route('/product/<int:product_id>/order', methods=['GET', 'POST'])
def order_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        try:
            # جمع بيانات الطلب
            customer_name = request.form.get('customer_name', '').strip()
            customer_phone = request.form.get('customer_phone', '').strip()
            customer_address = request.form.get('customer_address', '').strip()
            quantity = int(request.form.get('quantity', 1))
            size = request.form.get('size', '').strip()
            color = request.form.get('color', '').strip()
            
            # التحقق من البيانات
            if not all([customer_name, customer_phone, customer_address]):
                flash('جميع الحقول مطلوبة', 'danger')
                return redirect(url_for('order_product', product_id=product_id))
            
            # التحقق من رقم الهاتف
            if not customer_phone.isdigit() or len(customer_phone) != 10:
                flash('رقم الهاتف غير صالح', 'danger')
                return redirect(url_for('order_product', product_id=product_id))
            
            # التحقق من توفر الكمية المطلوبة
            if quantity > product.stock:
                flash('عذراً، الكمية المطلوبة غير متوفرة في المخزون', 'danger')
                return redirect(url_for('order_product', product_id=product_id))
            
            # حساب السعر الإجمالي والربح
            total_price = product.selling_price * quantity
            profit = (product.selling_price - product.purchase_price) * quantity
            
            # إنشاء طلب جديد
            order = Order(
                customer_name=customer_name,
                customer_phone=customer_phone,
                customer_address=customer_address,
                product_id=product.id,
                quantity=quantity,
                size=size,
                color=color,
                total_price=total_price,
                profit=profit,
                status='pending',  # حالة الطلب الافتراضية
                payment_status='pending'  # حالة الدفع الافتراضية
            )
            
            # تحديث المخزون
            product.stock -= quantity
            
            db.session.add(order)
            db.session.commit()
            
            flash('تم إرسال طلبك بنجاح!', 'success')
            return redirect(url_for('index'))
            
        except ValueError as e:
            flash('خطأ في البيانات المدخلة', 'danger')
            return redirect(url_for('order_product', product_id=product_id))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error creating order: {str(e)}")
            flash('حدث خطأ أثناء إرسال الطلب. الرجاء المحاولة مرة أخرى.', 'danger')
            return redirect(url_for('order_product', product_id=product_id))
    
    return render_template('order.html', product=product)

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if current_user.is_authenticated:
            return redirect(url_for('index'))
            
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            app.logger.info(f'محاولة تسجيل دخول للمستخدم: {username}')
            
            if not username or not password:
                flash('يرجى إدخال اسم المستخدم وكلمة المرور', 'danger')
                return render_template('login.html')
            
            user = User.query.filter_by(username=username).first()
            app.logger.info(f'نتيجة البحث عن المستخدم: {user}')
            
            if user:
                if user.check_password(password):
                    login_user(user)
                    flash('تم تسجيل الدخول بنجاح!', 'success')
                    next_page = request.args.get('next')
                    if next_page and urlparse(next_page).netloc == '':
                        return redirect(next_page)
                    if user.is_admin:
                        return redirect(url_for('admin_dashboard'))
                    return redirect(url_for('index'))
                else:
                    app.logger.warning('كلمة المرور غير صحيحة')
                    flash('كلمة المرور غير صحيحة', 'danger')
            else:
                app.logger.warning('المستخدم غير موجود')
                flash('المستخدم غير موجود', 'danger')
        
        return render_template('login.html')
    except Exception as e:
        app.logger.error(f'خطأ في تسجيل الدخول: {str(e)}')
        app.logger.error(traceback.format_exc())
        flash('حدث خطأ أثناء تسجيل الدخول. الرجاء المحاولة مرة أخرى.', 'danger')
        return render_template('login.html')

@app.route('/admin/logout')
@login_required
def logout():
    logout_user()
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('login'))

@app.route('/admin')
@app.route('/admin/')
@login_required
def admin_index():
    if not current_user.is_admin:
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('index'))
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/dashboard')
@app.route('/admin/dashboard/')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('index'))
    
    try:
        # إحصائيات عامة
        total_sales = float(db.session.query(func.sum(Order.total_price)).scalar() or 0)
        total_orders = Order.query.count()
        total_products = Product.query.count()
        total_users = User.query.count()
        
        # الطلبات الجديدة
        new_orders = Order.query.filter_by(is_new=True).count()
        
        # إحصائيات المبيعات الشهرية
        current_year = datetime.utcnow().year
        monthly_sales = db.session.query(
            func.strftime('%m', Order.order_date).label('month'),
            func.sum(Order.total_price).label('sales')
        ).filter(
            func.strftime('%Y', Order.order_date) == str(current_year)
        ).group_by('month').all()
        
        months = [0.0] * 12
        for month, sales in monthly_sales:
            if month and sales:
                try:
                    month_index = int(month) - 1
                    months[month_index] = float(sales)
                except (ValueError, IndexError) as e:
                    app.logger.error(f"خطأ في معالجة بيانات المبيعات الشهرية: {str(e)}")
        
        # حالة الطلبات
        default_statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
        status_labels = ['قيد الانتظار', 'قيد المعالجة', 'تم الشحن', 'تم التسليم', 'ملغي']
        order_counts = {status: 0 for status in default_statuses}
        
        order_status_results = db.session.query(
            Order.status,
            func.count(Order.id).label('count')
        ).group_by(Order.status).all()
        
        status_data = []
        for status in default_statuses:
            count = 0
            for result_status, result_count in order_status_results:
                if result_status == status:
                    count = int(result_count)
                    break
            status_data.append(count)
        
        # آخر الطلبات
        recent_orders = Order.query.order_by(Order.order_date.desc()).limit(5).all()
        
        # تحديث حالة الطلبات الجديدة
        if new_orders > 0:
            Order.query.filter_by(is_new=True).update({Order.is_new: False})
            db.session.commit()
        
        # إعدادات المتجر
        settings = Settings.get_settings()
        
        return render_template('admin_dashboard_new.html',
            total_sales=total_sales,
            total_orders=total_orders,
            total_products=total_products,
            total_users=total_users,
            new_orders=new_orders,
            months=months,
            status_labels=status_labels,
            status_data=status_data,
            recent_orders=recent_orders,
            settings=settings
        )
    except Exception as e:
        app.logger.error(f"خطأ في لوحة التحكم: {str(e)}")
        flash('حدث خطأ في تحميل لوحة التحكم', 'danger')
        return redirect(url_for('index'))

@app.route('/admin/orders')
@login_required
def manage_orders():
    if not current_user.is_admin:
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('home'))
    
    # Get filter parameters
    status = request.args.get('status')
    payment_status = request.args.get('payment_status')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    # Base query
    query = Order.query
    
    # Apply filters
    if status:
        query = query.filter(Order.status == status)
    if payment_status:
        query = query.filter(Order.payment_status == payment_status)
    if date_from:
        date_from = datetime.strptime(date_from, '%Y-%m-%d')
        query = query.filter(Order.order_date >= date_from)
    if date_to:
        date_to = datetime.strptime(date_to, '%Y-%m-%d')
        query = query.filter(Order.order_date <= date_to)
    
    # Get orders sorted by date
    orders = query.order_by(Order.order_date.desc()).all()
    
    # Calculate totals
    total_orders = len(orders)
    total_revenue = sum(order.total_price for order in orders)
    total_profit = sum((order.total_price - (order.product.purchase_price * order.quantity)) for order in orders)
    
    # Get settings
    settings = Settings.query.first()
    
    return render_template('manage_orders.html', 
                         orders=orders,
                         total_orders=total_orders,
                         total_revenue=total_revenue,
                         total_profit=total_profit,
                         settings=settings)

class OrderUpdateForm(FlaskForm):
    status = SelectField('حالة الطلب', choices=[
        ('pending', 'قيد الانتظار'),
        ('processing', 'قيد المعالجة'),
        ('shipped', 'تم الشحن'),
        ('delivered', 'تم التسليم'),
        ('cancelled', 'ملغي')
    ])
    payment_status = SelectField('حالة الدفع', choices=[
        ('pending', 'قيد الانتظار'),
        ('paid', 'تم الدفع'),
        ('refunded', 'تم الإرجاع')
    ])
    submit = SubmitField('تحديث الطلب')

@app.route('/admin/order/<int:order_id>/update', methods=['GET', 'POST'])
@login_required
def admin_update_order(order_id):
    if not current_user.is_admin:
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('home'))
        
    order = Order.query.get_or_404(order_id)
    form = OrderUpdateForm(obj=order)
    
    if form.validate_on_submit():
        order.status = form.status.data
        order.payment_status = form.payment_status.data
        
        if order.status == 'delivered':
            order.delivery_date = datetime.utcnow()
            
        try:
            db.session.commit()
            flash('تم تحديث حالة الطلب بنجاح', 'success')
        except Exception as e:
            db.session.rollback()
            flash('حدث خطأ أثناء تحديث حالة الطلب', 'danger')
            app.logger.error(f"Error updating order status: {str(e)}")
        
        return redirect(url_for('manage_orders'))  # Changed from admin_orders to manage_orders
    
    return render_template('update_order.html', order=order, form=form)

@app.route('/admin/product/<int:product_id>/update-stock', methods=['POST'])
@login_required
def update_product_stock(product_id):
    try:
        data = request.get_json()
        new_stock = int(data.get('stock', 0))
        
        product = Product.query.get_or_404(product_id)
        product.stock = new_stock
        db.session.commit()
        
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/admin/manage-products')
@login_required
def manage_products():
    if not current_user.is_admin:
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('home'))
    
    # Get query parameters
    search = request.args.get('search', '')
    availability = request.args.get('availability', 'all')
    sort = request.args.get('sort', 'newest')
    
    # Start with base query
    query = Product.query
    
    # Apply search filter
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))
    
    # Apply availability filter
    if availability == 'in_stock':
        query = query.filter(Product.stock > 0)
    elif availability == 'out_of_stock':
        query = query.filter(Product.stock == 0)
    
    # Apply sorting
    if sort == 'newest':
        query = query.order_by(Product.id.desc())
    elif sort == 'price_high':
        query = query.order_by(Product.selling_price.desc())
    elif sort == 'price_low':
        query = query.order_by(Product.selling_price.asc())
    elif sort == 'stock_low':
        query = query.order_by(Product.stock.asc())
    
    # Get products and settings
    products = query.all()
    settings = Settings.query.first()
    
    return render_template('manage_products.html', 
                         products=products,
                         search=search,
                         availability=availability,
                         sort=sort,
                         settings=settings)

@app.route('/products')
def list_products():
    products = Product.query.all()
    categories = Category.query.all()
    return render_template('products.html', products=products, categories=categories)

@app.route('/products/category/<int:category_id>')
def list_products_by_category(category_id):
    category = Category.query.get_or_404(category_id)
    products = Product.query.filter_by(category_id=category_id).all()
    categories = Category.query.all()  # Add this to show category filter
    return render_template('products.html', products=products, categories=categories, category=category)

@app.route('/admin/product/delete/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    if not current_user.is_admin:
        return redirect(url_for('home'))
    
    product = Product.query.get_or_404(product_id)
    
    # التحقق من وجود طلبات مرتبطة
    related_orders = Order.query.filter_by(product_id=product_id).all()
    if related_orders:
        flash('لا يمكن حذف هذا المنتج لأنه مرتبط بطلبات موجودة', 'danger')
        return redirect(url_for('list_products'))
    
    # حذف صورة المنتج إذا كانت موجودة
    if product.image_filename:
        image_path = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], product.image_filename)
        if os.path.exists(image_path):
            os.remove(image_path)
    
    try:
        db.session.delete(product)
        db.session.commit()
        flash('تم حذف المنتج بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting product: {str(e)}")
        flash('حدث خطأ أثناء حذف المنتج', 'danger')
    
    return redirect(url_for('list_products'))

class ProductForm(FlaskForm):
    name = StringField('اسم المنتج', validators=[DataRequired()])
    category_id = SelectField('القسم', coerce=int, validators=[DataRequired()])
    description = TextAreaField('وصف المنتج')
    purchase_price = FloatField('سعر الشراء', validators=[DataRequired()])
    selling_price = FloatField('سعر البيع', validators=[DataRequired()])
    stock = IntegerField('الكمية المتوفرة', validators=[DataRequired()])
    sizes = StringField('المقاسات المتوفرة')
    colors = StringField('الألوان المتوفرة')
    primary_image = FileField('الصورة الرئيسية', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], 'الصور فقط!')
    ])
    additional_images = MultipleFileField('صور إضافية', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], 'الصور فقط!')
    ])
    submit = SubmitField('حفظ المنتج')

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        self.category_id.choices = [(c.id, c.name) for c in Category.query.all()]

@app.route('/admin/products/add', methods=['GET', 'POST'])
@login_required
def add_product():
    if not current_user.is_admin:
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('index'))

    form = ProductForm()
    if form.validate_on_submit():
        try:
            # جمع البيانات من النموذج
            product = Product(
                name=form.name.data,
                category_id=form.category_id.data,
                description=form.description.data,
                purchase_price=form.purchase_price.data,
                selling_price=form.selling_price.data,
                stock=form.stock.data,
                sizes=form.sizes.data,
                colors=form.colors.data
            )
            
            db.session.add(product)
            db.session.flush()  # للحصول على ID المنتج
            
            # معالجة الصورة الرئيسية
            if form.primary_image.data:
                filename = handle_image_upload(form.primary_image.data)
                if filename:
                    primary_image = ProductImage(
                        product_id=product.id,
                        filename=filename,
                        is_primary=True,
                        order=0
                    )
                    db.session.add(primary_image)
            
            # معالجة الصور الإضافية
            if form.additional_images.data:
                for i, image in enumerate(form.additional_images.data, 1):
                    if image:
                        filename = handle_image_upload(image)
                        if filename:
                            additional_image = ProductImage(
                                product_id=product.id,
                                filename=filename,
                                is_primary=False,
                                order=i
                            )
                            db.session.add(additional_image)
            
            db.session.commit()
            flash('تم إضافة المنتج بنجاح!', 'success')
            return redirect(url_for('manage_products'))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error adding product: {str(e)}")
            flash('حدث خطأ أثناء إضافة المنتج', 'danger')
    
    return render_template('add_product.html', form=form)

@app.route('/admin/product/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    if not current_user.is_admin:
        return redirect(url_for('home'))
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    if form.validate_on_submit():
        try:
            # تحديث بيانات المنتج
            product.name = form.name.data
            product.category_id = form.category_id.data
            product.description = form.description.data
            product.purchase_price = form.purchase_price.data
            product.selling_price = form.selling_price.data
            product.stock = form.stock.data
            product.sizes = form.sizes.data
            product.colors = form.colors.data
            
            # معالجة الصورة الرئيسية
            if form.primary_image.data:
                # حذف الصورة الرئيسية القديمة إذا وجدت
                old_primary = ProductImage.query.filter_by(product_id=product.id, is_primary=True).first()
                if old_primary:
                    old_image_path = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], old_primary.filename)
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
                    db.session.delete(old_primary)
                
                # إضافة الصورة الرئيسية الجديدة
                filename = handle_image_upload(form.primary_image.data)
                if filename:
                    primary_image = ProductImage(
                        product_id=product.id,
                        filename=filename,
                        is_primary=True,
                        order=0
                    )
                    db.session.add(primary_image)
            
            # معالجة الصور الإضافية
            if form.additional_images.data:
                # احصل على أعلى ترتيب حالي
                max_order = db.session.query(db.func.max(ProductImage.order))\
                    .filter_by(product_id=product.id).scalar() or 0
                
                for i, image in enumerate(form.additional_images.data, max_order + 1):
                    if image:
                        filename = handle_image_upload(image)
                        if filename:
                            additional_image = ProductImage(
                                product_id=product.id,
                                filename=filename,
                                is_primary=False,
                                order=i
                            )
                            db.session.add(additional_image)
            
            db.session.commit()
            flash('تم تحديث المنتج بنجاح!', 'success')
            return redirect(url_for('manage_products'))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error updating product: {str(e)}")
            flash('حدث خطأ أثناء تحديث المنتج', 'danger')
    
    return render_template('edit_product.html', form=form, product=product)

@app.route('/admin/users')
@login_required
def manage_users():
    if not current_user.is_admin:
        return redirect(url_for('home'))
    users = User.query.all()
    return render_template('manage_users.html', users=users)

@app.route('/admin/user/add', methods=['POST'])
@login_required
def add_user():
    if not current_user.is_admin:
        return redirect(url_for('home'))
    
    username = request.form.get('username')
    password = request.form.get('password')
    is_admin = request.form.get('is_admin') == 'on'
    
    if User.query.filter_by(username=username).first():
        flash('اسم المستخدم موجود بالفعل', 'error')
        return redirect(url_for('manage_users'))
    
    user = User(
        username=username,
        password_hash=generate_password_hash(password),
        is_admin=is_admin
    )
    db.session.add(user)
    db.session.commit()
    
    flash('تم إضافة المستخدم بنجاح', 'success')
    return redirect(url_for('manage_users'))

@app.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        return redirect(url_for('home'))
    
    if current_user.id == user_id:
        flash('لا يمكنك حذف حسابك الخاص', 'error')
        return redirect(url_for('manage_users'))
    
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    
    flash('تم حذف المستخدم بنجاح', 'success')
    return redirect(url_for('manage_users'))

@app.route('/admin/profile', methods=['GET', 'POST'])
@login_required
def admin_profile():
    if not current_user.is_admin:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # التحقق من كلمة المرور الحالية
        if not check_password_hash(current_user.password_hash, current_password):
            flash('كلمة المرور الحالية غير صحيحة', 'error')
            return redirect(url_for('admin_profile'))
        
        # التحقق من تطابق كلمة المرور الجديدة
        if new_password and new_password != confirm_password:
            flash('كلمة المرور الجديدة غير متطابقة', 'error')
            return redirect(url_for('admin_profile'))
        
        # تحديث اسم المستخدم إذا تم تغييره
        if username != current_user.username:
            if User.query.filter_by(username=username).first():
                flash('اسم المستخدم موجود بالفعل', 'error')
                return redirect(url_for('admin_profile'))
            current_user.username = username
        
        # تحديث كلمة المرور إذا تم تغييرها
        if new_password:
            current_user.password_hash = generate_password_hash(new_password)
        
        db.session.commit()
        flash('تم تحديث المعلومات بنجاح', 'success')
        return redirect(url_for('admin_profile'))
    
    return render_template('admin_profile.html')

@app.route('/admin/order/<int:order_id>/print')
@login_required
def print_order(order_id):
    if not current_user.is_admin:
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('home'))
        
    order = Order.query.get_or_404(order_id)
    return render_template('print_order.html', order=order)

@app.route('/admin/orders/export', methods=['GET'])
@login_required
def export_orders():
    if not current_user.is_admin:
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('index'))
    
    try:
        # إنشاء قائمة لتخزين البيانات
        data = []
        
        # إضافة رؤوس الأعمدة
        headers = [
            'رقم الطلب', 'تاريخ الطلب', 'اسم العميل', 'رقم الهاتف', 
            'العنوان', 'المنتج', 'الكمية', 'المقاس', 'اللون',
            'السعر الإجمالي', 'الربح', 'حالة الطلب', 'حالة الدفع', 
            'تاريخ التوصيل', 'ملاحظات', 'الكوبون المستخدم', 'السعر النهائي'
        ]
        data.append(headers)
        
        # جلب جميع الطلبات
        orders = Order.query.order_by(Order.order_date.desc()).all()
        
        # إضافة بيانات كل طلب
        for order in orders:
            product_name = order.product.name if order.product else 'غير متوفر'
            coupon_code = order.coupon.code if order.coupon else 'لا يوجد'
            delivery_date = order.delivery_date.strftime('%Y-%m-%d %H:%M:%S') if order.delivery_date else 'غير محدد'
            order_date = order.order_date.strftime('%Y-%m-%d %H:%M:%S') if order.order_date else 'غير محدد'
            
            row = [
                str(order.id),
                order_date,
                order.customer_name,
                order.customer_phone,
                order.customer_address,
                product_name,
                str(order.quantity),
                order.size or 'غير محدد',
                order.color or 'غير محدد',
                str(order.total_price),
                str(order.profit),
                order.status,
                order.payment_status,
                delivery_date,
                order.notes or '',
                coupon_code,
                str(order.final_price or order.total_price)
            ]
            data.append(row)
        
        # إنشاء الملف مع ترميز مناسب للعربية
        output = StringIO()
        output.write('\ufeff')  # BOM للدعم العربي
        writer = csv.writer(output, dialect='excel')
        writer.writerows(data)
        
        # إنشاء الاستجابة
        response = make_response(output.getvalue())
        filename = f"orders_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        response.headers["Content-type"] = "text/csv; charset=utf-8-sig"
        return response
        
    except Exception as e:
        app.logger.error(f"خطأ في تصدير الطلبات: {str(e)}")
        flash(f'حدث خطأ أثناء تصدير الطلبات: {str(e)}', 'danger')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/reports')
@login_required
def admin_reports():
    print(">>> بداية دالة التقارير")  # للتسجيل المباشر
    if not current_user.is_admin:
        print(">>> المستخدم ليس مسؤولاً")  # للتسجيل المباشر
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('index'))
    
    try:
        print(">>> جاري استخراج إحصائيات المبيعات")  # للتسجيل المباشر
        # إحصائيات المبيعات حسب الشهر
        monthly_sales = db.session.query(
            func.strftime('%Y-%m', Order.order_date).label('month'),
            func.sum(Order.total_price).label('total_sales'),
            func.sum(Order.profit).label('total_profit'),
            func.count(Order.id).label('order_count')
        ).filter(Order.order_date.isnot(None))\
         .group_by('month')\
         .order_by('month').all()
        print(f">>> تم استخراج {len(monthly_sales)} شهر من المبيعات")  # للتسجيل المباشر

        monthly_sales_data = []
        for sale in monthly_sales:
            try:
                monthly_sales_data.append({
                    'month': sale.month,
                    'total_sales': float(sale.total_sales if sale.total_sales is not None else 0),
                    'total_profit': float(sale.total_profit if sale.total_profit is not None else 0),
                    'order_count': int(sale.order_count if sale.order_count is not None else 0)
                })
            except (ValueError, TypeError) as e:
                print(f"خطأ في تحويل البيانات الشهرية: {str(e)}")
                continue

        print(">>> جاري استخراج إحصائيات المنتجات")  # للتسجيل المباشر
        # إحصائيات المنتجات الأكثر مبيعاً
        top_products = db.session.query(
            Product.name.label('name'),
            func.sum(Order.quantity).label('total_quantity'),
            func.sum(Order.total_price).label('total_sales')
        ).join(Order).group_by(Product.id, Product.name)\
         .order_by(func.sum(Order.quantity).desc())\
         .limit(10).all()
        print(f">>> تم استخراج {len(top_products)} منتج")  # للتسجيل المباشر

        top_products_data = []
        for product in top_products:
            try:
                top_products_data.append({
                    'name': product.name,
                    'total_quantity': int(product.total_quantity if product.total_quantity is not None else 0),
                    'total_sales': float(product.total_sales if product.total_sales is not None else 0)
                })
            except (ValueError, TypeError) as e:
                print(f"خطأ في تحويل بيانات المنتجات: {str(e)}")
                continue

        print(">>> جاري استخراج إحصائيات حالة الطلبات")  # للتسجيل المباشر
        # إحصائيات حالة الطلبات
        order_status = db.session.query(
            Order.status,
            func.count(Order.id)
        ).group_by(Order.status).all()
        print(f">>> تم استخراج {len(order_status)} حالة للطلبات")  # للتسجيل المباشر

        order_status_data = []
        for status in order_status:
            try:
                count_value = status[1] if isinstance(status, tuple) else status.count
                order_status_data.append({
                    'status': status[0] if isinstance(status, tuple) else status.status,
                    'count': int(count_value if count_value is not None else 0)
                })
            except (ValueError, TypeError) as e:
                print(f"خطأ في تحويل بيانات حالة الطلبات: {str(e)}")
                continue

        print(">>> جاري تحضير القالب")  # للتسجيل المباشر
        return render_template('admin_reports.html',
                             monthly_sales=monthly_sales_data,
                             top_products=top_products_data,
                             order_status=order_status_data)

    except Exception as e:
        print(f">>> خطأ: {str(e)}")  # للتسجيل المباشر
        print(f">>> التفاصيل: {traceback.format_exc()}")  # للتسجيل المباشر
        flash(f'حدث خطأ أثناء تحميل التقارير: {str(e)}', 'danger')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/coupons')
@login_required
def manage_coupons():
    if not current_user.is_admin:
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('index'))
    
    coupons = Coupon.query.order_by(Coupon.created_at.desc()).all()
    return render_template('manage_coupons.html', coupons=coupons)

@app.route('/add_coupon', methods=['GET', 'POST'])
@login_required
def add_coupon():
    if not current_user.is_admin:
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        code = request.form.get('code')
        discount = float(request.form.get('discount'))
        valid_from = datetime.strptime(request.form.get('valid_from'), '%Y-%m-%dT%H:%M')
        valid_until = datetime.strptime(request.form.get('valid_until'), '%Y-%m-%dT%H:%M')

        # التحقق من عدم وجود كوبون بنفس الكود
        existing_coupon = Coupon.query.filter_by(code=code).first()
        if existing_coupon:
            flash('هذا الكود مستخدم بالفعل', 'error')
            return redirect(url_for('manage_coupons'))

        coupon = Coupon(
            code=code,
            discount=discount,
            valid_from=valid_from,
            valid_until=valid_until,
            is_active=True
        )
        db.session.add(coupon)
        db.session.commit()
        flash('تم إضافة الكوبون بنجاح', 'success')
        return redirect(url_for('manage_coupons'))
    return redirect(url_for('manage_coupons'))

@app.route('/toggle_coupon/<int:coupon_id>', methods=['POST'])
@login_required
def toggle_coupon(coupon_id):
    if not current_user.is_admin:
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('index'))

    coupon = Coupon.query.get_or_404(coupon_id)
    coupon.is_active = not coupon.is_active
    db.session.commit()
    flash('تم تحديث حالة الكوبون بنجاح', 'success')
    return redirect(url_for('manage_coupons'))

@app.route('/delete_coupon/<int:coupon_id>', methods=['POST'])
@login_required
def delete_coupon(coupon_id):
    if not current_user.is_admin:
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('index'))

    coupon = Coupon.query.get_or_404(coupon_id)
    db.session.delete(coupon)
    db.session.commit()
    flash('تم حذف الكوبون بنجاح', 'success')
    return redirect(url_for('manage_coupons'))

class SlideForm(FlaskForm):
    title = StringField('العنوان', validators=[DataRequired()])
    description = TextAreaField('الوصف')
    link = StringField('الرابط')
    order = IntegerField('الترتيب', default=0)
    active = BooleanField('نشط', default=True)
    image = FileField('الصورة', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'الصور فقط!')])
    submit = SubmitField('حفظ')

@app.route('/admin/slides')
@login_required
def manage_slides():
    if not current_user.is_admin:
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('index'))
    slides = Slide.query.order_by(Slide.order).all()
    return render_template('admin_slides.html', slides=slides)

@app.route('/admin/slides/add', methods=['GET', 'POST'])
@login_required
def add_slide():
    if not current_user.is_admin:
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('index'))

    form = SlideForm()
    if form.validate_on_submit():
        try:
            filename = None
            if form.image.data:
                filename = handle_image_upload(form.image.data)
                if not filename:
                    flash('حدث خطأ أثناء رفع الصورة', 'danger')
                    return render_template('add_slide.html', form=form)
            
            slide = Slide(
                title=form.title.data,
                description=form.description.data,
                link=form.link.data,
                order=form.order.data,
                active=form.active.data,
                image_filename=filename
            )

            db.session.add(slide)
            db.session.commit()
            
            app.logger.info(f"Successfully added slide: {slide.title} with image: {filename}")
            flash('تم إضافة السلايد بنجاح!', 'success')
            return redirect(url_for('manage_slides'))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error adding slide: {str(e)}")
            flash('حدث خطأ أثناء إضافة السلايد', 'danger')

    return render_template('add_slide.html', form=form)

@app.route('/admin/slides/edit/<int:slide_id>', methods=['GET', 'POST'])
@login_required
def edit_slide(slide_id):
    if not current_user.is_admin:
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('index'))

    slide = Slide.query.get_or_404(slide_id)
    form = SlideForm(obj=slide)

    if form.validate_on_submit():
        slide.title = form.title.data
        slide.description = form.description.data
        slide.link = form.link.data
        slide.order = form.order.data
        slide.active = form.active.data

        if form.image.data:
            image = form.image.data
            filename = handle_image_upload(image)
            slide.image_filename = filename

        try:
            db.session.commit()
            flash('تم تحديث السلايد بنجاح!', 'success')
            return redirect(url_for('manage_slides'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"خطأ في تحديث السلايد: {str(e)}")
            flash('حدث خطأ أثناء تحديث السلايد', 'danger')

    return render_template('add_slide.html', form=form, slide=slide)

@app.route('/admin/slides/delete/<int:slide_id>', methods=['POST'])
@login_required
def delete_slide(slide_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'}), 403
    
    try:
        slide = Slide.query.get_or_404(slide_id)
        
        # حذف صورة السلايد إذا كانت موجودة
        if slide.image_filename:
            image_path = os.path.join(app.root_path, 'static/uploads', slide.image_filename)
            if os.path.exists(image_path):
                os.remove(image_path)
        
        db.session.delete(slide)
        db.session.commit()
        
        flash('تم حذف السلايد بنجاح', 'success')
        return jsonify({'success': True, 'message': 'تم حذف السلايد بنجاح'})
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting slide: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

class SettingsForm(FlaskForm):
    store_name = StringField('اسم المتجر', validators=[DataRequired()])
    store_phone = StringField('رقم الهاتف')
    store_email = StringField('البريد الإلكتروني')
    store_address = TextAreaField('العنوان')
    currency = StringField('العملة', validators=[DataRequired()])
    primary_color = StringField('اللون الرئيسي')
    secondary_color = StringField('اللون الثانوي')
    accent_color = StringField('لون التأكيد')
    text_color = StringField('لون النصوص')
    submit = SubmitField('حفظ الإعدادات')

@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def manage_settings():
    if not current_user.is_admin:
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('index'))
    
    settings = Settings.get_settings()
    form = SettingsForm(obj=settings)
    
    if form.validate_on_submit():
        try:
            form.populate_obj(settings)
            db.session.commit()
            flash('تم تحديث إعدادات المتجر بنجاح', 'success')
            return redirect(url_for('manage_settings'))
            
        except Exception as e:
            db.session.rollback()
            flash('حدث خطأ أثناء حفظ الإعدادات', 'danger')
            print(str(e))
    
    return render_template('manage_settings.html', settings=settings, form=form)

@app.route('/admin/categories')
@login_required
def manage_categories():
    if not current_user.is_admin:
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('index'))
    categories = Category.query.all()
    return render_template('manage_categories.html', categories=categories)

@app.route('/admin/categories/add', methods=['POST'])
@login_required
def add_category():
    if not current_user.is_admin:
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('index'))
    
    name = request.form.get('name')
    description = request.form.get('description')
    
    if not name:
        flash('اسم القسم مطلوب', 'danger')
        return redirect(url_for('manage_categories'))
    
    category = Category(name=name, description=description)
    db.session.add(category)
    
    try:
        db.session.commit()
        flash('تم إضافة القسم بنجاح', 'success')
    except:
        db.session.rollback()
        flash('حدث خطأ أثناء إضافة القسم', 'danger')
    
    return redirect(url_for('manage_categories'))

@app.route('/admin/categories/<int:category_id>/edit', methods=['POST'])
@login_required
def edit_category(category_id):
    if not current_user.is_admin:
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('index'))
    
    category = Category.query.get_or_404(category_id)
    name = request.form.get('name')
    description = request.form.get('description')
    
    if not name:
        flash('اسم القسم مطلوب', 'danger')
        return redirect(url_for('manage_categories'))
    
    category.name = name
    category.description = description
    
    try:
        db.session.commit()
        flash('تم تحديث القسم بنجاح', 'success')
    except:
        db.session.rollback()
        flash('حدث خطأ أثناء تحديث القسم', 'danger')
    
    return redirect(url_for('manage_categories'))

@app.route('/admin/categories/<int:category_id>/delete', methods=['POST'])
@login_required
def delete_category(category_id):
    if not current_user.is_admin:
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('index'))
    
    category = Category.query.get_or_404(category_id)
    
    try:
        db.session.delete(category)
        db.session.commit()
        flash('تم حذف القسم بنجاح', 'success')
    except:
        db.session.rollback()
        flash('حدث خطأ أثناء حذف القسم', 'danger')
    
    return redirect(url_for('manage_categories'))

@app.route('/view_cart')
def view_cart():
    cart = session.get('cart', {})
    cart_items = []
    total = 0
    
    for product_id, item in cart.items():
        product = Product.query.get(int(product_id))
        if product:
            subtotal = product.selling_price * item['quantity']
            cart_items.append({
                'product': product,
                'quantity': item['quantity'],
                'size': item.get('size'),
                'color': item.get('color'),
                'subtotal': subtotal
            })
            total += subtotal
    
    settings = Settings.get_settings()
    return render_template('cart.html', cart_items=cart_items, total=total, settings=settings)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    
    if not product:
        flash('المنتج غير موجود', 'error')
        return redirect(url_for('index'))
    
    quantity = int(request.form.get('quantity', 1))
    size = request.form.get('size')
    color = request.form.get('color')
    
    if quantity > product.stock:
        flash('الكمية المطلوبة غير متوفرة', 'error')
        return redirect(url_for('product_detail', product_id=product_id))
    
    cart = session.get('cart', {})
    
    cart[str(product_id)] = {
        'quantity': quantity,
        'size': size,
        'color': color
    }
    
    session['cart'] = cart
    flash('تمت إضافة المنتج إلى السلة', 'success')
    return redirect(url_for('view_cart'))

@app.route('/update_cart/<int:product_id>', methods=['POST'])
def update_cart(product_id):
    cart = session.get('cart', {})
    product_id_str = str(product_id)
    
    if product_id_str in cart:
        quantity = int(request.form.get('quantity', 1))
        product = Product.query.get(product_id)
        
        if quantity > product.stock:
            flash('الكمية المطلوبة غير متوفرة', 'error')
        else:
            cart[product_id_str]['quantity'] = quantity
            session['cart'] = cart
            flash('تم تحديث السلة', 'success')
    
    return redirect(url_for('view_cart'))

@app.route('/remove_from_cart/<int:product_id>')
def remove_from_cart(product_id):
    cart = session.get('cart', {})
    cart.pop(str(product_id), None)
    session['cart'] = cart
    flash('تم إزالة المنتج من السلة', 'success')
    return redirect(url_for('view_cart'))

@app.route('/clear_cart')
def clear_cart():
    session.pop('cart', None)
    flash('تم تفريغ السلة', 'success')
    return redirect(url_for('view_cart'))

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                             'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/admin/product/<int:product_id>/image/<int:image_id>/delete', methods=['POST'])
@login_required
def delete_product_image(product_id, image_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'}), 403
    
    try:
        image = ProductImage.query.get_or_404(image_id)
        if image.product_id != product_id:
            return jsonify({'success': False, 'message': 'صورة غير صالحة'}), 400
            
        # لا تسمح بحذف الصورة الرئيسية إذا كانت الصورة الوحيدة
        if image.is_primary and ProductImage.query.filter_by(product_id=product_id).count() == 1:
            return jsonify({'success': False, 'message': 'لا يمكن حذف الصورة الرئيسية الوحيدة'}), 400
        
        # احذف الملف
        image_path = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], image.filename)
        if os.path.exists(image_path):
            os.remove(image_path)
        
        # احذف السجل
        db.session.delete(image)
        
        # إذا كانت الصورة المحذوفة رئيسية، اجعل أول صورة متبقية رئيسية
        if image.is_primary:
            next_image = ProductImage.query.filter_by(product_id=product_id)\
                .order_by(ProductImage.order).first()
            if next_image:
                next_image.is_primary = True
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'تم حذف الصورة بنجاح'})
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting product image: {str(e)}")
        return jsonify({'success': False, 'message': 'حدث خطأ أثناء حذف الصورة'}), 500

@app.route('/admin/product/<int:product_id>/image/<int:image_id>/make-primary', methods=['POST'])
@login_required
def make_image_primary(product_id, image_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح'}), 403
    
    try:
        # إلغاء تعيين الصورة الرئيسية الحالية
        ProductImage.query.filter_by(product_id=product_id, is_primary=True)\
            .update({ProductImage.is_primary: False})
        
        # تعيين الصورة الجديدة كرئيسية
        image = ProductImage.query.get_or_404(image_id)
        if image.product_id != product_id:
            return jsonify({'success': False, 'message': 'صورة غير صالحة'}), 400
            
        image.is_primary = True
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'تم تعيين الصورة كصورة رئيسية'
        })
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error making image primary: {str(e)}")
        return jsonify({
            'success': False, 
            'message': 'حدث خطأ أثناء تعيين الصورة كصورة رئيسية'
        }), 500

@app.route('/admin/product/toggle_featured/<int:product_id>', methods=['POST'])
@login_required
def toggle_featured(product_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'غير مصرح لك بهذه العملية'}), 403
    
    try:
        product = Product.query.get_or_404(product_id)
        product.is_featured = not product.is_featured
        db.session.commit()
        
        status = 'مميز' if product.is_featured else 'غير مميز'
        return jsonify({
            'success': True, 
            'message': f'تم تحديث حالة المنتج إلى {status}',
            'is_featured': product.is_featured
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error toggling featured status: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@csrf.exempt
@app.route('/search')
def search():
    query = request.args.get('q', '')
    if query:
        products = Product.query.filter(
            (Product.name.ilike(f'%{query}%')) |
            (Product.description.ilike(f'%{query}%'))
        ).all()
    else:
        products = []
    
    return render_template('search_results.html', products=products, query=query)

@app.route('/debug/check_users')
def check_users():
    if app.debug:
        users = User.query.all()
        return jsonify([{'id': user.id, 'username': user.username, 'is_admin': user.is_admin} for user in users])
    return 'Not available in production', 403

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # This will create any missing tables
        
        # إنشاء مستخدم مسؤول افتراضي إذا لم يكن موجوداً
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("تم إنشاء المستخدم المسؤول")
            
        # إنشاء إعدادات افتراضية إذا لم تكن موجودة
        settings = Settings.query.first()
        if not settings:
            settings = Settings()
            db.session.add(settings)
            db.session.commit()
            print("تم إنشاء الإعدادات الافتراضية")
        
    app.run(debug=True, port=5000)
