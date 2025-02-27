from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import numpy as np
# from scipy.sparse.linalg import svds
import pymysql
#import pandas as pd
# استيراد قاعدة البيانات من الملف الجديد
from models import db, User, Course, Enrollment#, Student
# from flask_mysqldb import MySQL
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from recommendation import get_recommendations
#from sqlalchemy import create_engine
from svd_main import get_recommend
 
#✅ استخدام Random Forest لتوقع أداء الطالب في الدورات القادمة

import os
import re
app = Flask(__name__)


#app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///students.db"
#app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://u804311892_agline:Ah#630540@193.203.184.99:3306/u804311892_agline"
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:rootroot@localhost:3306/agline"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SECRET_KEY'] = 'your_secret_key'

db.init_app(app)  # ربط قاعدة البيانات بتطبيق Flask
bcrypt = Bcrypt(app)


login_manager = LoginManager(app)
login_manager.login_view = 'login'
def get_db_connection():
    return pymysql.connect(host='localhost', user='root', password='rootroot', database='agline', cursorclass=pymysql.cursors.DictCursor)






@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    student_id = current_user.id
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT* FROM courses ")# WHERE enrollments.user_id = %s", (student_id,))
    courses = cursor.fetchall()
    cursor.close()
    conn.close()
    #courses = Course.query.filter_by(user_id=current_user.id)
    #recommendation = get_recommendations(1)  # مؤقتًا لـ user_id=1
    #svd_main = get_recommend(current_user.id)  # مؤقتًا لـ user_id=1
	 #print('ss',svd_main.tolist())
    return render_template(
    'dashboard.html',
    courses=courses,
    recommendation=[],
    #recommend=svd_main,
     user=current_user)


# تحديث `gpa` للمستخدم
# تحديث GPA للمستخدم
@app.route('/update_gpa', methods=['GET', 'POST'])
def update_gpa():
    if request.method == 'POST':
        try:
            # استقبال البيانات من النموذج أو JSON
            user_id = request.form.get('user_id') or request.json.get('user_id')
            new_gpa = request.form.get('new_gpa') or request.json.get('gpa')

            # البحث عن المستخدم في قاعدة البيانات
            user = User.query.filter_by(id=user_id).first()

            if user:
                user.gpa = float(new_gpa)  # تحديث المعدل التراكمي
                db.session.commit()  # حفظ التغييرات
                flash(f"تم تحديث GPA بنجاح إلى {user.gpa} ✅", "success")
                return redirect(url_for('update_gpa'))
            else:
                flash("المستخدم غير موجود ❌", "danger")

        except Exception as e:
            flash(f"خطأ أثناء تحديث GPA: {str(e)} ❌", "danger")

    # عند زيارة الصفحة بـ GET، يتم عرض النموذج
    return render_template('update_gpa.html', user=current_user)
	
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form['phone']
        password = request.form['password']
        user = User.query.filter_by(phone=phone).first()
        
        #hashed_password = generate_password_hash(password)
        print(bcrypt.check_password_hash(user.password_hash, password))
        print(password)
		
        if user and bcrypt.check_password_hash(user.password_hash, password):#and check_password_hash(user.password_hash, hashed_password):
            login_user(user)
            return redirect(url_for('dashboard'))
			
            flash('User with this phone already exists!', 'danger')
    return render_template('login.html', title="Login")

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/recommend')
@login_required
def recommend():
    recommendations = get_recommendations(current_user.id)
    return render_template('recommend.html', title="Recommendations", recommendations=recommendations)



@app.route('/myfile')

@login_required
def myfile():
    
    
    return render_template('myfile.html')

''''
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        #email = request.form['email']
        password = request.form['password']

        # تشفير كلمة المرور
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # إضافة المستخدم لقاعدة البيانات
        new_user = User(username=username,  password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('تم إنشاء الحساب بنجاح! يمكنك تسجيل الدخول الآن.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')
'''

# Validate Phone Number
def is_valid_phone(phone):
    return re.fullmatch(r"^\d{9,15}$", phone) is not None

# Registration Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form['full_name']
        phone = request.form['phone']
        password = request.form['password']
        gpa = request.form.get('gpa', type=float)
        major = request.form['major']

        #if not is_valid_phone(phone):
            #flash('Invalid phone number! Must be 9-15 digits.', 'danger')
            #return redirect(url_for('register'))

        existing_user = User.query.filter_by(phone=phone).first()
        if existing_user:
            flash('User with this phone already exists!', 'danger')
            return redirect(url_for('register'))
        # تشفير كلمة المرور
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        #hashed_password = generate_password_hash(password)

        new_user = User(full_name=full_name, phone=phone, password_hash=hashed_password, gpa=gpa, major=major)
        db.session.add(new_user)
        db.session.commit()


        flash('تم إنشاء الحساب بنجاح! يمكنك تسجيل الدخول الآن.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')
	
	
	
	

# ✅ API لاسترجاع الدورات الموصى بها بناءً على المعدل التراكمي
@app.route('/api/recommend_courses', methods=['GET'])
def recommend_courses():
    if current_user.id==0:
        return jsonify({"error": "User not logged in"}), 401

    student_id = current_user.id
    conn = get_db_connection()
    cursor = conn.cursor()

    # 🔹 استرجاع معدل الطالب التراكمي
    cursor.execute("SELECT gpa FROM users WHERE id = %s", (student_id,))
    student = cursor.fetchone()
    if not student:
        return jsonify({"error": "Student not found"}), 404

    student_gpa = student['gpa']

    # 🔹 استرجاع الدورات المناسبة بناءً على المعدل التراكمي
    cursor.execute("""
        SELECT *
        FROM courses
        WHERE gpa_requirement <= %s
        ORDER BY gpa_requirement DESC
    """, (student_gpa,))

    recommendations = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(recommendations)	
# إنشاء الجداول في قاعدة البيانات
with app.app_context():
    db.create_all()
    print("✅ تم إنشاء الجداول في قاعدة البيانات بنجاح!")
print(current_user)
if __name__ == '__main__':
    app.run(debug=True)
   
    