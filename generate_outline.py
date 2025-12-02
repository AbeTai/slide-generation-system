import os
from anthropic import Anthropic


def generate_outline_from_text(input_text, api_key=None, detail_level="standard"):
    """
    テキストからClaude APIを使って人間が読みやすいアウトラインを生成
    
    Args:
        input_text: 講義の元となるテキスト
        api_key: Anthropic APIキー (Noneの場合は環境変数から取得)
        detail_level: 詳細度 ("standard" or "detailed")
    
    Returns:
        str: 人間が読みやすい形式のアウトライン（txt形式）
    """
    # APIキーの取得
    if api_key is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    if not api_key:
        raise ValueError("APIキーが設定されていません。環境変数ANTHROPIC_API_KEYを設定するか、引数で渡してください。")
    
    # Claude APIクライアントを初期化
    client = Anthropic(api_key=api_key)
    
    # 詳細度に応じた指示を設定
    if detail_level == "detailed":
        detail_instruction = """
要件（詳細版）:
- アジェンダは4-7個程度（標準版より多め）
- 各アジェンダには2-5枚程度のスライドを作成（標準版より多め）
- 各スライドの内容はより詳しく、具体例や補足説明も含める
- サブ項目も積極的に使用して情報を構造化
- 各スライドは400-500文字程度でも可
- 実践的な例やケーススタディも含める
"""
    else:  # standard
        detail_instruction = """
要件（標準版）:
- アジェンダは3-5個程度
- 各アジェンダには1-3枚程度のスライドを作成
- 各スライドの内容は「•」または「-」を使った箇条書き
- 各スライドは300文字程度に収める
- 人間が修正しやすいように、わかりやすく構造化
"""
    
    # プロンプトを構築
    prompt = f"""以下のテキストを元に、講義スライドのアウトラインを作成してください。

出力形式は以下のような人間が読みやすいテキスト形式でお願いします：

```
タイトル: [講義全体のタイトル]

アジェンダ:
1. [アジェンダ1のタイトル]
2. [アジェンダ2のタイトル]
3. [アジェンダ3のタイトル]
...

---

## 1. [アジェンダ1のタイトル]

### スライド1
- 箇条書き項目1
- 箇条書き項目2
  - サブ項目
- 箇条書き項目3

### スライド2
- 箇条書き項目1
- 箇条書き項目2

---

## 2. [アジェンダ2のタイトル]

### スライド1
- 箇条書き項目1
- 箇条書き項目2

...
```

{detail_instruction}

入力テキスト:
{input_text}

上記の形式でアウトラインを作成してください。説明は不要で、アウトラインのみを出力してください。"""

    # Claude APIを呼び出し
    detail_label = "詳細版" if detail_level == "detailed" else "標準版"
    print(f"Claude APIでアウトラインを生成中...({detail_label})")
    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=20000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # レスポンスからテキストを取得
    outline_text = message.content[0].text.strip()
    
    # ```で囲まれている場合は除去
    if outline_text.startswith("```"):
        lines = outline_text.split("\n")
        outline_text = "\n".join(lines[1:-1]) if len(lines) > 2 else outline_text
    
    print("アウトライン生成完了")
    
    return outline_text


if __name__ == "__main__":
    # テスト実行
    test_input = """
    機械学習の基礎について学ぶ講義を作成します。
    
    機械学習とは何か、教師あり学習と教師なし学習の違い、
    代表的なアルゴリズム（線形回帰、ロジスティック回帰、決定木）、
    モデルの評価方法、過学習と正則化について扱います。
    """
    
    try:
        outline = generate_outline_from_text(test_input)
        print("\n=== 生成されたアウトライン ===")
        print(outline)
        
        # ファイルに保存
        with open('/home/claude/outline_sample.txt', 'w', encoding='utf-8') as f:
            f.write(outline)
        print("\n保存先: /home/claude/outline_sample.txt")
        
    except ValueError as e:
        print(f"エラー: {e}")
