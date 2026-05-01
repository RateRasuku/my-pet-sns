import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import cloudinary
import cloudinary.uploader
import os
import datetime

# --- 1. Cloudinary設定 ---
cloudinary.config(
    cloud_name = st.secrets["CLOUDINARY_CLOUD_NAME"],
    api_key = st.secrets["CLOUDINARY_API_KEY"],
    api_secret = st.secrets["CLOUDINARY_API_SECRET"],
    secure = True
)

st.set_page_config(page_title="ペットSNS - コメント機能", layout="wide")

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
        df = pd.DataFrame(columns=["url", "public_id", "contributor", "likes", "created_at", "comments"])
        df.to_csv(DB_FILE, index=False, encoding="utf-8")

    st.title('🐶 ペットギャラリー & トーク')

    # --- 3. 投稿セクション ---
    with st.expander("✨ 写真を投稿する"):
        uploaded_file = st.file_uploader("写真を選択", type=["jpg", "png", "jpeg"])
        if uploaded_file:
            st.image(uploaded_file, use_container_width=True)
            if st.button("🚀 投稿する", use_container_width=True):
                upload_result = cloudinary.uploader.upload(uploaded_file)
                img_url = upload_result["secure_url"]
                img_id = upload_result["public_id"]
                # 現在の日付を取得
                now = datetime.datetime.now().strftime("%Y/%m/%d %H:%M")
                
                # 新しいデータを追加（最初はコメント空っぽ）
                new_data = pd.DataFrame([[img_url, img_id, st.session_state["name"], 0, now, ""]], 
                                      columns=["url", "public_id", "contributor", "likes", "created_at", "comments"])
                df = pd.read_csv(DB_FILE)
                df = pd.concat([df, new_data], ignore_index=True)
                df.to_csv(DB_FILE, index=False, encoding="utf-8")
                st.success("投稿完了！")
                st.rerun()

    st.divider()

    # --- 4. ギャラリー表示 ---
    df = pd.read_csv(DB_FILE).fillna("") # 空白をエラーにしないための処理
    if not df.empty:
        df_display = df.iloc[::-1]
        
        # 1列に1つの投稿を大きく表示する形式に変更
        for idx, row in df_display.iterrows():
            with st.container(border=True):
                col_img, col_txt = st.columns([1, 1])
                
                with col_img:
                    st.image(row['url'], use_container_width=True)
                
                with col_txt:
                    st.write(f"👤 **{row['contributor']}**")
                    st.caption(f"📅 投稿日: {row['created_at']}")
                    st.write(f"❤️ {row['likes']} いいね")
                    
                    # --- コメント表示エリア ---
                    st.write("---")
                    st.write("💬 コメント")
                    if row['comments']:
                        for c in str(row['comments']).split(" / "):
                            st.info(c)
                    
                    # --- コメント入力エリア ---
                    with st.popover("➕ コメントを書く"):
                        new_comment = st.text_input("コメントを入力", key=f"input_{row['public_id']}")
                        if st.button("送信", key=f"btn_{row['public_id']}"):
                            if new_comment:
                                # 名前と時間を付けて保存
                                comment_with_name = f"{st.session_state['name']}: {new_comment}"
                                if row['comments']:
                                    updated_comments = f"{row['comments']} / {comment_with_name}"
                                else:
                                    updated_comments = comment_with_name
                                
                                # CSVを更新
                                full_df = pd.read_csv(DB_FILE)
                                # 元のインデックスを使って正確に更新
                                full_df.loc[idx, 'comments'] = updated_comments
                                full_df.to_csv(DB_FILE, index=False, encoding="utf-8")
                                st.rerun()

                    # --- いいね & 削除ボタン ---
                    st.write("")
                    b1, b2, _ = st.columns([1, 1, 2])
                    with b1:
                        if st.button("❤️", key=f"like_{row['public_id']}"):
                            full_df = pd.read_csv(DB_FILE)
                            full_df.loc[idx, 'likes'] += 1
                            full_df.to_csv(DB_FILE, index=False, encoding="utf-8")
                            st.rerun()
                    with b2:
                        if row['contributor'] == st.session_state["name"]:
                            if st.button("🗑️", key=f"del_{row['public_id']}"):
                                cloudinary.uploader.destroy(row['public_id'])
                                full_df = pd.read_csv(DB_FILE)
                                full_df = full_df.drop(idx)
                                full_df.to_csv(DB_FILE, index=False, encoding="utf-8")
                                st.rerun()