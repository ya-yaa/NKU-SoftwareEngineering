from flask import Flask, render_template, request, redirect, url_for, session, flash, render_template_string
from matplotlib import pyplot as plt
from fish_price_spider import get_today_fish_prices
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import requests
import csv
import os
import base64
from zhipuai import ZhipuAI
import pandas as pd
import numpy as np
from flask import flash, redirect, url_for, request, session
from pymysql import connect
from mysql.connector import connect
from flask import send_file
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'my_secret_key'  # 用于 session 加密

# 数据库连接配置
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'database': 'visualsystem',
    'charset': 'utf8mb4'
}

client = ZhipuAI(api_key="13680a80f7b9444880e714e04730e260.xAzPHXxzK5CGOFA6") 

# 用户注册
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # 提取注册表单中填写的字段数据
        username = request.form['username']
        password = request.form['password']
        phone = request.form['phone']
        role = int(request.form['role'])

        # 禁止注册管理员账号
        if role == 0:
            flash("不允许注册管理员账号。")
            return redirect(url_for('register'))

        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()

        # 检查用户名是否已存在
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            flash("用户名已存在，请更换。")
            conn.close()
            return redirect(url_for('register'))

        # 加密密码并写入数据库
        hashed_pwd = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users (username, password, role, phone) VALUES (%s, %s, %s, %s)",
            (username, hashed_pwd, role, phone)
        )
        conn.commit()

        # 记录操作日志（注册）
        cursor.execute(
            "INSERT INTO action_logs (username,  role, action_type, timestamp) VALUES (%s, %s, %s, %s)",
            (username, role, '注册', datetime.now())
        )
        conn.commit()

        conn.close()

        flash("注册成功，请登录。")
        return redirect(url_for('login'))

    return render_template('register.html')

# 用户登录
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT id, password, role FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        # 验证密码是否正确
        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            session['username'] = username
            session['role'] = user[2]

            # 记录操作日志（登录）
            cursor.execute(
                "INSERT INTO action_logs (username,  role, action_type, timestamp) VALUES (%s, %s, %s, %s)",
                (username, user[2], '登录', datetime.now())
            )
            conn.commit()

            conn.close()

            flash("登录成功。", "login_success")
            return redirect(url_for('home'))
        else:
            flash("用户名或密码错误。")
            conn.close()
            return redirect(url_for('login'))

    return render_template('login.html')

# 首页（登录后访问）
@app.route('/')
def home():
    if 'username' in session:
        return render_template('home.html', username=session['username'], role=session['role'])
    return redirect(url_for('login'))

# 用户退出
@app.route('/logout')
def logout():
    session.clear()
    flash("您已退出登录。")
    return redirect(url_for('login'))

# 管理员查看操作日志
@app.route('/admin/logs')
def admin_logs():
    if session.get('role') != 0:  
        flash("您无权访问此页面。")
        return redirect(url_for('home'))

    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username,  role, action_type, timestamp FROM action_logs ORDER BY timestamp DESC")
    logs = cursor.fetchall()
    conn.close()
    return render_template('admin_logs.html', logs=logs)

# 管理员查看所有用户
@app.route('/admin/users')
def admin_users():
    if session.get('role') != 0:  
        flash("您无权访问此页面。")
        return redirect(url_for('home'))

    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role, phone FROM users")
    users = cursor.fetchall()
    conn.close()
    return render_template('admin_users.html', users=users)


# 修改用户信息
@app.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    if session.get('role') != 0:
        flash("无权限")
        return redirect(url_for('home'))

    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = int(request.form['role'])
        phone = request.form['phone']

        if password:
            hashed_pwd = generate_password_hash(password)
            cursor.execute("UPDATE users SET username=%s, password=%s, role=%s, phone=%s WHERE id=%s",
                           (username, hashed_pwd, role, phone, user_id))
        else:
            cursor.execute("UPDATE users SET username=%s, role=%s, phone=%s WHERE id=%s",
                           (username, role, phone, user_id))

        conn.commit()
        conn.close()
        flash("用户信息已更新")
        return redirect(url_for('admin_users'))

    cursor.execute("SELECT id, username, role, phone FROM users WHERE id=%s", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return render_template('edit_user.html', user=user)


# 删除用户
@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if session.get('role') != 0:
        flash("无权限")
        return redirect(url_for('home'))

    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id=%s", (user_id,))
    conn.commit()
    conn.close()
    flash("用户已删除")
    return redirect(url_for('admin_users'))


# 添加用户
@app.route('/admin/users/add', methods=['GET', 'POST'])
def add_user():
    if session.get('role') != 0:
        flash("无权限")
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = int(request.form['role'])
        phone = request.form['phone']

        hashed_pwd = generate_password_hash(password)

        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password, role, phone) VALUES (%s, %s, %s, %s)",
                       (username, hashed_pwd, role, phone))
        conn.commit()
        conn.close()

        flash("新用户添加成功")
        return redirect(url_for('admin_users'))

    return render_template('add_user.html')

from flask import flash, redirect, url_for

@app.route('/admin/upload_fishes', methods=['GET', 'POST'])
def upload_fishes():
    if session.get('role') != 0:
        flash("无权限", "error")  # 指定类别为 error
        return redirect(url_for('home'))

    if request.method == 'POST':
        file = request.files['file']
        if not file or file.filename == '':
            flash("请选择要上传的文件。", "error")  # 指定类别为 error
            return redirect(url_for('upload_fishes'))

        try:
            # 连接数据库
            conn = connect(**db_config)
            cursor = conn.cursor()

            # 使用pandas读取Excel文件
            if file.filename.endswith('.xls'):
                df = pd.read_excel(file, engine='xlrd')
            elif file.filename.endswith('.xlsx'):
                df = pd.read_excel(file, engine='openpyxl')
            elif file.filename.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                raise ValueError("Unsupported file format")

            # 检查必要的列是否存在
            required_columns = {'species', 'length1', 'length2', 'length3', 'height', 'date', 'weight', 'width'}
            if not required_columns.issubset(df.columns):
                raise ValueError("文件内容错误")

            # 插入数据到数据库
            for index, row in df.iterrows():
                species = row.get('species')
                length1 = row.get('length1')
                length2 = row.get('length2')
                length3 = row.get('length3')
                height = row.get('height')
                date = row.get('date')
                weight = row.get('weight')
                width = row.get('width')

                # 检查是否有任何值为空
                if any(pd.isna([species, length1, length2, length3, height, date, weight, width])):
                    raise ValueError("文件内容错误")

                cursor.execute(
                    "INSERT INTO fishes (species, length1, length2, length3, height, date, weight, width) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (species, length1, length2, length3, height, date, weight, width)
                )

            conn.commit()
            conn.close()
            flash("数据上传成功！", "success")  # 指定类别为 success
            return redirect(url_for('upload_fishes'))

        except ValueError as ve:
            # 特定错误信息，并指定类别为 error
            flash(str(ve), "error")
        except Exception as e:
            # 其他错误信息，并指定类别为 error
            flash(f"上传失败：{str(e)}", "error")

        return redirect(url_for('upload_fishes'))

    return render_template('upload_fishes.html')

@app.route('/admin/export_fishes', methods=['GET'])
def export_fishes():
    if session.get('role') != 0:
        flash("无权限", "error")
        return redirect(url_for('home'))

    # 获取用户请求的格式，默认是 csv
    file_format = request.args.get('format', 'csv').lower()
    if file_format not in ['csv', 'xls', 'xlsx']:
        flash("不支持的文件格式", "error")
        return redirect(url_for('upload_fishes')) 

    try:
        # 连接数据库
        conn = connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # 查询所有鱼类数据
        cursor.execute("SELECT fish_id, species, length1, length2, length3, height, date, weight, width FROM fishes")
        data = cursor.fetchall()

        conn.close()

        # 将数据转为 pandas DataFrame
        df = pd.DataFrame(data)

        # 设置响应头以触发浏览器下载
        output = BytesIO()

        if file_format == 'csv':
            df.to_csv(output, index=False, encoding='utf-8-sig')
            content_type = 'text/csv'
            filename = f"fishes_{datetime.now().strftime('%Y%m%d')}.csv"
        # elif file_format == 'xls':
        #     df.to_excel(output, index=False, engine='xlwt')
        #     content_type = 'application/vnd.ms-excel'
        #     filename = f"fishes_{datetime.now().strftime('%Y%m%d')}.xls"
        elif file_format == 'xlsx':
            df.to_excel(output, index=False, engine='openpyxl')
            content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            filename = f"fishes_{datetime.now().strftime('%Y%m%d')}.xlsx"

        # 构造响应
        output.seek(0)
        return send_file(
            output,
            mimetype=content_type,
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        print("导出失败，错误详情：", str(e))  # 关键调试信息
        flash(f"导出失败: {str(e)}", "error")
        return redirect(url_for('fish_farms'))
    
@app.route('/admin/export_fish_farms', methods=['GET'])
def export_fish_farms():
    if session.get('role') != 0:
        flash("无权限", "error")
        return redirect(url_for('home'))

    # 获取用户请求的格式，默认是 csv
    file_format = request.args.get('format', 'csv').lower()  # 修改为使用 GET 参数
    if file_format not in ['csv', 'xlsx']:
        flash("不支持的文件格式", "error")
        return redirect(url_for('water_quality_data')) 

    try:
        # 连接数据库
        conn = connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # 查询所有渔场的数据
        query = """
            SELECT id, province, river_basin, section_name, monitor_time, quality_level,
                   water_temp, ph, dissolved_oxygen, conductivity, turbidity, cod_mn,
                   ammonia_nitrogen, total_phosphorus, total_nitrogen, chlorophyll_a,
                   algae_density, site_status, farm_id, source_date 
            FROM water_quality_data
        """
        cursor.execute(query)
        data = cursor.fetchall()

        conn.close()

        # 将数据转为 pandas DataFrame
        df = pd.DataFrame(data)

        # 设置响应头以触发浏览器下载
        output = BytesIO()

        if file_format == 'csv':
            df.to_csv(output, index=False, encoding='utf-8-sig')
            content_type = 'text/csv'
            filename = f"water_quality_data_{datetime.now().strftime('%Y%m%d')}.csv"
        elif file_format == 'xlsx':
            df.to_excel(output, index=False, engine='openpyxl')
            content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            filename = f"water_quality_data_{datetime.now().strftime('%Y%m%d')}.xlsx"

        # 构造响应
        output.seek(0)
        return send_file(
            output,
            mimetype=content_type,
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        print("导出失败，错误详情：", str(e))  # 关键调试信息
        flash(f"导出失败: {str(e)}", "error")
        return redirect(url_for('fish_farms'))

# 渔场列表与搜索页面
@app.route('/fish_farms', methods=['GET'])
def fish_farms():
    # 获取查询参数
    search_query = request.args.get('search', '').strip()
    page = int(request.args.get('page', 1))
    per_page = 10  # 每页10条
    offset = (page - 1) * per_page

    # 连接数据库
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()

    # 构建查询
    like_pattern = f"%{search_query}%"
    if search_query:
        # 获取总记录数
        cursor.execute("""
            SELECT COUNT(*) FROM fish_farms 
            WHERE section_name LIKE %s OR river_basin LIKE %s OR province LIKE %s
        """, (like_pattern, like_pattern, like_pattern))
        total = cursor.fetchone()[0]

        # 获取当前页数据
        cursor.execute("""
            SELECT * FROM fish_farms 
            WHERE section_name LIKE %s OR river_basin LIKE %s OR province LIKE %s
            LIMIT %s OFFSET %s
        """, (like_pattern, like_pattern, like_pattern, per_page, offset))
    else:
        cursor.execute("SELECT COUNT(*) FROM fish_farms")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT * FROM fish_farms LIMIT %s OFFSET %s", (per_page, offset))

    fish_farms = cursor.fetchall()
    conn.close()

    total_pages = (total + per_page - 1) // per_page

    return render_template(
        'fish_farms.html',
        fish_farms=fish_farms,
        search_query=search_query,
        page=page,
        total_pages=total_pages
    )


@app.route('/fish_farm/<int:farm_id>')
def view_fish_farm(farm_id):
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()

    # 获取渔场信息
    cursor.execute("SELECT * FROM fish_farms WHERE farm_id = %s", (farm_id,))
    farm = cursor.fetchone()
    conn.close()

    # 获取经纬度
    province = farm[2]  # 第三列为省份
    latitude, longitude = get_coordinates(province)

    # 获取天气数据
    weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&hourly=temperature_2m,rain&daily=temperature_2m_max,temperature_2m_min&timezone=auto&models=cma_grapes_global"
    weather_response = requests.get(weather_url)

    if weather_response.status_code == 200:
        weather_data = weather_response.json()
        today_temp_max = weather_data['daily']['temperature_2m_max'][0]
        today_temp_min = weather_data['daily']['temperature_2m_min'][0]
        current_temp = weather_data['hourly']['temperature_2m'][0]
        current_rain = weather_data['hourly']['rain'][0]
    else:
        today_temp_max = today_temp_min = current_temp = current_rain = '暂无数据'

    video_url = url_for('static', filename='videos/test.mp4')


    return render_template(
        'fish_farm_detail.html',
        farm=farm,
        current_temp=current_temp,
        current_rain=current_rain,
        today_temp_max=today_temp_max,
        today_temp_min=today_temp_min,
        video_url=video_url
    )

def csv_to_json_array(csv_file_path):
    # 读取CSV文件并转换为JSON数组
    with open(csv_file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)  # 自动读取CSV表头作为字典键
        json_array = []
        for row in reader:
            # 处理每行数据，转换数值类型（可选）
            processed_row = {
                "Species": row["Species"],
                "Weight(g)": float(row["Weight(g)"]),
                "Length1(cm)": float(row["Length1(cm)"]),
                "Length2(cm)": float(row["Length2(cm)"]),
                "Length3(cm)": float(row["Length3(cm)"]),
                "Height(cm)": float(row["Height(cm)"]),
                "Width(cm)": float(row["Width(cm)"])
            }
            json_array.append(processed_row)
        return json_array

def db_to_json_array():
    # 连接数据库
    conn = pymysql.connect(**db_config)
    mycursor = conn.cursor()
    # 执行SQL查询语句
    query = "SELECT species, weight, length1, length2, length3, height, width FROM fishes"
    mycursor.execute(query)
    results = mycursor.fetchall()

    json_array = []
    for row in results:
        processed_row = {
            "Species": row[0],
            "Weight(g)": row[1],
            "Length1(cm)": row[2],
            "Length2(cm)": row[3],
            "Length3(cm)": row[4],
            "Height(cm)": row[5],
            "Width(cm)": row[6]
        }
        json_array.append(processed_row)

    mycursor.close()
    conn.close()
    return json_array 

@app.route('/fish_farm_detail/<int:farm_id>')
def v_fish_farm(farm_id):
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()

    # 获取渔场信息
    # csv_path = "Fish.csv"  # CSV文件路径

    # 获取当前文件（app.py）所在目录的绝对路径
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # 拼接得到 CSV 文件的完整路径
    csv_path = os.path.join(base_dir, "Fish.csv")

    fish_data = db_to_json_array()
    # 修正后的 SQL 查询，添加 source_a 条件
    cursor.execute("SELECT * FROM water_quality_data WHERE farm_id = %s AND source_date = %s", (farm_id, '2020-05-08'))
    wat = cursor.fetchone()
    conn.close()
    

    if not wat:
        return "未找到对应水质数据", 404

    # 将罗马数字转换为阿拉伯数字
    arabic_quality_level = roman_to_int(wat[5]) if wat[5] else 0

    return render_template(
        'wat.html',
        wat=wat,
        quality_level=arabic_quality_level,
        water_temp=wat[6],
        ph=wat[7],
        dissolved_oxygen=wat[8],
        turbidity=wat[10],
        cod_mn=wat[11],
        fishData=fish_data
    )

def roman_to_int(roman):
    roman_map = {'I': 1, 'V': 5, 'Ⅲ': 3, 'Ⅱ': 2}
    total = 0
    prev_value = 0
    
    for char in reversed(roman):
        value = roman_map.get(char, 0)
        if value >= prev_value:
            total += value
        else:
            total -= value
        prev_value = value
    
    return total


def get_coordinates(province):
    province_coords = {
        "北京市": (39.9042, 116.4074),
        "天津市": (39.3434, 117.3616),
        "上海市": (31.2304, 121.4737),
        "重庆市": (29.5630, 106.5516),
        "河北省": (38.0428, 114.5149),
        "山西省": (37.8735, 112.5624),
        "辽宁省": (41.8057, 123.4315),
        "吉林省": (43.8965, 125.3264),
        "黑龙江省": (45.8038, 126.5349),
        "江苏省": (32.0603, 118.7969),
        "浙江省": (30.2741, 120.1551),
        "安徽省": (31.8612, 117.2857),
        "福建省": (26.0745, 119.2965),
        "江西省": (28.6765, 115.8922),
        "山东省": (36.6683, 117.0204),
        "河南省": (34.7466, 113.6254),
        "湖北省": (30.5928, 114.3055),
        "湖南省": (28.2282, 112.9388),
        "广东省": (23.3790, 113.7633),
        "海南省": (20.0440, 110.1983),
        "四川省": (30.5728, 104.0668),
        "贵州省": (26.6476, 106.6302),
        "云南省": (25.0453, 102.7097),
        "陕西省": (34.3416, 108.9398),
        "甘肃省": (36.0611, 103.8343),
        "青海省": (36.6209, 101.7801),
        "台湾省": (25.0308, 121.5200),
        "内蒙古自治区": (40.8175, 111.7652),
        "广西壮族自治区": (22.8170, 108.3669),
        "西藏自治区": (29.6520, 91.1721),
        "宁夏回族自治区": (38.4872, 106.2309),
        "新疆维吾尔自治区": (43.8256, 87.6168),
        "香港特别行政区": (22.3193, 114.1694),
        "澳门特别行政区": (22.1987, 113.5439)
    }
    return province_coords.get(province, (0, 0))

# 今日鱼群价格
@app.route("/fish_price_today")
def fish_price_today():
    fish_data = get_today_fish_prices()
    return render_template("fish_price_today.html", data=fish_data)

# 数据中心（由警报改）
from datetime import date

@app.route('/datas')
def datas():
    if 'user_id' not in session or session.get('role') != 1:
        flash("请先登录养殖户账号。")
        return redirect(url_for('login'))

    user_id = session['user_id']
    today = date.today()

    conn = pymysql.connect(**db_config)
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # 查询该用户的所有渔场
    cursor.execute("SELECT * FROM fish_farms WHERE farmer_id = %s", (user_id,))
    farms = cursor.fetchall()

    # 预设标准值范围
    standards = {
        'water_temp': '10~30℃',
        'ph': '6.5~8.5',
        'dissolved_oxygen': '≥5',
        'conductivity': '0~1500',
        'turbidity': '0~5',
        'cod_mn': '≤6',
        'ammonia_nitrogen': '≤1.5',
        'total_phosphorus': '≤0.2',
        'total_nitrogen': '≤2.0',
        'chlorophyll_a': '≤15',
        'algae_density': '≤10000',
    }

    def check_exceed(key, value):
        try:
            value = float(value)
            if key == 'water_temp':
                return not (10 <= value <= 30)
            elif key == 'ph':
                return not (6.5 <= value <= 8.5)
            elif key == 'dissolved_oxygen':
                return value < 5
            elif key == 'conductivity':
                return value > 1500
            elif key == 'turbidity':
                return value > 5
            elif key == 'cod_mn':
                return value > 6
            elif key == 'ammonia_nitrogen':
                return value > 1.5
            elif key == 'total_phosphorus':
                return value > 0.2
            elif key == 'total_nitrogen':
                return value > 2.0
            elif key == 'chlorophyll_a':
                return value > 15
            elif key == 'algae_density':
                return value > 10000
        except:
            return False
        return False

    data = []
    for farm in farms:
        cursor.execute("""
            SELECT * FROM water_quality_data 
            WHERE farm_id = %s  
            AND DATE_FORMAT(monitor_time, '%%m-%%d %%H:%%i:%%s') <= DATE_FORMAT(NOW(), '%%m-%%d %%H:%%i:%%s')
            ORDER BY DATE_FORMAT(monitor_time, '%%m-%%d %%H:%%i:%%s') DESC 
            LIMIT 1
        """, (farm['farm_id']))
        row = cursor.fetchone()
        if row:
            quality_level = row.get('quality_level', '未知')
            site_status = row.get('site_status', '未知')
            values = {}
            for key in standards:
                if key in row:
                    values[key] = {
                        'data': row[key],
                        'standard': standards[key],
                        'exceed': check_exceed(key, row[key])
                    }
            farm_display = {
                'farm_id': farm['farm_id'],
                'province': farm['province'],
                'river_basin': farm['river_basin'],
                'section_name': farm['section_name'],
                'monitor_time': row['monitor_time'],
                'quality_level': quality_level,
                'site_status': site_status,
                'values': values
            }
            data.append(farm_display)

    conn.close()
    return render_template('datas.html', data=data)

from flask import jsonify
@app.route('/alerts')
def alerts():
    if 'user_id' not in session or session.get('role') != 1:
        return jsonify([])

    user_id = session['user_id']
    today = date.today()

    conn = pymysql.connect(**db_config)
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute("SELECT * FROM fish_farms WHERE farmer_id = %s", (user_id,))
    farms = cursor.fetchall()

    def check_exceed(key, value):
        try:
            value = float(value)
            if key == 'water_temp':
                return not (10 <= value <= 30)
            elif key == 'ph':
                return not (6.5 <= value <= 8.5)
            elif key == 'dissolved_oxygen':
                return value < 5
            elif key == 'conductivity':
                return value > 1500
            elif key == 'turbidity':
                return value > 5
            elif key == 'cod_mn':
                return value > 6
            elif key == 'ammonia_nitrogen':
                return value > 1.5
            elif key == 'total_phosphorus':
                return value > 0.2
            elif key == 'total_nitrogen':
                return value > 2.0
            elif key == 'chlorophyll_a':
                return value > 15
            elif key == 'algae_density':
                return value > 10000
        except:
            return False
        return False

    alerts = []
    for farm in farms:
        cursor.execute("""
            SELECT * FROM water_quality_data 
            WHERE farm_id = %s  
            ORDER BY monitor_time DESC 
            LIMIT 1
        """, (farm['farm_id'],))
        row = cursor.fetchone()
        if row and row.get('site_status') == '正常':
            for key, value in row.items():
                if key in ['water_temp', 'ph', 'dissolved_oxygen', 'conductivity',
                           'turbidity', 'cod_mn', 'ammonia_nitrogen',
                           'total_phosphorus', 'total_nitrogen', 'chlorophyll_a', 'algae_density']:
                    if check_exceed(key, value):
                        alerts.append({
                            'section_name': farm['section_name'],
                            'param': key,
                            'value': value
                        })

    conn.close()
    return jsonify(alerts)


# 智能中心
@app.route('/AI_center', methods=['GET', 'POST'])
def AI_center():
    result = None
    img_data = None
    fish_type = None
    suggestion = None
    selected_species = None
    predictions = None
    encoded_plot = None
    error_msg = None
    length_suggestion = None


    # 1. 获取鱼类种类列表
    try:
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='123456',
            database='visualsystem',
            
        )
        cursor = connection.cursor()
        cursor.execute("SELECT DISTINCT species FROM fishes")
        species_list = [row[0] for row in cursor.fetchall()]
        connection.close()
    except Exception as e:
        species_list = []
        error_msg = f"数据库连接失败：{str(e)}"

    if request.method == 'POST':
        form_type = request.form.get('form_type')

        # 2. 图片识别模块
        if form_type == 'image_recognition':
            file = request.files.get('image')
            if file and file.filename != '':
                img_bytes = file.read()
                img_data = base64.b64encode(img_bytes).decode('utf-8')

                response = client.chat.completions.create(
                    model="glm-4v-plus-0111",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "image_url", "image_url": {"url": img_data}},
                                {"type": "text", "text": "这是什么鱼？请只回答鱼的名称，不需要额外的词语及标点符号"}
                            ]
                        }
                    ]
                )
                result = response.choices[0].message.content.strip()
                fish_type = result

        # 3. 查看养殖建议
        elif form_type == 'fish_suggestion':
            fish_type = request.form.get('fish_type')
            result = fish_type
            img_data = request.form.get('img_data')
            selected_species = request.form.get('selected_species')
            encoded_plot = request.form.get('plot_img')
            predictions = request.form.getlist('predictions')
            predictions = [float(p) for p in predictions] if predictions else None

            response = client.chat.completions.create(
                model="glm-4-plus",
                messages=[
                    {"role": "system", "content": "你是一个乐于回答各种问题的小助手，你的任务是提供专业、准确、有洞察力的建议。"},
                    {"role": "user", "content": f"请用一段话提供关于{fish_type}的养殖建议。"}
                ]
            )
            suggestion = response.choices[0].message.content.strip()

        # 4. 体长预测模块
        elif form_type == 'length_prediction':
            selected_species = request.form.get('species')
            img_data = request.form.get('img_data')
            result = request.form.get('result')
            fish_type = result
            suggestion = request.form.get('suggestion')
            predictions = []

            if not selected_species:
                error_msg = "请选择一个鱼类种类。"
            else:
                try:
                    connection = pymysql.connect(
                        host='localhost',
                        user='root',
                        password='123456',
                        database='visualsystem'
                    )
                    cursor = connection.cursor()
                    cursor.execute(
                        "SELECT date, length2 FROM fishes WHERE species = %s ORDER BY date ASC",
                        (selected_species,)
                    )
                    data = cursor.fetchall()
                    connection.close()

                    if not data:
                        error_msg = f"未找到 '{selected_species}' 的历史记录。"
                    else:
                        dates = [int(row[0]) for row in data]
                        lengths = [float(row[1]) for row in data]

                        # 🔮 向大模型请求预测未来3天体长
                        input_series = ", ".join([f"{v:.2f}" for v in lengths])
                        prompt = (
                            f"给定以下鱼类 {selected_species} 的历史体长数据（单位：cm）：\n"
                            f"{input_series}\n"
                            f"请根据趋势预测接下来3天的体长数值，仅返回3个数字，单位为cm，不要其他描述。"
                        )

                        response = client.chat.completions.create(
                            model="glm-4-plus",
                            messages=[
                                {"role": "user", "content": prompt}
                            ]
                        )

                        # 🧠 提取返回预测值
                        pred_text = response.choices[0].message.content.strip()
                        predictions = [float(p.strip()) for p in pred_text.replace('\n', ',').split(',') if p.strip()]

                        # 📈 绘图：历史 + 预测
                        x = np.arange(1, len(lengths) + 1)
                        y = np.array(lengths)
                        future_x = np.arange(len(lengths) + 1, len(lengths) + 1 + len(predictions))

                        plt.figure(figsize=(8, 4))
                        plt.plot(x, y, 'bo-', label='历史体长')
                        plt.plot(future_x, predictions, 'ro--', label='预测体长')
                        plt.xlabel('日期序号')
                        plt.ylabel('体长 (cm)')
                        plt.title(f'{selected_species} 的体长预测')
                        plt.legend()
                        plt.tight_layout()

                        img_io = BytesIO()
                        plt.savefig(img_io, format='png')
                        img_io.seek(0)
                        encoded_plot = base64.b64encode(img_io.read()).decode('utf-8')
                        plt.close()

                except Exception as e:
                    error_msg = f"查询或预测失败：{str(e)}"

            # 🔁 若无养殖建议则补全
            if not suggestion and result:
                response = client.chat.completions.create(
                    model="glm-4-plus",
                    messages=[
                        {"role": "system", "content": "你是一个乐于回答各种问题的小助手，你的任务是提供专业、准确、有洞察力的建议。"},
                        {"role": "user", "content": f"请用一段话提供关于{result}的养殖建议。"}
                    ]
                )
                suggestion = response.choices[0].message.content.strip()
            if selected_species and predictions:
                prediction_str = ', '.join(f"{p:.2f}" for p in predictions)
                prompt = (
                    f"我正在养殖{selected_species}，最近的体长预测为：{prediction_str} cm。\n"
                    f"请结合这一趋势，给出一些养殖建议，如是否需要调整投喂、注意生长速度或环境控制等。"
                )
                response = client.chat.completions.create(
                    model="glm-4-plus",
                    messages=[
                        {"role": "system", "content": "你是一位专业的水产养殖顾问，善于结合数据做出精准建议,只要给出一段话即可。"},
                        {"role": "user", "content": prompt}
                    ]
                )
                length_suggestion = response.choices[0].message.content.strip()
    return render_template(
        'AI_center.html',
        result=result,
        img_data=img_data,
        fish_type=fish_type,
        suggestion=suggestion or [],
        species_list=species_list,
        selected_species=selected_species,
        predictions=predictions or [],
        plot_img=encoded_plot,
        error_msg=error_msg,
        length_suggestion=length_suggestion
    )

# 智能问答
@app.route('/AI_center/ai_qa', methods=['GET'])
def ai_qa():
    return render_template('ai_qa.html')  # 渲染前端 HTML 页面

@app.route('/AI_center/ask', methods=['POST'])
def ask_question():
    data = request.get_json()
    user_question = data.get("question")

    if not user_question:
        return jsonify({"error": "问题不能为空"}), 400

    try:
        response = client.chat.completions.create(
            model="glm-4-plus",
            messages=[
                {"role": "system", "content": "你是一位乐于回答各种问题的小助手，擅长水产养殖相关知识，回答要简洁、专业、有洞察力。"},
                {"role": "user", "content": user_question}
            ]
        )
        answer = response.choices[0].message.content.strip()
        return jsonify({"answer": answer})

    except Exception as e:
        return jsonify({"error": f"生成回答失败：{str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)




