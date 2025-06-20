import feedparser
import requests
import json
from datetime import datetime

def collect_news():
    """ニュースを収集する関数"""
    articles = []
    
    # アメリカのRSSフィード（あなたのZapierフィードを使用）
    feeds = [
        'https://zapier.com/engine/rss/21996507/usa'
    ]
    
    print("ニュース収集を開始します...")
    
    for feed_url in feeds:
        try:
            print(f"フィード取得中: {feed_url}")
            feed = feedparser.parse(feed_url)
            
            # フィードから記事を取得
            for entry in feed.entries:
                article = {
                    'title': entry.title,
                    'url': entry.link,
                    'published': entry.published if 'published' in entry else 'N/A',
                    'collected_at': datetime.now().isoformat()
                }
                articles.append(article)
                
        except Exception as e:
            print(f"エラー: {feed_url} - {str(e)}")
    
    # 結果をJSONファイルに保存
    output_data = {
        'collection_time': datetime.now().isoformat(),
        'total_articles': len(articles),
        'articles': articles
    }
    
    with open('news_output.json', 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"収集完了！ {len(articles)}件の記事を取得しました")
    
    # 結果の一部をコンソールに表示
    for i, article in enumerate(articles[:5]):
        print(f"{i+1}. {article['title']}")

if __name__ == "__main__":
    collect_news()
