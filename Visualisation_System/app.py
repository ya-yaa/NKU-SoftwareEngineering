from flask import Flask, render_template, request, redirect, url_for, session, flash
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'my_secret_key'  # 用于 session 加密

# 数据库连接配置
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Root12345!',
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
        return f"欢迎您，{session['username']}！角色：{session['role']} <br><a href='/logout'>退出登录</a>"
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
    # if session.get('role') != 0:  
    #     flash("您无权访问此页面。")
    #     return redirect(url_for('home'))

    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username,  role, action_type, timestamp FROM action_logs ORDER BY timestamp DESC")
    logs = cursor.fetchall()
    conn.close()
    return render_template('admin_logs.html', logs=logs)

# 管理员查看所有用户
@app.route('/admin/users')
def admin_users():
    # if session.get('role') != 0:  
    #     flash("您无权访问此页面。")
    #     return redirect(url_for('home'))

    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role, phone FROM users")
    users = cursor.fetchall()
    conn.close()
    return render_template('admin_users.html', users=users)


# 修改用户信息
@app.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    # if session.get('role') != 0:
    #     flash("无权限")
    #     return redirect(url_for('home'))

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
    # if session.get('role') != 0:
    #     flash("无权限")
    #     return redirect(url_for('home'))

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
    # if session.get('role') != 0:
    #     flash("无权限")
    #     return redirect(url_for('home'))

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


if __name__ == '__main__':
    app.run(debug=True)
