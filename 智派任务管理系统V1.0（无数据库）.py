import streamlit as st
import hashlib
import datetime
import pandas as pd

# ==============================
# 智派协同任务管理系统 — 在线可分享版（无数据库）
# ==============================

st.set_page_config(page_title="智派协同任务管理系统", layout="wide")
st.title("🏅 智派协同任务管理系统 V1.0")

# 内存存储（部署在线后可永久使用）
if "users" not in st.session_state:
    st.session_state.users = [{"id": 1, "username": "admin", "password": hashlib.sha256("admin".encode()).hexdigest(), "email": "admin@test.com"}]

if "tasks" not in st.session_state:
    st.session_state.tasks = []

if "task_receives" not in st.session_state:
    st.session_state.task_receives = []

if "user" not in st.session_state:
    st.session_state.user = None

# ----------------------
# 功能：登录
# ----------------------
def login():
    st.subheader("🔑 登录")
    username = st.text_input("用户名")
    password = st.text_input("密码", type="password")
    if st.button("登录"):
        pw_hash = hashlib.sha256(password.encode()).hexdigest()
        for u in st.session_state.users:
            if u["username"] == username and u["password"] == pw_hash:
                st.session_state.user = u
                st.success("登录成功！")
                st.rerun()
                return
        st.error("账号或密码错误")

# ----------------------
# 功能：注册
# ----------------------
def register():
    st.subheader("📝 注册")
    username = st.text_input("用户名")
    password = st.text_input("密码", type="password")
    email = st.text_input("邮箱")
    if st.button("注册"):
        if not username or not password or not email:
            st.warning("请填写完整")
            return
        for u in st.session_state.users:
            if u["username"] == username:
                st.error("用户名已存在")
                return
        new_id = len(st.session_state.users) + 1
        st.session_state.users.append({
            "id": new_id,
            "username": username,
            "password": hashlib.sha256(password.encode()).hexdigest(),
            "email": email
        })
        st.success("注册成功！")

# ----------------------
# 功能：发布任务
# ----------------------
def publish_task():
    st.subheader("📤 发布任务")
    title = st.text_input("标题")
    content = st.text_area("内容")
    if st.button("发布"):
        if title and content:
            new_task = {
                "id": len(st.session_state.tasks) + 1,
                "title": title,
                "content": content,
                "publisher_id": st.session_state.user["id"],
                "publisher_name": st.session_state.user["username"],
                "status": "未完成",
                "created_at": datetime.datetime.now().strftime("%m-%d %H:%M")
            }
            st.session_state.tasks.append(new_task)
            st.success("发布成功")
        else:
            st.warning("标题和内容不能为空")

# ----------------------
# 功能：任务中心
# ----------------------
def task_list():
    tab1, tab2 = st.tabs(["未完成", "已完成"])
    with tab1:
        for t in st.session_state.tasks:
            if t["status"] == "未完成":
                with st.expander(f"📌 {t['title']}（发布者：{t['publisher_name']}）"):
                    st.write(t["content"])
                    received = [r for r in st.session_state.task_receives if r["task_id"] == t["id"]]
                    if received:
                        st.success(f"✅ 已接收：{received[0]['username']}")
                    else:
                        st.info("⌛ 未接收")
                        if st.button(f"接收任务", key=f"r{t['id']}"):
                            st.session_state.task_receives.append({
                                "task_id": t["id"],
                                "user_id": st.session_state.user["id"],
                                "username": st.session_state.user["username"]
                            })
                            st.rerun()
                    if received and received[0]["user_id"] == st.session_state.user["id"]:
                        if st.button("✅ 标记完成", key=f"d{t['id']}"):
                            t["status"] = "已完成"
                            st.rerun()
    with tab2:
        for t in st.session_state.tasks:
            if t["status"] == "已完成":
                receiver = next((r["username"] for r in st.session_state.task_receives if r["task_id"] == t["id"]), "无")
                with st.expander(f"✅ {t['title']}（执行者：{receiver}）"):
                    st.write(t["content"])

# ----------------------
# 排行榜
# ----------------------
def monthly_rank():
    st.subheader("📊 月度排行榜")
    count = {}
    for r in st.session_state.task_receives:
        task = next((t for t in st.session_state.tasks if t["id"] == r["task_id"]), None)
        if task and task["status"] == "已完成":
            name = r["username"]
            count[name] = count.get(name, 0) + 1
    if count:
        df = pd.DataFrame(list(count.items()), columns=["用户名", "完成任务数"])
        st.dataframe(df)
        st.bar_chart(df, x="用户名", y="完成任务数")
    else:
        st.info("暂无数据")

# ----------------------
# 菜单
# ----------------------
if not st.session_state.user:
    menu = st.sidebar.selectbox("菜单", ["登录", "注册"])
    login() if menu == "登录" else register()
else:
    st.sidebar.success(f"欢迎：{st.session_state.user['username']}")
    menu = st.sidebar.selectbox("菜单", ["任务中心", "发布任务", "月度排行榜", "退出登录"])
    if menu == "任务中心": task_list()
    elif menu == "发布任务": publish_task()
    elif menu == "月度排行榜": monthly_rank()
    elif menu == "退出登录":
        st.session_state.user = None
        st.rerun()