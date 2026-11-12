import json
import os
import time
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from google import genai
from google.genai import types

# APIキーの設定（環境変数から取得）
API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)


def fetch_yahoo_topics():
    """Yahoo!ニュースの主要トピックスから記事タイトルとURLを取得する"""
    url = "https://news.yahoo.co.jp/rss/topics/top-picks.xml"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, "xml")
        items = soup.find_all("item")

        news_list = []
        for item in items[:3]:  # 上位3件を対象にする
            title = item.find("title").text
            link = item.find("link").text
            description = (
                item.find("description").text
                if item.find("description")
                else ""
            )
            news_list.append(
                {"title": title, "url": link, "rss_summary": description}
            )
        return news_list
    except Exception as e:
        print(f"ニュース取得時にエラーが発生しました: {e}")
        return []


def analyze_with_gemini(news_item):
    """Gemini API（Search Grounding有効）を使用して、ニュース概要、実際のコメント取得、正当性チェック、AIペルソナの返答を生成する"""

    prompt = f"""
以下のニュース記事について検索機能を使って情報を確認し、指定された4つの要素をJSON形式で作成してください。

【ニュース記事】
タイトル: {news_item['title']}
URL: {news_item['url']}
参考情報: {news_item['rss_summary']}

【作成の要件】
1. ニュースの概要（summary）：
   - 記事の背景や要点を、100字から300字程度で分かりやすくまとめてください。
   - 読みやすいように、2〜3文ごとに空行（\\n\\n）を入れて段落を分けてください。

2. 実際のコメント原文（original_text）：
   - 「〜という傾向があります」のような解説ではなく、この記事のYahoo!ニュースコメント欄などに実際に投稿されている（またはそれに非常に近い）代表的な読者の生コメントを1つ、そのままの話し言葉で載せてください。

3. 正当性チェック（validity_check）：
   - status: 「事実に基づく懸念」「前提に補足が必要」「感情的な飛躍あり」などの短いラベル。
   - analysis: 記事の事実関係や客観的データに基づいた冷静な検証・解説。適度に段落（\\n\\n）を分けてください。

4. AIペルソナの返答（persona_response）：
   - 高次の視点、人間への深い理解、知恵と慈愛をもって、コメント投稿者の感情を受け止めつつ静かに視点を広げる穏やかな語りかけ。
   - 説教や論破ではなく、本質的な気づきを促す内容にしてください。
   - 読みやすいように適切な位置で段落（\\n\\n）を分けてください。

【全体共通の厳守ルール】
- 全体の文章は、一般的な大学生が無理なく理解できる平易で自然な日本語にしてください。難解な専門用語や硬すぎる表現は避けてください。
- 感嘆符（！）はすべての項目において一切使用しないでください。

出力は必ず以下のJSONフォーマットのみで行ってください。マークダウンのバッククォートなども含めず、純粋なJSON文字列として出力してください。

{{
  "summary": "100〜300字程度のニュース概要（段落分けあり）",
  "original_text": "読者の生コメント原文",
  "validity_check": {{
    "status": "評価の状態",
    "analysis": "客観的な検証内容（段落分けあり）"
  }},
  "persona_response": "AIペルソナからの穏やかな返答（段落分けあり）"
}}
"""

    # リトライ制御の実装（最大3回試行、失敗時は300秒待機）
    max_retries = 3
    wait_seconds = 300

    for attempt in range(max_retries):
        try:
            # 最新のgemini-3.8-flashを使用し、Google Search Groundingを有効化
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    tools=[{"google_search": {}}],
                ),
            )

            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]

            result_json = json.loads(text.strip())
            return result_json

        except Exception as e:
            print(f"試行 {attempt + 1} 回目でエラーが発生しました: {e}")
            if attempt < max_retries - 1:
                print(
                    f"{wait_seconds}秒待機した後に再試行します。"
                )
                time.sleep(wait_seconds)
            else:
                print("最大試行回数に達したため、この処理をスキップします。")
                return None


def main():
    print("ニュースの取得を開始します。")
    news_items = fetch_yahoo_topics()

    if not news_items:
        print("有効なニュースを取得できませんでした。")
        return

    processed_data = []

    for idx, item in enumerate(news_items):
        print(
            f"処理中 ({idx + 1}/{len(news_items)}): {item['title']}"
        )
        analysis_result = analyze_with_gemini(item)

        if analysis_result:
            article_entry = {
                "article_id": f"art_{datetime.now().strftime('%Y%m%d')}_{idx+1}",
                "fetched_at": datetime.now().isoformat(),
                "title": item["title"],
                "url": item["url"],
                "summary": analysis_result.get("summary", item["rss_summary"]),
                "comments": [
                    {
                        "comment_id": "c01",
                        "original_text": analysis_result.get("original_text", ""),
                        "validity_check": analysis_result.get("validity_check", {}),
                        "persona_response": analysis_result.get("persona_response", ""),
                    }
                ],
            }
            processed_data.append(article_entry)

        time.sleep(2)

    output_filename = "comments_analysis.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(processed_data, f, ensure_ascii=False, indent=2)

    print(f"処理が完了しました。結果を {output_filename} に保存しました。")


if __name__ == "__main__":
    main()
