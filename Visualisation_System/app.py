from flask import Flask, render_template, request, redirect, url_for, session, flash
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import requests
import csv
import os
app = Flask(__name__)
app.secret_key = 'my_secret_key'  # 用于 session 加密

# 数据库连接配置
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'yuxin173',
    'database': 'visualsystem',
    'charset': 'utf8mb4'
}

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

            flash("登录成功。")
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
            # 标准逻辑（简化处理）
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


# 智能中心
@app.route('/AI_center')
def AI_center():
    if 'username' not in session:
        flash("请先登录。")
        return redirect(url_for('login'))
    return render_template('AI_center.html')

# 图片识别
@app.route('/AI_center/image_recognition')
def image_recognition():
    return "<h2>图片识别模块（待实现）</h2>"

# 鱼类体长预测
@app.route('/AI_center/fish_length_prediction')
def fish_length_prediction():
    return "<h2>鱼类体长预测模块（待实现）</h2>"

# 智能问答
@app.route('/AI_center/ai_qa')
def ai_qa():
    return "<h2>智能问答模块（待实现）</h2>"

if __name__ == '__main__':
    app.run(debug=True)




