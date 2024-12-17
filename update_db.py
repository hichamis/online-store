from app import app, db
from models import User
import os
import sqlite3

def update_settings_table():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'store.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # إنشاء جدول الإعدادات إذا لم يكن موجوداً
    c.execute('''CREATE TABLE IF NOT EXISTS settings
                 (id INTEGER PRIMARY KEY,
                  store_name TEXT DEFAULT 'متجر الملابس العربية',
                  store_phone TEXT DEFAULT '+213 123 456 789',
                  store_email TEXT DEFAULT 'info@arabicstore.com',
                  store_address TEXT DEFAULT 'الجزائر العاصمة، الجزائر',
                  currency TEXT DEFAULT 'دج',
                  primary_color TEXT DEFAULT '#0d6efd',
                  secondary_color TEXT DEFAULT '#6c757d',
                  accent_color TEXT DEFAULT '#198754',
                  text_color TEXT DEFAULT '#212529')''')

    # التحقق من وجود إعدادات
    c.execute('SELECT COUNT(*) FROM settings')
    count = c.fetchone()[0]

    if count == 0:
        # إضافة الإعدادات الافتراضية
        c.execute('''INSERT INTO settings (store_name, store_phone, store_email, store_address,
                                         currency, primary_color, secondary_color, accent_color,
                                         text_color)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                 ('متجر الملابس العربية', '+213 123 456 789', 'info@arabicstore.com',
                  'الجزائر العاصمة، الجزائر', 'دج', '#0d6efd', '#6c757d', '#198754', '#212529'))
        conn.commit()

    conn.close()
    print("تم تحديث جدول الإعدادات")

def update_db():
    with app.app_context():
        db.drop_all()
        db.create_all()
        
        # إنشاء مستخدم مسؤول
        admin = User(username='admin', is_admin=True)
        admin.set_password('admin')
        db.session.add(admin)
        db.session.commit()
        
        print('تم تحديث قاعدة البيانات وإنشاء حساب المسؤول')

if __name__ == '__main__':
    update_db()
    update_settings_table()
