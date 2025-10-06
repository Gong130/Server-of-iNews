from flask import Flask, request, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
from sqlalchemy import func

app = Flask(__name__)

# 配置数据库，替换成你的连接字符串
app.config['SQLALCHEMY_DATABASE_URI'] = (
    'mssql+pyodbc://sa:123456@localhost/inews_db?driver=ODBC+Driver+17+for+SQL+Server'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# JWT配置
app.config['JWT_SECRET_KEY'] = 'your_super_secret_jwt_key'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

db = SQLAlchemy(app)
jwt = JWTManager(app)

# 用户模型，password_hash长度足够大，避免截断
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)  # 加大长度
    role = db.Column(db.String(20), default='user')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class News(db.Model):
    __tablename__ = 'news'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=True)
    author = db.Column(db.String(80), nullable=False, default='系统')
    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())

# 初始化数据库并种子数据（首次运行）
with app.app_context():
    db.create_all()
    # 如果新闻表为空，插入几条示例新闻
    if db.session.query(News).count() == 0:
        demo_rows = [
            News(title='今日头条：iNews 系统已上线', content='欢迎使用 iNews，体验简洁的新闻系统。', author='系统'),
            News(title='技术快讯：Flask JWT 登录打通', content='后端已支持基于 JWT 的安全登录与鉴权。', author='后端'),
            News(title='产品更新：新闻数据接入数据库', content='新闻列表现在从数据库读取，支持更稳定的展示。', author='产品')
        ]
        db.session.add_all(demo_rows)
        db.session.commit()

# 登录注册页面（前端）
login_page_html = """
<!DOCTYPE html>
<html lang="zh">
<head><meta charset="UTF-8" /><title>登录 / 注册</title></head>
<body>
<h1>登录 / 注册</h1>
<form id="authForm">
  <label>用户名：<input type="text" id="username" required></label><br>
  <label>密码：<input type="password" id="password" required></label><br>
  <button type="button" id="loginBtn">登录</button>
  <button type="button" id="registerBtn">注册</button>
</form>
<h2>结果：</h2>
<pre id="result"></pre>
<script>
const resultEl = document.getElementById('result');

async function sendRequest(url) {
  const username = document.getElementById('username').value.trim();
  const password = document.getElementById('password').value.trim();
  if (!username || !password) {
    resultEl.textContent = '用户名和密码不能为空';
    return;
  }
  const res = await fetch(url, {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({username, password})
  });
  const data = await res.json();
  if (url.endsWith('/login') && res.ok) {
    // 登录成功，保存 token
    localStorage.setItem('access_token', data.access_token);
    // 跳转到新闻页
    window.location.href = '/news.html';
  } else {
    resultEl.textContent = JSON.stringify(data, null, 2);
  }
}

document.getElementById('loginBtn').addEventListener('click', () => sendRequest('/api/auth/login'));
document.getElementById('registerBtn').addEventListener('click', () => sendRequest('/api/auth/register'));
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(login_page_html)

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    if not username or not password:
        return jsonify({"msg": "用户名和密码不能为空"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"msg": "用户名已存在"}), 400
    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    try:
        db.session.commit()
        print(f"注册成功，用户：{username}")
        return jsonify({"msg": "注册成功"}), 201
    except Exception as e:
        print(f"数据库提交错误: {e}")
        db.session.rollback()
        return jsonify({"msg": "注册失败，数据库错误"}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    if not username or not password:
        return jsonify({"msg": "用户名和密码不能为空"}), 400
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"msg": "用户名或密码错误"}), 401
    if not user.check_password(password):
        return jsonify({"msg": "用户名或密码错误"}), 401
    # 使用字符串身份，避免 PyJWT 对 sub 的限制；角色放到附加声明
    access_token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    print(f"用户登录成功：{username}")
    return jsonify(access_token=access_token)

# 获取新闻列表（受保护接口）
@app.route('/api/news', methods=['GET'])
@jwt_required()
def get_news():
    _current_user_id = get_jwt_identity()
    rows = (
        db.session.query(News)
        .order_by(News.created_at.desc(), News.id.desc())
        .limit(50)
        .all()
    )
    return jsonify([
        {
            "id": r.id,
            "title": r.title,
            "author": r.author,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "content": r.content,
        }
        for r in rows
    ])

# 允许访问 /news.html 静态文件
@app.route('/news.html')
def news_page():
    return app.send_static_file('new.html')

if __name__ == '__main__':
    app.run(debug=True)

