import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import cloudinary
import cloudinary.uploader
import os
import datetime

# --- 1. Cloudinary設定 (Secretsから読み込み) ---
cloudinary.config(
    cloud_name = st.secrets["CLOUDINARY_CLOUD_NAME"],
    api_key = st.secrets["CLOUDINARY_API_KEY"],
    api_secret = st.secrets["CLOUDINARY_API_SECRET"],
    secure = True
)

st.set_page_config(page_title="ペットSNS - 完全版", layout="wide")

# --- 2. ユーザー認証設定 ---
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
    
    # ファイルがない場合は新規作成
    if not os.path.exists(DB_FILE):
        df = pd.DataFrame(columns=["url", "public_id", "contributor", "likes", "created_at", "comments"])
        df.to_csv(DB_FILE, index=False, encoding="utf-8")

    st.title('🐶 ペット写真ギャラリー & トーク')

    # --- 3. 投稿セクション ---
    with st.expander("✨ 新しい写真を投稿する"):
        uploaded_file = st.file_uploader("写真を選択", type=["jpg", "png", "jpeg"])
        if uploaded_file:
            st.image(uploaded_file, use_container_width=True)
            if st.button("🚀 この写真を投稿する", use_container_width=True):
                # Cloudinaryへアップロード
                upload_result = cloudinary.uploader.upload(uploaded_file)
                img_url = upload_result["secure_url"]
                img_id = upload_result["public_id"]
                
                # 現在の日時
                now = datetime.datetime.now().strftime("%Y/%m/%d %H:%M")
                
                # 新しいデータ行を作成 (コメントは最初は空文字)
                new_data = pd.DataFrame([[img_url, img_id, st.session_state["name"], 0, now, ""]], 
                                      columns=["url", "public_id", "contributor", "likes", "created_at", "comments"])
                
                # 既存のデータを読み込んで結合
                df = pd.read_csv(DB_FILE, dtype={'comments': str}).fillna("")
                df = pd.concat([df, new_data], ignore_index=True)
                df.to_csv(DB_FILE, index=False, encoding="utf-8")
                
                st.success("投稿が完了しました！")
                st.rerun()

    st.divider()

    # --- 4. ギャラリー表示 & コメント機能 ---
    # ここで強制的に 'comments' 列を文字列として読み込むことでエラーを防ぎます
    df = pd.read_csv(DB_FILE, dtype={'comments': str}).fillna("")
    
    if not df.empty:
        # 新しい順に並び替え
        df_display = df.iloc[::-1]
        
        for idx, row in df_display.iterrows():
            with st.container(border=True):
                col_img, col_txt = st.columns([1, 1])
                
                # 左側：画像
                with col_img:
                    st.image(row['url'], use_container_width=True)
                
                # 右側：情報とコメント
                with col_txt:
                    st.write(f"👤 **{row['contributor']}**")
                    st.caption(f"📅 投稿日: {row['created_at']}")
                    st.write(f"❤️ {row['likes']} いいね")
                    
                    st.write("---")
                    st.write("💬 **コメント**")
                    
                    # コメントを表示（スラッシュで区切ってループ）
                    current_comments = str(row['comments'])
                    if current_comments:
                        for c in current_comments.split(" / "):
                            if c.strip():
                                st.info(c)
                    
                    # コメント投稿（ポップオーバー）
                    with st.popover("➕ コメントを書く"):
                        comment_input = st.text_input("コメント内容", key=f"in_{row['public_id']}")
                        if st.button("送信", key=f"btn_{row['public_id']}"):
                            if comment_input:
                                name = st.session_state['name']
                                new_entry = f"{name}: {comment_input}"
                                
                                # 最新のCSVを読み込み直して更新
                                full_df = pd.read_csv(DB_FILE, dtype={'comments': str}).fillna("")
                                
                                old_comments = str(full_df.at[idx, 'comments'])
                                if old_comments and old_comments != "":
                                    updated_comments = f"{old_comments} / {new_entry}"
                                else:
                                    updated_comments = new_entry
                                
                                full_df.at[idx, 'comments'] = updated_comments
                                full_df.to_csv(DB_FILE, index=False, encoding="utf-8")
                                st.rerun()

                    # ボタン類
                    st.write("")
                    b1, b2, _ = st.columns([1, 1, 2])
                    with b1:
                        if st.button("❤️", key=f"like_{row['public_id']}"):
                            full_df = pd.read_csv(DB_FILE, dtype={'comments': str}).fillna("")
                            full_df.at[idx, 'likes'] += 1
                            full_df.to_csv(DB_FILE, index=False, encoding="utf-8")
                            st.rerun()
                    with b2:
                        if row['contributor'] == st.session_state["name"]:
                            if st.button("🗑️", key=f"del_{row['public_id']}"):
                                cloudinary.uploader.destroy(row['public_id'])
                                full_df = pd.read_csv(DB_FILE, dtype={'comments': str}).fillna("")
                                full_df = full_df.drop(idx)
                                full_df.to_csv(DB_FILE, index=False, encoding="utf-8")
                                st.rerun()