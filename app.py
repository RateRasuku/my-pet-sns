import streamlit as st
import streamlit_authenticator as stauth
import os
import datetime
import pandas as pd

# ページの設定：レイアウトを 'wide' にすると画面を広く使えます
st.set_page_config(page_title="ペットSNS - タイル表示版", layout="wide")

# --- 1. 認証設定 ---
credentials = {
    "usernames": {
        "taki": {"name": "Taki User", "password": "123"},
        "guest": {"name": "Guest User", "password": "456"}
    }
}
authenticator = stauth.Authenticate(credentials, "pet_app_cookie", "auth_key")
authenticator.login(location='main')

if st.session_state["authentication_status"]:
    # サイドバーにログアウトとユーザー名を表示
    with st.sidebar:
        st.write(f"ログイン中: **{st.session_state['name']}**")
        authenticator.logout('ログアウト')
    
    # --- 2. データの準備 ---
    SAVE_DIR = "saved_photos"
    DB_FILE = "photo_data.csv"

    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)
    
    if not os.path.exists(DB_FILE):
        df = pd.DataFrame(columns=["filename", "contributor", "likes"])
        df.to_csv(DB_FILE, index=False, encoding="utf-8")

    st.title('🐶 ペット写真ギャラリー')

    # --- 3. 投稿セクション（中央に配置） ---
    col_left, col_mid, col_right = st.columns([1, 2, 1])
    with col_mid:
        with st.expander("✨ ここをクリックして写真を投稿する"):
            uploaded_file = st.file_uploader("写真を選択", type=["jpg", "png", "jpeg"])
            if uploaded_file:
                st.image(uploaded_file, use_container_width=True)
                if st.button("🚀 投稿する", use_container_width=True):
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    file_name = f"{timestamp}_{uploaded_file.name}"
                    file_path = os.path.join(SAVE_DIR, file_name)
                    
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    new_data = pd.DataFrame([[file_name, st.session_state["name"], 0]], 
                                          columns=["filename", "contributor", "likes"])
                    df = pd.read_csv(DB_FILE)
                    df = pd.concat([df, new_data], ignore_index=True)
                    df.to_csv(DB_FILE, index=False, encoding="utf-8")
                    
                    st.success("投稿完了！")
                    st.rerun()

    st.divider()

    # --- 4. タイル状の一覧表示 ---
    df = pd.read_csv(DB_FILE)

    if df.empty:
        st.center().write("まだ投稿がありません。")
    else:
        # 投稿を新しい順（逆順）にする
        df_display = df.iloc[::-1]
        
        # 3列のグリッドを作成
        cols = st.columns(3)
        
        for index, (idx, row) in enumerate(df_display.iterrows()):
            # 順番に列（0, 1, 2）を割り振る
            with cols[index % 3]:
                with st.container(border=True):
                    img_path = os.path.join(SAVE_DIR, row['filename'])
                    if os.path.exists(img_path):
                        st.image(img_path, use_container_width=True)
                    
                    st.caption(f"👤 {row['contributor']}")
                    
                    # ボタンのデザインを少しスッキリさせる
                    if st.button(f"❤️ {row['likes']}", key=f"tile_{row['filename']}", use_container_width=True):
                        df.at[idx, 'likes'] += 1
                        df.to_csv(DB_FILE, index=False, encoding="utf-8")
                        st.rerun()

elif st.session_state["authentication_status"] is False:
    st.error('ログインに失敗しました')