import json
import os
import streamlit as st

# ページの基本設定
st.set_page_config(
    page_title="InsightNews",
    page_icon="🌿",
    layout="centered",
)

# アースカラー基調のカスタムCSS適用（感嘆符なし）
st.markdown(
    """
    <style>
    /* 全体の背景と文字色 */
    .stApp {
        background-color: #F9F7F2;
        color: #3E362E;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* ヘッダーの調整 */
    h1, h2, h3 {
        color: #2C241D;
    }
    
    /* ニュースカードのスタイル */
    .news-card {
        background-color: #FFFFFF;
        border: 1px solid #E5E0D8;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02);
    }

    /* ニュース概要のスタイル */
    .summary-text {
        color: #4A4036;
        font-size: 0.98rem;
        line-height: 1.75;
        margin-top: 12px;
        margin-bottom: 16px;
    }
    
    /* コメント引用部分 */
    .comment-box {
        background-color: #F4F1EA;
        border-left: 3px solid #8C7B6B;
        padding: 14px 18px;
        margin: 16px 0;
        border-radius: 0 8px 8px 0;
        font-size: 0.95rem;
        line-height: 1.7;
    }
    
    /* 正当性チェックのボックス */
    .validity-box {
        background-color: #F0EDEA;
        border: 1px solid #DCD5CD;
        border-radius: 8px;
        padding: 16px;
        margin: 14px 0;
        font-size: 0.93rem;
        line-height: 1.75;
    }
    
    /* AIペルソナの返答ボックス */
    .persona-box {
        background-color: #FAF6EE;
        border: 1px solid #D8CFC4;
        border-radius: 8px;
        padding: 18px;
        margin-top: 14px;
        font-size: 0.96rem;
        line-height: 1.8;
    }
    
    .section-title {
        font-weight: bold;
        font-size: 0.85rem;
        color: #6B5B4F;
        margin-bottom: 8px;
        letter-spacing: 0.04em;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def format_paragraphs(text):
    """改行コードをHTMLの改行タグに変換して段落を見やすくする"""
    if not text:
        return ""
    return text.replace("\n", "<br>")


def load_data():
    """保存されたJSONデータを読み込む"""
    filename = "comments_analysis.json"
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def main():
    st.title("InsightNews")
    st.markdown(
        "日々の出来事に対する多様な意見を客観的に見つめ直し、高次の視点から静かな気づきを得るための空間です。"
    )
    st.markdown("---")

    data = load_data()

    if not data:
        st.info(
            "表示するデータがまだありません。バックエンドスクリプトを実行してデータを生成してください。"
        )
        return

    for item in data:
        with st.container():
            st.markdown('<div class="news-card">', unsafe_allow_html=True)

            # ニュースタイトルとリンク
            title = item.get("title", "無題のニュース")
            url = item.get("url", "#")
            st.markdown(
                f"### [{title}]({url})", unsafe_allow_html=True
            )

            # ニュース概要（100〜300字・段落分け）
            summary = format_paragraphs(item.get("summary", ""))
            if summary:
                st.markdown(
                    f'<div class="summary-text">{summary}</div>',
                    unsafe_allow_html=True,
                )

            st.markdown("---")

            # コメントと分析の表示
            comments = item.get("comments", [])
            for comment in comments:
                # 元のコメントをそのまま表示
                orig_text = format_paragraphs(comment.get("original_text", ""))
                st.markdown(
                    f'<div class="comment-box"><div class="section-title">読者のコメント</div>{orig_text}</div>',
                    unsafe_allow_html=True,
                )

                # 正当性チェック
                val_check = comment.get("validity_check", {})
                status = val_check.get("status", "")
                analysis = format_paragraphs(val_check.get("analysis", ""))
                st.markdown(
                    f'<div class="validity-box"><div class="section-title">客観的検証 （{status}）</div>{analysis}</div>',
                    unsafe_allow_html=True,
                )

                # AIペルソナの返答
                persona_resp = format_paragraphs(comment.get("persona_response", ""))
                st.markdown(
                    f'<div class="persona-box"><div class="section-title">AIペルソナからの気づき</div>{persona_resp}</div>',
                    unsafe_allow_html=True,
                )

            st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
