import json
import os
from anthropic import Anthropic


def convert_outline_to_json(outline_text, api_key=None):
    """
    人間が修正したアウトラインテキストをJSONに変換
    (人間の修正でフォーマットがズレている可能性があるため、LLMで整形)
    
    Args:
        outline_text: アウトラインテキスト
        api_key: Anthropic APIキー (Noneの場合は環境変数から取得)
    
    Returns:
        dict: JSON形式の講義データ
    """
    # APIキーの取得
    if api_key is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    if not api_key:
        raise ValueError("APIキーが設定されていません。")
    
    # Claude APIクライアントを初期化
    client = Anthropic(api_key=api_key)
    
    # プロンプトを構築
    prompt = f"""以下のアウトラインテキストを、指定されたJSON形式に変換してください。
人間が手動で修正している可能性があるため、多少フォーマットがズレていても柔軟に解釈してください。

出力するJSON形式:
{{
  "title": "講義のタイトル",
  "agenda": ["アジェンダ1", "アジェンダ2", "アジェンダ3", ...],
  "main": {{
    "アジェンダ1": ["スライド1の内容\\n箇条書き", "スライド2の内容\\n箇条書き", ...],
    "アジェンダ2": ["スライド1の内容\\n箇条書き", ...],
    ...
  }}
}}

注意事項:
- 各スライドの内容は改行を含む1つの文字列として格納
- 箇条書きは「•」または「-」で始まる
- JSONのみを出力し、それ以外の説明やマークダウンは不要

アウトラインテキスト:
{outline_text}

上記をJSON形式に変換してください。JSONのみを出力してください。"""

    # Claude APIを呼び出し
    print("アウトラインをJSONに変換中...")
    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=20000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # レスポンスからテキストを取得
    response_text = message.content[0].text.strip()
    
    # JSONをパース (```json と ``` を削除)
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    if response_text.startswith("```"):
        response_text = response_text[3:]
    if response_text.endswith("```"):
        response_text = response_text[:-3]
    response_text = response_text.strip()
    
    try:
        lecture_data = json.loads(response_text)
        print("JSON変換完了")
        return lecture_data
    except json.JSONDecodeError as e:
        print(f"JSONパースエラー: {e}")
        print(f"レスポンステキスト:\n{response_text}")
        raise


if __name__ == "__main__":
    # テスト実行（サンプルアウトライン）
    sample_outline = """
タイトル: 機械学習の基礎

アジェンダ:
1. 機械学習とは
2. 代表的なアルゴリズム
3. モデル評価

---

## 1. 機械学習とは

### スライド1
- 機械学習の定義
- AIとの関係
- 実用例

### スライド2
- 教師あり学習
- 教師なし学習
- 強化学習

---

## 2. 代表的なアルゴリズム

### スライド1
- 線形回帰
- ロジスティック回帰
- 決定木

---

## 3. モデル評価

### スライド1
- 交差検証
- 精度指標
- 混同行列
"""
    
    try:
        json_data = convert_outline_to_json(sample_outline)
        print("\n=== 生成されたJSON ===")
        print(json.dumps(json_data, ensure_ascii=False, indent=2))
        
        # ファイルに保存
        with open('/home/claude/converted.json', 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        print("\n保存先: /home/claude/converted.json")
        
    except ValueError as e:
        print(f"エラー: {e}")
