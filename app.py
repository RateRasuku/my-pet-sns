import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import cloudinary
import cloudinary.uploader
import os

# --- 1. Cloudinaryの設定 (Secretsから読み込み) ---
cloudinary.config(
    cloud_name = st.secrets["CLOUDINARY_CLOUD_NAME"],
    api_key = st.secrets["CLOUDINARY_API_KEY"],
    api_secret = st.secrets["CLOUDINARY_API_SECRET"],
    secure = True
)

st.set_page_config(page_title="ペットSNS - 永久保存版", layout="wide")

# --- 2. 認証設定 ---
credentials = {
    "usernames": {
        "taki": {"name": "Taki User", "password": "123"},
        "guest": {"name": "Guest User", "password": "456"}
    }
}
authenticator = stauth.Authenticate(credentials, "pet_app_cookie", "auth_key")
authenticator.login(location='main')

if st.session_state["authentication_status"]:
    with st.sidebar:
        st.write(f"ログイン中: **{st.session_state['name']}**")
        authenticator.logout('ログアウト')
    
    DB_FILE = "photo_data.csv"
    if not os.path.exists(DB_FILE):
        df = pd.DataFrame(columns=["url", "public_id", "contributor", "likes"])
        df.to_csv(DB_FILE, index=False, encoding="utf-8")

    st.title('🐶 ペット写真ギャラリー (Cloud版)')

    # --- 3. 投稿セクション ---
    with st.expander("✨ 写真を投稿する"):
        uploaded_file = st.file_uploader("写真を選択", type=["jpg", "png", "jpeg"])
        if uploaded_file:
            st.image(uploaded_file, use_container_width=True)
            if st.button("🚀 クラウドに保存して投稿", use_container_width=True):
                # Cloudinaryにアップロード
                upload_result = cloudinary.uploader.upload(uploaded_file)
                
                # 画像のURLと、削除に必要なID（public_id）を取得
                img_url = upload_result["secure_url"]
                img_id = upload_result["public_id"]
                
                # CSVに記録
                new_data = pd.DataFrame([[img_url, img_id, st.session_state["name"], 0]], 
                                      columns=["url", "public_id", "contributor", "likes"])
                df = pd.read_csv(DB_FILE)
                df = pd.concat([df, new_data], ignore_index=True)
                df.to_csv(DB_FILE, index=False, encoding="utf-8")
                
                st.success("クラウドに保存しました！")
                st.rerun()

    st.divider()

    # --- 4. 一覧表示 & 削除機能 ---
    df = pd.read_csv(DB_FILE)
    if not df.empty:
        df_display = df.iloc[::-1]
        cols = st.columns(3)
        for index, (idx, row) in enumerate(df_display.iterrows()):
            with cols[index % 3]:
                with st.container(border=True):
                    # CloudinaryのURLから画像を表示
                    st.image(row['url'], use_container_width=True)
                    st.caption(f"👤 {row['contributor']}")
                    
                    b_col1, b_col2 = st.columns([1, 1])
                    with b_col1:
                        if st.button(f"❤️ {row['likes']}", key=f"like_{row['public_id']}"):
                            df.at[idx, 'likes'] += 1
                            df.to_csv(DB_FILE, index=False, encoding="utf-8")
                            st.rerun()
                    
                    with b_col2:
                        if row['contributor'] == st.session_state["name"]:
                            if st.button(f"🗑️ 削除", key=f"del_{row['public_id']}", use_container_width=True):
                                # 1. Cloudinaryから画像を消す
                                cloudinary.uploader.destroy(row['public_id'])
                                # 2. CSVから消す
                                df = df.drop(idx)
                                df.to_csv(DB_FILE, index=False, encoding="utf-8")
                                st.rerun()