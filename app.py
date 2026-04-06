import streamlit as st
import database as db

st.set_page_config(page_title="Microsoft To Do Clone", layout="wide", initial_sidebar_state="expanded")

# --- CSS 隱藏預設 Streamlit 樣式與美化 ---
st.markdown("""
<style>
/* 隱藏主菜單與頁尾 */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
/* 清單按鈕美化 */
div.stButton > button:first-child {
    text-align: left;
    border: none;
    box-shadow: none;
    background-color: transparent;
}
div.stButton > button:hover {
    background-color: #f0f2f6;
    border: none;
}
</style>
""", unsafe_allow_html=True)

# --- 初始化 Session State ---
if "lists" not in st.session_state:
    st.session_state.lists = db.get_all_lists()

if "selected_list" not in st.session_state:
    # 預設選擇第一個清單
    st.session_state.selected_list = {"id": -1, "name": "重要", "is_smart": True, "type": "smart_important"}

# --- 事件處理函式 (Callbacks) ---
def handle_add_list():
    new_list = st.session_state.new_list_name
    if new_list and new_list.strip() != "":
        db.add_list(new_list.strip())
        st.session_state.new_list_name = ""

def handle_add_task(list_id):
    new_task = st.session_state.new_task_input
    if new_task and new_task.strip() != "":
        db.add_task(list_id, new_task.strip())
        st.session_state.new_task_input = ""

def handle_add_subtask(task_id):
    subtask_title = st.session_state[f"new_subtask_{task_id}"]
    if subtask_title and subtask_title.strip() != "":
        db.add_subtask(task_id, subtask_title.strip())
        st.session_state[f"new_subtask_{task_id}"] = ""

# --- 側邊欄 (Sidebar) ---
with st.sidebar:
    st.title("📋 我的待辦")
    
    st.subheader("智慧清單")
    if st.button("⭐ 重要", use_container_width=True):
        st.session_state.selected_list = {"id": -1, "name": "重要", "is_smart": True, "type": "smart_important"}
        
    st.subheader("我的清單")
    all_lists = db.get_all_lists()
    for lst in all_lists:
        # 圖示判斷
        icon = "🏠" if lst['is_smart'] else "📁"
        btn_label = f"{icon} {lst['name']}"
        if st.button(btn_label, key=f"list_{lst['id']}", use_container_width=True):
            st.session_state.selected_list = lst
            
    st.write("---")
    st.text_input("+ 新增清單", key="new_list_name", on_change=handle_add_list, placeholder="輸入清單名稱後按 Enter")


# --- 主工作區 (Main Area) ---
selected_list = st.session_state.selected_list
st.header(selected_list["name"])

# 載入當前任務
tasks = []
if selected_list.get("type") == "smart_important":
    tasks = db.get_important_tasks()
else:
    tasks = db.get_tasks_by_list(selected_list["id"])

# 顯示新增任務區塊
if selected_list.get("type") == "smart_important":
    st.info("提示：請在「我的清單」中新增任務，並標記為重要，即可顯示於此。")
else:
    st.text_input("新增任務...", key="new_task_input", on_change=handle_add_task, args=(selected_list["id"],), placeholder="準備做什麼？按下 Enter 新增")

st.write("---")

# 顯示任務列表 (使用 st.expander 作為詳細資料展開)
if not tasks:
    st.write("目前沒有任務 🎉")

for task in tasks:
    prefix = "✅" if task["is_completed"] else "⬜"
    suffix = "⭐" if task["is_important"] else ""
    title_display = f"~~{task['title']}~~" if task["is_completed"] else task['title']
    
    expander_title = f"{prefix} {title_display} {suffix}"
    
    with st.expander(expander_title):
        col1, col2, col3, col4 = st.columns([1, 1, 2, 1])
        
        with col1:
            comp_val = st.checkbox("已完成", value=bool(task['is_completed']), key=f"comp_{task['id']}")
            if comp_val != bool(task['is_completed']):
                db.update_task_status(task['id'], int(comp_val))
                st.rerun()
                
        with col2:
            imp_val = st.checkbox("標示為重要", value=bool(task['is_important']), key=f"imp_{task['id']}")
            if imp_val != bool(task['is_important']):
                db.update_task_importance(task['id'], int(imp_val))
                st.rerun()
                
        with col3:
            st.caption(f"建立時間: {task['created_at'][:16].replace('T', ' ')}")
            
        with col4:
            if st.button("🗑️ 刪除", key=f"del_task_{task['id']}", use_container_width=True):
                db.delete_task(task['id'])
                st.rerun()
                
        st.divider()
        
        # 顯示子任務 (Steps)
        st.markdown("**步驟 (Subtasks)**")
        subtasks = db.get_subtasks_by_task(task['id'])
        for sub in subtasks:
            sc1, sc2, sc3 = st.columns([1, 6, 1])
            with sc1:
                sub_comp = st.checkbox(" ", value=bool(sub['is_completed']), key=f"subcomp_{sub['id']}")
                if sub_comp != bool(sub['is_completed']):
                    db.update_subtask_status(sub['id'], int(sub_comp))
                    st.rerun()
            with sc2:
                # 若完成則加上刪除線
                if sub['is_completed']:
                    st.write(f"~~{sub['title']}~~")
                else:
                    st.write(sub['title'])
            with sc3:
                if st.button("❌", key=f"delsub_{sub['id']}", help="刪除步驟"):
                    db.delete_subtask(sub['id'])
                    st.rerun()
                    
        # 新增子任務
        st.text_input("下一步？", key=f"new_subtask_{task['id']}", on_change=handle_add_subtask, args=(task['id'],), placeholder="按下 Enter 新增步驟")
