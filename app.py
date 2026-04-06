import streamlit as st
import database as db
import datetime

# ===================== 頁面設定 =====================
st.set_page_config(
    page_title="To Do",
    page_icon="✅",
    layout="wide",
    initial_sidebar_state="expanded",
)

import os

# ===================== CSS =====================
css_path = os.path.join(os.path.dirname(__file__), "style.css")
with open(css_path, "r", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# ===================== Session State 初始化 =====================
if "selected_view" not in st.session_state:
    st.session_state.selected_view = "my_day"
if "selected_list_id" not in st.session_state:
    st.session_state.selected_list_id = None
if "search_keyword" not in st.session_state:
    st.session_state.search_keyword = ""
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

# ===================== 主題切換 (CSS 注入) =====================
if st.session_state.dark_mode:
    st.markdown("""
    <style>
    .stApp {
        background-color: #1A1B26 !important;
    }
    section[data-testid="stSidebar"] {
        background-color: #16161E !important;
        border-right-color: #292E42 !important;
    }
    div[data-testid="stExpander"] {
        background-color: #24283B !important;
        border-color: #3B4261 !important;
    }
    .stApp, .stApp p, .stApp span, .stApp div, .stApp label, .stApp h1, .stApp h2, .stApp h3 {
        color: #C0CAF5 !important;
    }
    .stTextInput input, .stTextArea textarea, .stSelectbox select {
        background-color: #24283B !important;
        color: #C0CAF5 !important;
        border-color: #3B4261 !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus, .stSelectbox select:focus {
        border-color: #7AA2F7 !important;
    }
    /* Badge in dark mode */
    .badge { background: #3d59a1 !important; color: white !important; }
    .badge-muted { background: #3B4261 !important; color: #a9b1d6 !important; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
    .stApp {
        background-color: #FAFBFC !important;
    }
    section[data-testid="stSidebar"] {
        background-color: #F0F2F5 !important;
    }
    div[data-testid="stExpander"] {
        background-color: #FFFFFF !important;
    }
    .stApp {
        color: #1A1A2E !important;
    }
    /* 避免白天模式背景字體跟著 Streamlit theme 跑走 */
    p, span, div, label, h1, h2, h3 { color: inherit; }
    </style>
    """, unsafe_allow_html=True)


# ===================== Callback 函式 =====================
def _cb_add_list():
    val = st.session_state.get("new_list_input", "").strip()
    if val:
        db.add_list(val)
        st.session_state.new_list_input = ""


def _cb_add_task():
    val = st.session_state.get("new_task_input", "").strip()
    if val:
        lid = st.session_state.get("_add_target_list_id")
        if lid:
            new_id = db.add_task(lid, val)
            # 智慧清單自動標記
            v = st.session_state.selected_view
            if v == "my_day" and new_id:
                db.update_task_my_day(new_id, 1)
            elif v == "important" and new_id:
                db.update_task_importance(new_id, 1)
        st.session_state.new_task_input = ""


def _cb_add_subtask(task_id, key_prefix=""):
    key = f"{key_prefix}new_sub_{task_id}"
    val = st.session_state.get(key, "").strip()
    if val:
        db.add_subtask(task_id, val)
        st.session_state[key] = ""


def _cb_save_notes(task_id, key_prefix=""):
    key = f"{key_prefix}notes_{task_id}"
    val = st.session_state.get(key, "")
    db.update_task_notes(task_id, val)


# ===================== 輔助函式 =====================
def due_date_label(due_date_str):
    """回傳人類可讀的到期日文字。"""
    if not due_date_str:
        return ""
    try:
        due = datetime.date.fromisoformat(due_date_str)
    except ValueError:
        return ""
    delta = (due - datetime.date.today()).days
    if delta < 0:
        return f"逾期 {abs(delta)} 天"
    elif delta == 0:
        return "今天到期"
    elif delta == 1:
        return "明天到期"
    else:
        return f"{due.strftime('%m/%d')} 到期"


# ===================== Sidebar =====================
with st.sidebar:
    st.markdown("## ✅ To Do")

    # 搜尋
    search_input = st.text_input(
        "搜尋",
        value=st.session_state.search_keyword,
        placeholder="🔍 搜尋任務...",
        key="search_box",
        label_visibility="collapsed",
    )
    if search_input != st.session_state.search_keyword:
        st.session_state.search_keyword = search_input
        st.session_state.selected_view = "search"
        st.rerun()

    st.markdown("---")
    st.caption("智慧清單")

    my_day_count = db.get_my_day_count()
    if st.button(
        f"☀️  我的一天  ({my_day_count})" if my_day_count else "☀️  我的一天",
        key="nav_my_day",
        use_container_width=True,
    ):
        st.session_state.selected_view = "my_day"
        st.session_state.selected_list_id = None
        st.session_state.search_keyword = ""
        st.rerun()

    imp_count = db.get_important_count()
    if st.button(
        f"⭐  重要  ({imp_count})" if imp_count else "⭐  重要",
        key="nav_important",
        use_container_width=True,
    ):
        st.session_state.selected_view = "important"
        st.session_state.selected_list_id = None
        st.session_state.search_keyword = ""
        st.rerun()

    today_count = db.get_today_due_count()
    if st.button(
        f"📅  今日到期  ({today_count})" if today_count else "📅  今日到期",
        key="nav_today",
        use_container_width=True,
    ):
        st.session_state.selected_view = "today_due"
        st.session_state.selected_list_id = None
        st.session_state.search_keyword = ""
        st.rerun()

    all_count = db.get_all_task_count()
    if st.button(
        f"📋  所有任務  ({all_count})" if all_count else "📋  所有任務",
        key="nav_all",
        use_container_width=True,
    ):
        st.session_state.selected_view = "all"
        st.session_state.selected_list_id = None
        st.session_state.search_keyword = ""
        st.rerun()

    st.markdown("---")
    st.caption("我的清單")

    all_lists = db.get_all_lists()
    for lst in all_lists:
        icon = lst.get("icon") or "📁"
        count = db.get_task_count_by_list(lst["id"])
        label = f'{icon}  {lst["name"]}  ({count})' if count else f'{icon}  {lst["name"]}'

        if lst["is_smart"]:
            # 智慧清單不提供刪除按鈕
            if st.button(label, key=f"list_{lst['id']}", use_container_width=True):
                st.session_state.selected_view = "list"
                st.session_state.selected_list_id = lst["id"]
                st.session_state.search_keyword = ""
                st.rerun()
        else:
            col_btn, col_del = st.columns([5, 1])
            with col_btn:
                if st.button(label, key=f"list_{lst['id']}", use_container_width=True):
                    st.session_state.selected_view = "list"
                    st.session_state.selected_list_id = lst["id"]
                    st.session_state.search_keyword = ""
                    st.rerun()
            with col_del:
                if st.button("✕", key=f"del_list_{lst['id']}", help="刪除清單"):
                    db.delete_list(lst["id"])
                    if st.session_state.selected_list_id == lst["id"]:
                        st.session_state.selected_view = "my_day"
                        st.session_state.selected_list_id = None
                    st.rerun()

    # 新增清單 (使用 on_change callback 避免無限迴圈)
    st.text_input(
        "新增清單",
        key="new_list_input",
        placeholder="+ 輸入清單名稱後按 Enter",
        label_visibility="collapsed",
        on_change=_cb_add_list,
    )

    st.markdown("---")
    st.checkbox("🌙 夜間模式", key="dark_mode")


# ===================== 載入任務 =====================
view = st.session_state.selected_view
page_title = ""
tasks = []
allow_add = False
target_list_id = None

if view == "my_day":
    page_title = "☀️ 我的一天"
    tasks = db.get_my_day_tasks()
    allow_add = True
elif view == "important":
    page_title = "⭐ 重要"
    tasks = db.get_important_tasks()
    allow_add = True
elif view == "today_due":
    page_title = "📅 今日到期"
    tasks = db.get_today_due_tasks()
    allow_add = True
elif view == "all":
    page_title = "📋 所有任務"
    tasks = db.get_all_tasks()
    allow_add = True
elif view == "search":
    kw = st.session_state.search_keyword
    page_title = f'🔍 搜尋：「{kw}」'
    tasks = db.search_tasks(kw) if kw else []
    allow_add = False
elif view == "list":
    lid = st.session_state.selected_list_id
    if lid:
        list_name = db.get_list_name(lid)
        page_title = f"📁 {list_name}"
        tasks = db.get_tasks_by_list(lid)
        allow_add = True
        target_list_id = lid
    else:
        page_title = "📋 所有任務"
        tasks = db.get_all_tasks()

active_tasks = [t for t in tasks if not t["is_completed"]]
completed_tasks = [t for t in tasks if t["is_completed"]]


# ===================== 主工作區 =====================
st.markdown(f"### {page_title}")
st.caption(f"{datetime.date.today().strftime('%Y 年 %m 月 %d 日')}  ·  {len(active_tasks)} 個待辦")

# --- 新增任務區塊 ---
if allow_add:
    # 決定新增任務的目標清單
    if target_list_id:
        # 在特定清單頁面，直接加到該清單
        st.session_state._add_target_list_id = target_list_id
        st.text_input(
            "新增任務",
            key="new_task_input",
            placeholder="準備做什麼？按下 Enter 新增",
            label_visibility="collapsed",
            on_change=_cb_add_task,
        )
    else:
        # 在智慧清單頁面，需要選擇目標清單
        user_lists = db.get_all_lists()
        if user_lists:
            tc1, tc2 = st.columns([3, 1])
            with tc2:
                list_options = {lst["name"]: lst["id"] for lst in user_lists}
                chosen = st.selectbox(
                    "加入至",
                    options=list(list_options.keys()),
                    key="smart_add_target",
                    label_visibility="collapsed",
                )
                st.session_state._add_target_list_id = list_options[chosen]
            with tc1:
                st.text_input(
                    "新增任務",
                    key="new_task_input",
                    placeholder="準備做什麼？按下 Enter 新增",
                    label_visibility="collapsed",
                    on_change=_cb_add_task,
                )


# ===================== 渲染任務 =====================
def render_task(task, is_in_completed_section=False):
    """渲染單一任務卡片。"""
    star = " ⭐" if task["is_important"] else ""
    sun = " ☀️" if task.get("my_day") else ""
    due_label = due_date_label(task.get("due_date"))
    due_text = f" · {due_label}" if due_label else ""

    subtask_list = db.get_subtasks_by_task(task["id"])
    sub_done = sum(1 for s in subtask_list if s["is_completed"])
    sub_total = len(subtask_list)
    sub_text = f" · {sub_done}/{sub_total} 步驟" if sub_total > 0 else ""

    if task["is_completed"]:
        title = f'~~{task["title"]}~~{star}{due_text}{sub_text}'
    else:
        title = f'{task["title"]}{star}{sun}{due_text}{sub_text}'

    # 使用唯一 key 前綴避免巢狀 expander key 衝突
    prefix = "done_" if is_in_completed_section else ""

    with st.expander(title, expanded=False):
        # 第一列：完成 / 重要 / 我的一天
        c1, c2, c3 = st.columns(3)
        with c1:
            comp = st.checkbox(
                "完成",
                value=bool(task["is_completed"]),
                key=f"{prefix}comp_{task['id']}",
            )
            if comp != bool(task["is_completed"]):
                db.update_task_status(task["id"], int(comp))
                st.rerun()
        with c2:
            imp = st.checkbox(
                "⭐ 重要",
                value=bool(task["is_important"]),
                key=f"{prefix}imp_{task['id']}",
            )
            if imp != bool(task["is_important"]):
                db.update_task_importance(task["id"], int(imp))
                st.rerun()
        with c3:
            md = st.checkbox(
                "☀️ 我的一天",
                value=bool(task.get("my_day", 0)),
                key=f"{prefix}myday_{task['id']}",
            )
            if md != bool(task.get("my_day", 0)):
                db.update_task_my_day(task["id"], int(md))
                st.rerun()

        # 到期日 (使用 callback 避免無限迴圈)
        current_due = None
        if task.get("due_date"):
            try:
                current_due = datetime.date.fromisoformat(task["due_date"])
            except ValueError:
                pass

        due_key = f"{prefix}due_{task['id']}"

        def _cb_due_change(tid=task["id"], k=due_key):
            new_val = st.session_state.get(k)
            db.update_task_due_date(tid, new_val.isoformat() if new_val else None)

        st.date_input(
            "📅 到期日",
            value=current_due,
            key=due_key,
            format="YYYY/MM/DD",
            on_change=_cb_due_change,
        )

        # 備註 (使用 on_change callback)
        current_notes = task.get("notes", "") or ""
        st.text_area(
            "📝 備註",
            value=current_notes,
            key=f"{prefix}notes_{task['id']}",
            placeholder="新增備註...",
            height=80,
            on_change=_cb_save_notes,
            args=(task["id"], prefix),
        )

        # 子任務 (步驟)
        if subtask_list:
            st.markdown("**步驟**")
            for sub in subtask_list:
                sc1, sc2, sc3 = st.columns([1, 7, 1])
                with sc1:
                    sub_comp = st.checkbox(
                        "done",
                        value=bool(sub["is_completed"]),
                        key=f"{prefix}subcomp_{sub['id']}",
                        label_visibility="collapsed",
                    )
                    if sub_comp != bool(sub["is_completed"]):
                        db.update_subtask_status(sub["id"], int(sub_comp))
                        st.rerun()
                with sc2:
                    if sub["is_completed"]:
                        st.markdown(f"~~{sub['title']}~~")
                    else:
                        st.write(sub["title"])
                with sc3:
                    if st.button("✕", key=f"{prefix}delsub_{sub['id']}", help="刪除步驟"):
                        db.delete_subtask(sub["id"])
                        st.rerun()

        # 新增步驟 (使用 on_change callback)
        st.text_input(
            "新增步驟",
            key=f"{prefix}new_sub_{task['id']}",
            placeholder="+ 按下 Enter 新增步驟",
            label_visibility="collapsed",
            on_change=_cb_add_subtask,
            args=(task["id"], prefix),
        )

        # 底部：刪除 + 建立時間
        st.markdown("---")
        bc1, bc2 = st.columns([1, 3])
        with bc1:
            if st.button("🗑️ 刪除任務", key=f"{prefix}del_{task['id']}", use_container_width=True):
                db.delete_task(task["id"])
                st.rerun()
        with bc2:
            created = task["created_at"][:16].replace("T", " ")
            st.caption(f"建立於 {created}")


# --- 渲染未完成任務 ---
if not active_tasks and not completed_tasks:
    st.markdown(
        '<div style="text-align:center; padding:3rem 0; color:#9CA3AF;">'
        "<p style='font-size:1.2rem;'>目前沒有任務</p>"
        "<p>使用上方輸入框新增第一個任務</p>"
        "</div>",
        unsafe_allow_html=True,
    )

for t in active_tasks:
    render_task(t)

# --- 已完成任務 ---
if completed_tasks:
    st.markdown("---")
    st.markdown(f"**已完成 ({len(completed_tasks)})**")
    show_completed = st.checkbox("顯示已完成任務", value=False, key="toggle_completed")
    if show_completed:
        for t in completed_tasks:
            render_task(t, is_in_completed_section=True)
