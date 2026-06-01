import streamlit as st
import json
import os
import tempfile
from generate_outline import generate_outline_from_text
from outline_to_json import convert_outline_to_json
from generate_slides import create_slides_from_json
from generate_speaker_notes import SpeakerNotesGenerator
from generate_video import VideoGenerator

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

    google_api_key = st.text_input(
        "Google APIキー",
        type="password",
        value=os.environ.get("GOOGLE_API_KEY", ""),
        help="講義動画生成に使用（Gemini TTS）"
    )
    
    # st.divider()
    
    # st.header("📁 テンプレート")
    # template_file = st.file_uploader(
    #     "PowerPointテンプレートをアップロード",
    #     type=['pptx'],
    #     help="スライト_テンフ_レ.pptx のようなテンプレートファイル"
    # )
    
    # if template_file:
    #     # 一時保存
    #     template_path = "/tmp/template.pptx"
    #     with open(template_path, "wb") as f:
    #         f.write(template_file.getbuffer())
    #     st.success("✅ テンプレート読み込み完了")
    # else:
    #     template_path = "スライドテンプレ.pptx"
    template_path = "スライドテンプレ.pptx"

# タブを作成
tab1, tab2, tab3, tab4 = st.tabs([
    "📝 Step 1: アウトライン生成",
    "🎯 Step 2: スライド生成",
    "📢 Step 3: 発表者ノート生成",
    "🎬 Step 4: 講義動画生成"
])

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

# ========================================
# タブ3: 発表者ノート生成
# ========================================
with tab3:
    st.header("Step 3: 完成スライドから発表者ノート生成")
    st.markdown("""
    完成済みのPowerPointスライドとPDFファイルをアップロードして、各スライドの発表者ノート原稿を自動生成します。

    💡 **処理の流れ:**
    1. PDFから各ページを画像として抽出
    2. Claude AIが各スライドの内容を分析
    3. 発表者向けの詳細な原稿を生成
    4. PPTXファイルの発表者ノートに追記
    """)

    # PPTXファイルのアップロード
    col_pptx, col_pdf = st.columns(2)

    with col_pptx:
        uploaded_pptx = st.file_uploader(
            "PowerPointファイルをアップロード",
            type=['pptx'],
            help="発表者ノートを追加したいPowerPointファイルをアップロードしてください"
        )

    with col_pdf:
        uploaded_pdf = st.file_uploader(
            "PDFファイルをアップロード",
            type=['pdf'],
            help="スライド画像抽出用のPDFファイルをアップロードしてください"
        )

    if uploaded_pptx and uploaded_pdf:
        # ファイル情報を表示
        pptx_size_mb = len(uploaded_pptx.getvalue()) / (1024 * 1024)
        pdf_size_mb = len(uploaded_pdf.getvalue()) / (1024 * 1024)
        st.info(f"📎 PPTX: {uploaded_pptx.name} ({pptx_size_mb:.1f} MB) | PDF: {uploaded_pdf.name} ({pdf_size_mb:.1f} MB)")

        # 発表者ノート生成ボタン
        if st.button("🎤 発表者ノート生成", use_container_width=True, type="primary"):
            if not api_key:
                st.error("❌ APIキーを設定してください（サイドバー）")
            else:
                try:
                    # 一時ファイルに保存
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pptx") as tmp_input_pptx:
                        tmp_input_pptx.write(uploaded_pptx.getvalue())
                        input_pptx_path = tmp_input_pptx.name

                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_input_pdf:
                        tmp_input_pdf.write(uploaded_pdf.getvalue())
                        input_pdf_path = tmp_input_pdf.name

                    with tempfile.NamedTemporaryFile(delete=False, suffix="_with_notes.pptx") as tmp_output:
                        output_path = tmp_output.name

                    # 進捗表示用のプレースホルダー
                    progress_placeholder = st.empty()
                    progress_bar = st.progress(0)
                    status_placeholder = st.empty()

                    # 進捗コールバック関数
                    def update_progress(step_name, current, total):
                        progress = current / total
                        progress_bar.progress(progress)
                        status_placeholder.text(f"[{current}/{total}] {step_name}")

                    # 発表者ノート生成を実行
                    generator = SpeakerNotesGenerator(api_key)

                    success, message, notes_list = generator.process_pptx_with_pdf(
                        input_pptx_path, input_pdf_path, output_path, progress_callback=update_progress
                    )
                    
                    if success:
                        # 完成したファイルを読み込み
                        with open(output_path, 'rb') as f:
                            pptx_with_notes = f.read()
                        
                        st.success(message)
                        
                        # 生成された原稿をプレビュー表示
                        with st.expander("📝 生成された発表者ノート（プレビュー）"):
                            for i, note in enumerate(notes_list):
                                st.markdown(f"**スライド {i+1}:**")
                                st.text_area(
                                    f"原稿 {i+1}",
                                    value=note,
                                    height=100,
                                    disabled=True,
                                    key=f"note_{i}"
                                )
                                st.divider()
                        
                        # ダウンロードボタン
                        st.download_button(
                            label="💾 発表者ノート付きPowerPointをダウンロード",
                            data=pptx_with_notes,
                            file_name=f"notes_{uploaded_pptx.name}",
                            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                            use_container_width=True
                        )
                        
                        # 統計情報
                        st.info(f"✅ 処理完了: {len(notes_list)}枚のスライドの発表者ノートを生成しました")
                    
                    else:
                        st.error(f"❌ エラー: {message}")

                    # 一時ファイルを削除
                    try:
                        os.unlink(input_pptx_path)
                        os.unlink(input_pdf_path)
                        os.unlink(output_path)
                    except:
                        pass
                    
                    # 進捗表示をクリア
                    progress_placeholder.empty()
                    progress_bar.empty()
                    status_placeholder.empty()
                    
                except Exception as e:
                    st.error(f"❌ 処理中にエラーが発生しました: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())

    else:
        if not uploaded_pptx and not uploaded_pdf:
            st.info("👆 PowerPointファイルとPDFファイルをアップロードして開始してください")
        elif not uploaded_pptx:
            st.warning("⚠️ PowerPointファイルをアップロードしてください")
        elif not uploaded_pdf:
            st.warning("⚠️ PDFファイルをアップロードしてください")

    # 注意事項
    st.divider()
    st.markdown("**⚠️ 注意事項:**")
    st.markdown("""
    - PPTXファイルとPDFファイルの両方が必要です（同じスライドのPPTXとPDF版を用意してください）
    - 処理には数分かかる場合があります（スライド数に依存）
    - 生成された原稿は目安として使用し、必要に応じて手動で調整してください
    - 大きなファイル（30MB超）は処理に時間がかかる場合があります
    """)

# ========================================
# タブ4: 講義動画生成
# ========================================
with tab4:
    st.header("Step 4: 発表者ノートから講義動画生成")
    st.markdown("""
    発表者ノート付きのPowerPointとスライド画像ZIPをアップロードして、発表者ノートを読み上げる講義動画を自動生成します。

    💡 **処理の流れ:**
    1. PPTXから発表者ノートを抽出
    2. ZIPから各スライド画像を抽出
    3. 発表者ノートをGemini TTSで音声に変換
    4. スライド画像と音声を合成して動画作成
    5. 全スライドの動画を結合して最終動画を生成
    """)

    # ファイルアップロード
    col_pptx_v, col_zip_v = st.columns(2)

    with col_pptx_v:
        video_pptx = st.file_uploader(
            "PowerPointファイル（発表者ノート付き）",
            type=['pptx'],
            help="発表者ノートが含まれたPowerPointファイルをアップロードしてください",
            key="video_pptx"
        )

    with col_zip_v:
        video_zip = st.file_uploader(
            "スライド画像ZIP",
            type=['zip'],
            help="スライド1.jpeg, スライド2.jpeg... の形式で画像を格納したZIPファイル",
            key="video_zip"
        )

    if video_pptx and video_zip:
        # ファイル情報を表示
        pptx_size_mb = len(video_pptx.getvalue()) / (1024 * 1024)
        zip_size_mb = len(video_zip.getvalue()) / (1024 * 1024)
        st.info(f"📎 PPTX: {video_pptx.name} ({pptx_size_mb:.1f} MB) | ZIP: {video_zip.name} ({zip_size_mb:.1f} MB)")

        # 動画生成ボタン
        if st.button("🎬 講義動画生成", use_container_width=True, type="primary"):
            if not google_api_key:
                st.error("❌ Google APIキーを設定してください（サイドバー）")
            else:
                try:
                    # 一時ファイルに保存
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pptx") as tmp_pptx:
                        tmp_pptx.write(video_pptx.getvalue())
                        input_pptx_path = tmp_pptx.name

                    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_zip:
                        tmp_zip.write(video_zip.getvalue())
                        input_zip_path = tmp_zip.name

                    # 出力動画ファイル用の一時ファイル（削除せずに保持）
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_output:
                        output_video_path = tmp_output.name

                    # 進捗表示用のプレースホルダー
                    video_progress_placeholder = st.empty()
                    video_progress_bar = st.progress(0)
                    video_status_placeholder = st.empty()

                    # 進捗コールバック関数
                    def update_video_progress(step_name, current, total):
                        progress = current / total if total > 0 else 0
                        video_progress_bar.progress(progress)
                        video_status_placeholder.text(f"[{current}/{total}] {step_name}")

                    # 動画生成を実行
                    generator = VideoGenerator(google_api_key)

                    success, message = generator.generate_video(
                        input_pptx_path, input_zip_path, output_video_path,
                        progress_callback=update_video_progress
                    )

                    if success:
                        # ファイルサイズを取得
                        file_size_mb = os.path.getsize(output_video_path) / (1024 * 1024)

                        # セッションステートにファイルパスとメタデータを保存
                        st.session_state['video_file_path'] = output_video_path
                        st.session_state['video_filename'] = os.path.splitext(video_pptx.name)[0] + "_lecture.mp4"
                        st.session_state['video_file_size_mb'] = file_size_mb

                        st.success(f"{message} (ファイルサイズ: {file_size_mb:.1f} MB)")

                        # 大きなファイルの場合は警告
                        if file_size_mb > 200:
                            st.warning("⚠️ ファイルサイズが大きいため、ダウンロードに時間がかかる場合があります。")

                    else:
                        st.error(f"❌ エラー: {message}")

                    # 入力ファイルのみ削除（出力動画は保持）
                    try:
                        os.unlink(input_pptx_path)
                        os.unlink(input_zip_path)
                    except:
                        pass

                    # 進捗表示をクリア
                    video_progress_placeholder.empty()
                    video_progress_bar.empty()
                    video_status_placeholder.empty()

                except Exception as e:
                    st.error(f"❌ 処理中にエラーが発生しました: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())

    # 動画プレビューとダウンロードボタン（セッションステートから表示）
    if 'video_file_path' in st.session_state and os.path.exists(st.session_state['video_file_path']):
        st.divider()
        st.subheader("📥 生成された講義動画")

        video_path = st.session_state['video_file_path']
        file_size_mb = st.session_state.get('video_file_size_mb', 0)

        # ファイルサイズ情報を表示
        st.info(f"📊 ファイルサイズ: {file_size_mb:.1f} MB")

        # 動画プレビュー（ファイルから読み込み）
        with open(video_path, 'rb') as f:
            st.video(f.read())

        # ダウンロードボタン（ファイルから読み込み）
        with open(video_path, 'rb') as f:
            st.download_button(
                label="💾 講義動画をダウンロード",
                data=f.read(),
                file_name=st.session_state['video_filename'],
                mime="video/mp4",
                use_container_width=True
            )

    else:
        if not video_pptx and not video_zip:
            st.info("👆 PowerPointファイルとスライド画像ZIPをアップロードして開始してください")
        elif not video_pptx:
            st.warning("⚠️ PowerPointファイルをアップロードしてください")
        elif not video_zip:
            st.warning("⚠️ スライド画像ZIPをアップロードしてください")

    # 注意事項
    st.divider()
    st.markdown("**⚠️ 注意事項:**")
    st.markdown("""
    - 発表者ノート付きのPPTXファイルが必要です（Step 3で生成したものを使用してください）
    - ZIPファイルには「スライド1.jpeg」「スライド2.jpeg」...の形式で画像を格納してください
    - 発表者ノートがないスライドは3秒間の無音表示になります
    - 処理にはスライド枚数に応じて時間がかかります（1枚あたり約10-20秒）
    - ffmpegがシステムにインストールされている必要があります
    """)

# フッター
st.divider()
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.8em;'>
    講義スライド自動生成ツール v1.0 | Powered by Claude API
</div>
""", unsafe_allow_html=True)
