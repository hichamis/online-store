from app import app, db
from models import Category, Product, User, Review, Coupon, Slide, Order
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
import random
import os

def seed_data():
    """إضافة بيانات تجريبية"""
    with app.app_context():
        print("بدء إضافة البيانات...")
        
        # إضافة الفئات
        categories_data = [
            {
                "name": "قمصان رجالية",
                "description": "تشكيلة متنوعة من القمصان الرجالية الأنيقة",
                "image_filename": "shirts.jpg"
            },
            {
                "name": "بناطيل رجالية",
                "description": "تشكيلة من البناطيل الرجالية العصرية",
                "image_filename": "pants.jpg"
            },
            {
                "name": "أحذية رجالية",
                "description": "مجموعة مختارة من الأحذية الرجالية الفاخرة",
                "image_filename": "shoes.jpg"
            },
            {
                "name": "اكسسوارات",
                "description": "إكسسوارات رجالية فاخرة",
                "image_filename": "accessories.jpg"
            },
            {
                "name": "ملابس رياضية",
                "description": "ملابس رياضية عالية الجودة",
                "image_filename": "sportswear.jpg"
            },
            {
                "name": "بدلات رسمية",
                "description": "بدلات رسمية أنيقة للمناسبات الخاصة",
                "image_filename": "suits.jpg"
            }
        ]
        
        # إنشاء مجلد الصور إذا لم يكن موجوداً
        uploads_dir = os.path.join('static', 'uploads')
        if not os.path.exists(uploads_dir):
            os.makedirs(uploads_dir)
        
        # إضافة الفئات مع الصور
        for cat_data in categories_data:
            category = Category.query.filter_by(name=cat_data['name']).first()
            if not category:
                category = Category(
                    name=cat_data['name'],
                    description=cat_data['description'],
                    image_filename=cat_data['image_filename']
                )
                db.session.add(category)
        
        db.session.commit()
        print("تم إضافة الفئات")

        # إضافة المنتجات
        products = [
            {
                "name": "قميص كلاسيكي أبيض",
                "description": "قميص رجالي كلاسيكي باللون الأبيض، مناسب للمناسبات الرسمية. قماش قطني 100%",
                "purchase_price": 1500,
                "selling_price": 2500,
                "stock": 50,
                "sizes": "S,M,L,XL,XXL",
                "colors": "أبيض,أزرق فاتح,وردي فاتح",
                "category_name": "قمصان رجالية",
                "image_filename": "product1.jpg"
            },
            {
                "name": "قميص كاجوال",
                "description": "قميص كاجوال عصري، مناسب للإطلالات اليومية",
                "purchase_price": 1200,
                "selling_price": 2000,
                "stock": 40,
                "sizes": "M,L,XL",
                "colors": "أزرق,أحمر,أخضر",
                "category_name": "قمصان رجالية",
                "image_filename": "product2.jpg"
            },
            {
                "name": "بنطلون جينز أزرق",
                "description": "بنطلون جينز رجالي باللون الأزرق الداكن، قصة مستقيمة",
                "purchase_price": 2000,
                "selling_price": 3500,
                "stock": 30,
                "sizes": "30,32,34,36,38",
                "colors": "أزرق داكن,أسود",
                "category_name": "بناطيل رجالية",
                "image_filename": "product3.jpg"
            },
            {
                "name": "بنطلون قماش",
                "description": "بنطلون قماش أنيق للمناسبات الرسمية",
                "purchase_price": 2500,
                "selling_price": 4000,
                "stock": 25,
                "sizes": "32,34,36",
                "colors": "أسود,رمادي,كحلي",
                "category_name": "بناطيل رجالية",
                "image_filename": "product4.jpg"
            },
            {
                "name": "حذاء رياضي نايكي",
                "description": "حذاء رياضي مريح مناسب للمشي والرياضة",
                "purchase_price": 3000,
                "selling_price": 5000,
                "stock": 25,
                "sizes": "40,41,42,43,44,45",
                "colors": "أسود,أبيض,رمادي",
                "category_name": "أحذية رجالية",
                "image_filename": "product5.jpg"
            },
            {
                "name": "حذاء كلاسيكي",
                "description": "حذاء كلاسيكي جلد طبيعي للمناسبات الرسمية",
                "purchase_price": 4000,
                "selling_price": 6500,
                "stock": 20,
                "sizes": "41,42,43,44",
                "colors": "أسود,بني",
                "category_name": "أحذية رجالية",
                "image_filename": "product6.jpg"
            },
            {
                "name": "حزام جلد طبيعي",
                "description": "حزام رجالي من الجلد الطبيعي 100%",
                "purchase_price": 800,
                "selling_price": 1500,
                "stock": 40,
                "sizes": "105,110,115",
                "colors": "بني,أسود",
                "category_name": "اكسسوارات",
                "image_filename": "product7.jpg"
            },
            {
                "name": "ربطة عنق حرير",
                "description": "ربطة عنق حرير فاخرة بتصاميم عصرية",
                "purchase_price": 600,
                "selling_price": 1200,
                "stock": 35,
                "sizes": "one size",
                "colors": "أحمر,أزرق,أسود",
                "category_name": "اكسسوارات",
                "image_filename": "product8.jpg"
            },
            {
                "name": "طقم رياضي نايكي",
                "description": "طقم رياضي كامل مناسب للتمارين الرياضية",
                "purchase_price": 3500,
                "selling_price": 5500,
                "stock": 30,
                "sizes": "S,M,L,XL",
                "colors": "أسود,رمادي,أزرق",
                "category_name": "ملابس رياضية",
                "image_filename": "product9.jpg"
            },
            {
                "name": "بدلة رسمية",
                "description": "بدلة رسمية فاخرة للمناسبات الخاصة",
                "purchase_price": 8000,
                "selling_price": 12000,
                "stock": 15,
                "sizes": "48,50,52,54",
                "colors": "أسود,كحلي,رمادي",
                "category_name": "بدلات رسمية",
                "image_filename": "product10.jpg"
            }
        ]

        for prod_data in products:
            category = Category.query.filter_by(name=prod_data["category_name"]).first()
            if category:
                product = Product.query.filter_by(name=prod_data["name"]).first()
                if not product:
                    product = Product(
                        name=prod_data["name"],
                        description=prod_data["description"],
                        purchase_price=prod_data["purchase_price"],
                        selling_price=prod_data["selling_price"],
                        stock=prod_data["stock"],
                        sizes=prod_data["sizes"],
                        colors=prod_data["colors"],
                        category_id=category.id,
                        image_filename=prod_data["image_filename"]
                    )
                    db.session.add(product)
        db.session.commit()
        print("تم إضافة المنتجات")

        # Set some products as featured
        products = Product.query.all()
        featured_products = random.sample(products, min(8, len(products)))
        for product in featured_products:
            product.is_featured = True
        
        db.session.commit()
        print("تم تحديد المنتجات المميزة")

        # إضافة الكوبونات
        coupons = [
            {
                "code": "WELCOME2024",
                "discount": 15,
                "valid_from": datetime(2024, 1, 1),
                "valid_until": datetime(2024, 12, 31),
                "is_active": True
            },
            {
                "code": "SUMMER50",
                "discount": 50,
                "valid_from": datetime(2024, 6, 1),
                "valid_until": datetime(2024, 8, 31),
                "is_active": True
            },
            {
                "code": "RAMADAN30",
                "discount": 30,
                "valid_from": datetime(2024, 3, 1),
                "valid_until": datetime(2024, 4, 30),
                "is_active": True
            },
            {
                "code": "EID25",
                "discount": 25,
                "valid_from": datetime(2024, 4, 1),
                "valid_until": datetime(2024, 5, 31),
                "is_active": True
            }
        ]

        for coupon_data in coupons:
            coupon = Coupon.query.filter_by(code=coupon_data["code"]).first()
            if not coupon:
                coupon = Coupon(**coupon_data)
                db.session.add(coupon)
        db.session.commit()
        print("تم إضافة الكوبونات")

        # إضافة السلايدات
        slides = [
            {
                "title": "تخفيضات الصيف",
                "description": "خصومات تصل إلى 50% على جميع المنتجات",
                "link": "/products",
                "active": True,
                "order": 1,
                "image_filename": "slide1.jpg"
            },
            {
                "title": "تشكيلة رمضان",
                "description": "أحدث التشكيلات لشهر رمضان المبارك",
                "link": "/products",
                "active": True,
                "order": 2,
                "image_filename": "slide2.jpg"
            },
            {
                "title": "العودة للمدارس",
                "description": "عروض خاصة بمناسبة العودة للمدارس",
                "link": "/products",
                "active": True,
                "order": 3,
                "image_filename": "slide3.jpg"
            }
        ]

        for slide_data in slides:
            slide = Slide.query.filter_by(title=slide_data["title"]).first()
            if not slide:
                slide = Slide(
                    title=slide_data["title"],
                    description=slide_data["description"],
                    link=slide_data["link"],
                    active=slide_data["active"],
                    order=slide_data["order"],
                    image_filename=slide_data["image_filename"]
                )
                db.session.add(slide)
        db.session.commit()
        print("تم إضافة السلايدات")

        # إضافة تقييمات للمنتجات
        reviews = [
            "منتج ممتاز وجودة عالية",
            "سعر مناسب جداً",
            "خامة ممتازة وتصميم جميل",
            "سرعة في التوصيل وخدمة ممتازة",
            "راضي جداً عن المنتج",
            "أنصح به بشدة",
            "تجربة شراء موفقة"
        ]
        
        products = Product.query.all()
        for product in products:
            for _ in range(random.randint(3, 7)):  # كل منتج يحصل على 3-7 تقييمات
                review = Review(
                    product_id=product.id,
                    name=f"عميل_{random.randint(1000, 9999)}",
                    rating=random.randint(4, 5),  # تقييمات إيجابية غالباً
                    comment=random.choice(reviews),
                    created_at=datetime.now() - timedelta(days=random.randint(1, 60))
                )
                db.session.add(review)
        db.session.commit()
        print("تم إضافة التقييمات")

        # إضافة طلبات وهمية
        customer_names = [
            "أحمد محمد", "محمد علي", "عمر خالد", "سعيد أحمد",
            "خالد عبدالله", "عبدالرحمن محمد", "يوسف أحمد", "إبراهيم علي"
        ]
        addresses = [
            "شارع الجزائر رقم 123، الجزائر العاصمة",
            "شارع تونس رقم 456، وهران",
            "شارع المغرب رقم 789، قسنطينة",
            "شارع مصر رقم 321، عنابة",
            "شارع السودان رقم 654، سطيف"
        ]
        statuses = ["pending", "processing", "completed", "cancelled"]
        payment_statuses = ["pending", "paid", "refunded"]

        products = Product.query.all()
        for _ in range(50):  # إنشاء 50 طلب
            product = random.choice(products)
            quantity = random.randint(1, 3)
            total_price = product.selling_price * quantity
            profit = (product.selling_price - product.purchase_price) * quantity
            order_date = datetime.now() - timedelta(days=random.randint(0, 90))
            
            # احتمالية 20% أن يكون الطلب جديد
            is_new = random.random() < 0.2

            order = Order(
                customer_name=random.choice(customer_names),
                customer_phone=f"0555{random.randint(100000, 999999)}",
                customer_address=random.choice(addresses),
                product_id=product.id,
                quantity=quantity,
                size=random.choice(product.sizes.split(',')),
                color=random.choice(product.colors.split(',')),
                total_price=total_price,
                profit=profit,
                status=random.choice(statuses),
                payment_status=random.choice(payment_statuses),
                order_date=order_date,
                shipping_cost=random.choice([500, 750, 1000]),
                is_new=is_new
            )
            
            # احتمالية 30% لاستخدام كوبون
            if random.random() < 0.3:
                coupon = random.choice(Coupon.query.all())
                order.coupon_id = coupon.id
                order.coupon_code = coupon.code
                order.discount = total_price * (coupon.discount / 100)
                order.final_price = total_price - order.discount
            else:
                order.final_price = total_price
                
            db.session.add(order)
        db.session.commit()
        print("تم إضافة الطلبات")

        print("تم إضافة جميع البيانات بنجاح!")

if __name__ == "__main__":
    seed_data()
