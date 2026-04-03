import streamlit as st
import mysql.connector
import hashlib
import datetime
import pandas as pd

# ==============================
# 软著版本 · 智派协同任务管理系统 V1.0
# 功能：注册、登录、用户名防重复、邮箱找回密码、发任务、接任务、评论、完成状态、月度排行榜、公网访问
# ==============================

# ----------------------
# 数据库配置（软著标准）
# ----------------------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "zhipai_task_system",
    "charset": "utf8mb4"
}

# ----------------------
# 页面初始化
# ----------------------
st.set_page_config(page_title="智派协同任务管理系统 V1.0", layout="wide")
st.title("🏅 智派协同任务管理系统 V1.0")

# 登录状态保持
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
        st.error("数据库连接失败，请检查服务是否启动")
        return None

# ----------------------
# 1. 用户注册（用户名不重复）
# ----------------------
def register():
    st.subheader("用户注册")
    username = st.text_input("用户名")
    password = st.text_input("密码", type="password")
    email = st.text_input("邮箱（用于找回密码）")

    if st.button("注册"):
        if not (username and password and email):
            st.warning("请填写完整信息")
            return

        conn = get_conn()
        if not conn: return
        cur = conn.cursor()

        cur.execute("SELECT username FROM users WHERE username=%s", (username,))
        if cur.fetchone():
            st.error("用户名已存在！")
            conn.close()
            return

        cur.execute("INSERT INTO users (username, password, email) VALUES (%s,%s,%s)",
                    (username, hash_pw(password), email))
        conn.commit()
        conn.close()
        st.success("注册成功！")

# ----------------------
# 2. 登录
# ----------------------
def login():
    st.subheader("用户登录")
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
            st.rerun()
        else:
            st.error("账号或密码错误")

# ----------------------
# 3. 邮箱找回密码
# ----------------------
def forget_pw():
    st.subheader("找回密码")
    email = st.text_input("请输入注册邮箱")
    username = st.text_input("请输入用户名")
    new_pw = st.text_input("新密码", type="password")
    if st.button("重置密码"):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username=%s AND email=%s", (username, email))
        if cur.fetchone():
            cur.execute("UPDATE users SET password=%s WHERE username=%s", (hash_pw(new_pw), username))
            conn.commit()
            st.success("密码重置成功！")
        else:
            st.error("用户或邮箱不正确")
        conn.close()

# ----------------------
# 4. 发布任务
# ----------------------
def publish_task():
    st.subheader("发布任务")
    title = st.text_input("任务标题")
    content = st.text_area("任务内容")
    if st.button("发布"):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("INSERT INTO tasks (title, content, publisher_id, status) VALUES (%s,%s,%s,'未完成')",
                    (title, content, st.session_state.user["id"]))
        conn.commit()
        conn.close()
        st.success("发布成功")

# ----------------------
# 5. 任务列表（未完成 / 已完成）
# ----------------------
def task_list():
    tab1, tab2 = st.tabs(["未完成任务", "已完成任务"])
    conn = get_conn()
    cur = conn.cursor(dictionary=True)

    with tab1:
        st.subheader("未完成任务")
        cur.execute("""
            SELECT t.*, u.username as publisher
            FROM tasks t
            JOIN users u ON t.publisher_id = u.id
            WHERE t.status='未完成'
            ORDER BY t.created_at DESC
        """)
        tasks = cur.fetchall()
        for t in tasks:
            with st.expander(f"📌 {t['title']} —— 发布人：{t['publisher']}"):
                st.write(f"内容：{t['content']}")
                st.write(f"发布时间：{t['created_at']}")

                # 显示接收人
                cur.execute("SELECT username FROM users WHERE id=(SELECT user_id FROM task_receives WHERE task_id=%s)", (t["id"],))
                rec = cur.fetchone()
                if rec:
                    st.success(f"✅ 正在执行：{rec['username']}")
                else:
                    st.info("📌 状态：未接收")

                # 接收任务
                if st.button("接收任务", key=f"recv{t['id']}"):
                    cur.execute("INSERT INTO task_receives (task_id,user_id) VALUES (%s,%s) ON DUPLICATE KEY UPDATE user_id=user_id",
                                (t["id"], st.session_state.user["id"]))
                    conn.commit()
                    st.rerun()

                # 标记完成
                if rec and rec["username"] == st.session_state.user["username"]:
                    if st.button("标记已完成", key=f"done{t['id']}"):
                        cur.execute("UPDATE tasks SET status='已完成' WHERE id=%s", (t["id"],))
                        conn.commit()
                        st.rerun()

                # 评论
                st.markdown("---")
                st.write("💬 评论")
                cur.execute("SELECT c.*,u.username FROM comments c JOIN users u ON c.user_id=u.id WHERE task_id=%s ORDER BY c.created_at", (t["id"],))
                for c in cur.fetchall():
                    st.write(f"**{c['username']}**：{c['content']}")
                msg = st.text_input("发表评论", key=f"c{t['id']}")
                if st.button("发送", key=f"send{t['id']}"):
                    cur.execute("INSERT INTO comments (task_id,user_id,content) VALUES (%s,%s,%s)",
                                (t["id"], st.session_state.user["id"], msg))
                    conn.commit()
                    st.rerun()

    with tab2:
        st.subheader("已完成任务")
        cur.execute("""
            SELECT t.*, u.username as publisher, uu.username as receiver
            FROM tasks t
            JOIN users u ON t.publisher_id = u.id
            LEFT JOIN task_receives tr ON t.id=tr.task_id
            LEFT JOIN users uu ON tr.user_id=uu.id
            WHERE t.status='已完成'
            ORDER BY t.created_at DESC
        """)
        for t in cur.fetchall():
            with st.expander(f"✅ {t['title']} —— 完成人：{t['receiver']}"):
                st.write(t["content"])

    conn.close()

# ----------------------
# 6. 月度任务排行榜
# ----------------------
def monthly_rank():
    st.subheader("📊 本月任务完成排行榜")
    now = datetime.datetime.now()
    month = now.month
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT u.username, COUNT(*) as cnt
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
        st.dataframe(df, use_container_width=True)
        st.bar_chart(df, x="username", y="cnt")
    else:
        st.info("本月暂无完成任务")

# ----------------------
# 主菜单（软著标准界面）
# ----------------------
if not st.session_state.user:
    menu = st.sidebar.selectbox("菜单", ["登录", "注册", "找回密码"])
    if menu == "登录":
        login()
    elif menu == "注册":
        register()
    elif menu == "找回密码":
        forget_pw()
else:
    st.sidebar.success(f"欢迎，{st.session_state.user['username']}")
    menu = st.sidebar.selectbox("菜单", [
        "任务中心", "发布任务", "月度排行榜", "退出登录"
    ])
    if menu == "任务中心":
        task_list()
    elif menu == "发布任务":
        publish_task()
    elif menu == "月度排行榜":
        monthly_rank()
    elif menu == "退出登录":
        st.session_state.user = None
        st.rerun()