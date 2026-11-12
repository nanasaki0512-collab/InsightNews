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
                {"title": title, "url": link, "summary": description}
            )
        return news_list
    except Exception as e:
        print(f"ニュース取得時にエラーが発生しました: {e}")
        return []


def analyze_with_gemini(news_item):
    """Gemini APIを使用して、コメントの想定と正当性チェック、AIペルソナの返答を生成する"""

    prompt = f"""
以下のニュース記事について、読者がコメント欄に残しそうな代表的な意見（批判的または懸念を示すもの）を1つ想定し、それに対する分析とAIペルソナからの返答をJSON形式で作成してください。

【ニュース記事】
タイトル: {news_item['title']}
概要: {news_item['summary']}

【要件】
1. コメント原文（original_text）：この記事に対して一般の読者が抱きそうな率直な意見や懸念。
2. 正当性チェック（validity_check）：
   - status: 「事実に基づく懸念」「前提に補足が必要」「感情的な飛躍あり」などの評価。
   - analysis: 記事の事実関係や客観的データに基づいた冷静な検証・解説。
3. AIペルソナの返答（persona_response）：
   - 高次の視点、深い理解、知恵と慈愛をもって、読者の感情を受け止めつつ静かに視点を広げるような穏やかな語りかけ。
   - 説教や論破ではなく、本質的な気づきを促すこと。
   - 感嘆符（！）は一切使用しないこと。

出力は必ず以下のJSONフォーマットのみで行ってください。マークダウンのバッククォートなども含めず、純粋なJSON文字列として出力してください。

{{
  "original_text": "ここに想定されるコメントを入力",
  "validity_check": {{
    "status": "評価の状態",
    "analysis": "客観的な検証内容"
  }},
  "persona_response": "AIペルソナからの穏やかな返答"
}}
"""

    # リトライ制御の実装（最大3回試行、失敗時は300秒待機）
    max_retries = 3
    wait_seconds = 300

    for attempt in range(max_retries):
        try:
            # 指定された最新のgemini-3.8-flashを使用
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
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
                "summary": item["summary"],
                "comments": [
                    {
                        "comment_id": "c01",
                        "original_text": analysis_result["original_text"],
                        "validity_check": analysis_result["validity_check"],
                        "persona_response": analysis_result[
                            "persona_response"
                        ],
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
