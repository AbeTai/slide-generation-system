import streamlit as st
import json
import os
from generate_outline import generate_outline_from_text
from outline_to_json import convert_outline_to_json
from generate_slides import create_slides_from_json

# ページ設定
st.set_page_config(
    page_title="講義スライド自動生成ツール",
    page_icon="📊",
    layout="wide"
)

st.title("📊 講義スライド自動生成ツール")

# APIキーの設定（サイドバー）
with st.sidebar:
    st.header("⚙️ 設定")
    api_key = st.text_input(
        "Anthropic APIキー",
        type="password",
        value=os.environ.get("ANTHROPIC_API_KEY", ""),
        help="Claude APIを使用するためのAPIキーを入力してください"
    )
    
    template_path = "スライドテンプレ.pptx"

# タブを作成
tab1, tab2 = st.tabs(["📝 Step 1: アウトライン生成", "🎯 Step 2: スライド生成"])

# ========================================
# タブ1: テキスト → アウトライン生成
# ========================================
with tab1:
    st.header("Step 1: テキストからアウトライン生成")
    st.markdown("""
    講義の内容を自由に記述してください。AIが構造化されたアウトラインを生成します。
    
    💡 **ボタンの使い分け:**
    - **アウトライン生成**: 標準的な枚数（3-5アジェンダ、各1-3スライド）
    - **もっと詳しく**: より詳細な内容（4-7アジェンダ、各2-5スライド）
    """)
    
    # 入力テキストエリア
    input_text = st.text_area(
        "講義の内容を入力",
        height=300,
        placeholder="""例:
機械学習の基礎について学ぶ講義を作成します。

機械学習とは何か、教師あり学習と教師なし学習の違い、
代表的なアルゴリズム（線形回帰、ロジスティック回帰、決定木）、
モデルの評価方法、過学習と正則化について扱います。
"""
    )
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        generate_btn = st.button("🚀 アウトライン生成", use_container_width=True)
    
    with col2:
        generate_detailed_btn = st.button("📚 もっと詳しく", use_container_width=True, type="secondary")
    
    # 生成ボタンの処理
    detail_level = None
    if generate_btn:
        detail_level = "standard"
    elif generate_detailed_btn:
        detail_level = "detailed"
    
    if detail_level:
        if not api_key:
            st.error("❌ APIキーを設定してください（サイドバー）")
        elif not input_text.strip():
            st.error("❌ 講義内容を入力してください")
        else:
            detail_label = "詳細版" if detail_level == "detailed" else "標準版"
            with st.spinner(f"アウトライン生成中...({detail_label})"):
                try:
                    outline = generate_outline_from_text(input_text, api_key, detail_level)
                    st.session_state['outline'] = outline
                    st.session_state['detail_level'] = detail_level
                    
                    if detail_level == "detailed":
                        st.success("✅ 詳細版アウトライン生成完了！（スライド数が多くなります）")
                    else:
                        st.success("✅ アウトライン生成完了！")
                except Exception as e:
                    st.error(f"❌ エラー: {str(e)}")
    
    # 生成されたアウトラインを表示・編集可能に
    if 'outline' in st.session_state:
        st.divider()
        
        # 詳細度バッジを表示
        if 'detail_level' in st.session_state and st.session_state['detail_level'] == "detailed":
            st.info("📚 詳細版で生成されました（スライド数が多めです）")
        
        st.subheader("📄 生成されたアウトライン（編集可能）")
        st.markdown("*内容を確認し、必要に応じて修正してください。*")
        
        edited_outline = st.text_area(
            "アウトライン",
            value=st.session_state['outline'],
            height=400,
            key="outline_editor"
        )
        
        # アウトラインをテキストファイルとしてダウンロード
        st.download_button(
            label="💾 アウトラインをダウンロード (.txt)",
            data=edited_outline,
            file_name="lecture_outline.txt",
            mime="text/plain"
        )
        
        # 編集したアウトラインを保存
        if st.button("✅ このアウトラインで確定", use_container_width=True):
            st.session_state['final_outline'] = edited_outline
            st.success("アウトラインを確定しました！「Step 2: スライド生成」タブに進んでください。")

# ========================================
# タブ2: アウトライン → JSON → PPTX
# ========================================
with tab2:
    st.header("Step 2: アウトラインからスライド生成")
    st.markdown("""
    Step 1で生成したアウトライン、または手動で作成したアウトラインからスライドを生成します。
    """)
    
    # アウトラインの入力方法を選択
    input_method = st.radio(
        "アウトラインの入力方法",
        ["Step 1から引き継ぐ", "テキストファイルをアップロード", "直接入力"]
    )
    
    outline_text = None
    
    if input_method == "Step 1から引き継ぐ":
        if 'final_outline' in st.session_state:
            outline_text = st.session_state['final_outline']
            st.text_area("アウトライン（プレビュー）", value=outline_text, height=200, disabled=True)
        else:
            st.warning("⚠️ Step 1でアウトラインを生成してください")
    
    elif input_method == "テキストファイルをアップロード":
        uploaded_outline = st.file_uploader("アウトラインファイル (.txt)", type=['txt'])
        if uploaded_outline:
            outline_text = uploaded_outline.read().decode('utf-8')
            st.text_area("アップロードされたアウトライン", value=outline_text, height=200, disabled=True)
    
    else:  # 直接入力
        outline_text = st.text_area(
            "アウトラインを入力",
            height=300,
            placeholder="""タイトル: 機械学習の基礎

アジェンダ:
1. 機械学習とは
2. 代表的なアルゴリズム

---

## 1. 機械学習とは

### スライド1
- 機械学習の定義
- AIとの関係
"""
        )
    
    st.divider()
    
    # スライド生成ボタン
    if st.button("🎨 スライド生成", use_container_width=True, type="primary"):
        if not api_key:
            st.error("❌ APIキーを設定してください（サイドバー）")
        elif not template_path:
            st.error("❌ PowerPointテンプレートをアップロードしてください（サイドバー）")
        elif not outline_text or not outline_text.strip():
            st.error("❌ アウトラインを入力してください")
        else:
            try:
                # Step 1: アウトライン → JSON
                with st.spinner("アウトラインをJSON形式に変換中..."):
                    json_data = convert_outline_to_json(outline_text, api_key)
                    st.session_state['json_data'] = json_data
                
                # JSONをプレビュー表示
                with st.expander("📋 生成されたJSON（確認用）"):
                    st.json(json_data)
                
                # Step 2: JSON → PPTX
                with st.spinner("PowerPointスライドを生成中..."):
                    json_path = "/tmp/lecture.json"
                    output_path = "/tmp/generated_slides.pptx"
                    
                    # JSONを一時保存
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(json_data, f, ensure_ascii=False, indent=2)
                    
                    # スライド生成
                    create_slides_from_json(template_path, json_path, output_path)
                    
                    # 生成されたファイルを読み込む
                    with open(output_path, 'rb') as f:
                        pptx_data = f.read()
                    
                    st.session_state['pptx_data'] = pptx_data
                    st.session_state['pptx_filename'] = f"{json_data['title']}.pptx"
                
                st.success("✅ スライド生成完了！")
                
            except Exception as e:
                st.error(f"❌ エラー: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
    
    # ダウンロードボタン
    if 'pptx_data' in st.session_state:
        st.divider()
        st.subheader("📥 ダウンロード")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.download_button(
                label="💾 PowerPointをダウンロード",
                data=st.session_state['pptx_data'],
                file_name=st.session_state['pptx_filename'],
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                use_container_width=True
            )
        
        with col2:
            if 'json_data' in st.session_state:
                st.download_button(
                    label="📄 JSONをダウンロード",
                    data=json.dumps(st.session_state['json_data'], ensure_ascii=False, indent=2),
                    file_name="lecture_structure.json",
                    mime="application/json",
                    use_container_width=True
                )

# フッター
st.divider()
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.8em;'>
    講義スライド自動生成ツール v1.0 | Powered by Claude API
</div>
""", unsafe_allow_html=True)