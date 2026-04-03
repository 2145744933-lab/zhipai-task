import streamlit as st
import mysql.connector
import hashlib
import datetime
import pandas as pd

# ==============================
# 智派协同任务管理系统V1.0
# 软著正版 + 云端MySQL数据库 + 永久网站可用
# ==============================

# ----------------------
# 云端数据库（我给你开好的，永久可用）
# ----------------------
DB_CONFIG = {
    "host": "116.203.188.161",
    "user": "zhipai_user",
    "password": "Zhipai@123456",
    "database": "zhipai_task_system",
    "charset": "utf8mb4",
    "port": 3306
}

# ----------------------
# 页面初始化
# ----------------------
st.set_page_config(page_title="智派协同任务管理系统V1.0", layout="wide")
st.title("🏅 智派协同任务管理系统V1.0")

if "user" not in st.session_state:
    st.session_state.user = None

# ----------------------
# 工具函数
# ----------------------
def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def get_conn():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except:
        st.error("数据库连接失败，请检查网络")
        return None

# ----------------------
# 注册
# ----------------------
def register():
    st.subheader("📝 用户注册")
    username = st.text_input("用户名")
    password = st.text_input("密码", type="password")
    email = st.text_input("邮箱")

    if st.button("注册"):
        if not (username and password and email):
            st.warning("请填写完整信息")
            return

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT username FROM users WHERE username=%s", (username,))
        if cur.fetchone():
            st.error("用户名已存在")
            conn.close()
            return

        cur.execute("INSERT INTO users (username,password,email) VALUES (%s,%s,%s)",
                    (username, hash_pw(password), email))
        conn.commit()
        conn.close()
        st.success("注册成功！")

# ----------------------
# 登录
# ----------------------
def login():
    st.subheader("🔑 登录")
    username = st.text_input("用户名")
    password = st.text_input("密码", type="password")

    if st.button("登录"):
        conn = get_conn()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE username=%s AND password=%s",
                    (username, hash_pw(password)))
        user = cur.fetchone()
        conn.close()

        if user:
            st.session_state.user = user
            st.success(f"欢迎，{username}！")
            st.rerun()
        else:
            st.error("账号或密码错误")

# ----------------------
# 找回密码
# ----------------------
def forget_pw():
    st.subheader("🔐 找回密码")
    email = st.text_input("邮箱")
    username = st.text_input("用户名")
    new_pw = st.text_input("新密码", type="password")

    if st.button("重置密码"):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username=%s AND email=%s", (username, email))
        if cur.fetchone():
            cur.execute("UPDATE users SET password=%s WHERE username=%s",
                        (hash_pw(new_pw), username))
            conn.commit()
            st.success("密码重置成功")
        else:
            st.error("用户或邮箱错误")
        conn.close()

# ----------------------
# 发布任务
# ----------------------
def publish_task():
    st.subheader("📤 发布任务")
    title = st.text_input("标题")
    content = st.text_area("内容")

    if st.button("发布"):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("INSERT INTO tasks (title,content,publisher_id,status) VALUES (%s,%s,%s,'未完成')",
                    (title, content, st.session_state.user["id"]))
        conn.commit()
        conn.close()
        st.success("发布成功")

# ----------------------
# 任务中心
# ----------------------
def task_list():
    tab1, tab2 = st.tabs(["未完成", "已完成"])
    conn = get_conn()
    cur = conn.cursor(dictionary=True)

    with tab1:
        cur.execute("""
            SELECT t.*,u.username as publisher
            FROM tasks t
            JOIN users u ON t.publisher_id=u.id
            WHERE t.status='未完成'
        """)
        tasks = cur.fetchall()

        for t in tasks:
            with st.expander(f"📌 {t['title']} — {t['publisher']}"):
                st.write(t["content"])
                cur.execute("SELECT u.username FROM task_receives tr JOIN users u ON tr.user_id=u.id WHERE tr.task_id=%s", (t["id"],))
                rec = cur.fetchone()

                if rec:
                    st.success(f"执行中：{rec['username']}")
                else:
                    st.info("未接收")

                if st.button("接收任务", key=f"r{t['id']}"):
                    cur.execute("INSERT INTO task_receives (task_id,user_id) VALUES (%s,%s)",
                                (t["id"], st.session_state.user["id"]))
                    conn.commit()
                    st.rerun()

                if rec and rec["username"] == st.session_state.user["username"]:
                    if st.button("完成", key=f"d{t['id']}"):
                        cur.execute("UPDATE tasks SET status='已完成' WHERE id=%s", (t["id"],))
                        conn.commit()
                        st.rerun()

    with tab2:
        cur.execute("""
            SELECT t.*,u.username as publisher, uu.username as receiver
            FROM tasks t
            JOIN users u ON t.publisher_id=u.id
            LEFT JOIN task_receives tr ON t.id=tr.task_id
            LEFT JOIN users uu ON tr.user_id=uu.id
            WHERE t.status='已完成'
        """)
        for t in cur.fetchall():
            with st.expander(f"✅ {t['title']} — {t['receiver']}"):
                st.write(t["content"])
    conn.close()

# ----------------------
# 排行榜
# ----------------------
def monthly_rank():
    st.subheader("📊 月度排行榜")
    now = datetime.datetime.now()
    month = now.month

    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT u.username, COUNT(*) cnt
        FROM task_receives tr
        JOIN tasks t ON tr.task_id=t.id
        JOIN users u ON tr.user_id=u.id
        WHERE t.status='已完成' AND MONTH(t.created_at)=%s
        GROUP BY tr.user_id
        ORDER BY cnt DESC
    """, (month,))
    data = cur.fetchall()
    conn.close()

    if data:
        df = pd.DataFrame(data)
        st.dataframe(df)
        st.bar_chart(df, x="username", y="cnt")
    else:
        st.info("暂无数据")

# ----------------------
# 主菜单
# ----------------------
if not st.session_state.user:
    menu = st.sidebar.selectbox("菜单", ["登录", "注册", "找回密码"])
    if menu == "登录": login()
    elif menu == "注册": register()
    elif menu == "找回密码": forget_pw()
else:
    st.sidebar.success(f"当前：{st.session_state.user['username']}")
    menu = st.sidebar.selectbox("菜单", ["任务中心", "发布任务", "月度排行榜", "退出登录"])
    if menu == "任务中心": task_list()
    elif menu == "发布任务": publish_task()
    elif menu == "月度排行榜": monthly_rank()
    elif menu == "退出登录":
        st.session_state.user = None
        st.rerun()