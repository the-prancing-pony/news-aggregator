import feedparser
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
import time
import re

class NewsCollector:
    def __init__(self):
        self.articles = []
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def extract_media_name(self, url):
        """URLからメディア名を抽出"""
        domain = urlparse(url).netloc.lower()
        if 'cnn.com' in domain:
            return 'CNN'
        elif 'foxnews.com' in domain:
            return 'Fox News'
        elif 'nytimes.com' in domain:
            return 'New York Times'
        elif 'wsj.com' in domain:
            return 'Wall Street Journal'
        elif 'breitbart.com' in domain:
            return 'Breitbart'
        elif 'bbc.com' in domain or 'bbc.co.uk' in domain:
            return 'BBC'
        elif 'theguardian.com' in domain:
            return 'The Guardian'
        elif 'telegraph.co.uk' in domain:
            return 'Telegraph'
        elif 'reuters.com' in domain:
            return 'Reuters'
        else:
            # ドメインから推測
            return domain.replace('www.', '').split('.')[0].title()

    def collect_from_rss(self, rss_url, max_articles=5):
        """RSSフィードから記事収集"""
        try:
            print(f"RSS収集中: {rss_url}")
            feed = feedparser.parse(rss_url)
            
            if not feed.entries:
                print(f"⚠️ RSS記事が見つかりません: {rss_url}")
                return []
            
            articles = []
            for entry in feed.entries[:max_articles]:
                article = {
                    'title': entry.title,
                    'url': entry.link,
                    'published': entry.published if 'published' in entry else 'N/A',
                    'summary': entry.summary if 'summary' in entry else '',
                    'media': self.extract_media_name(entry.link),
                    'collection_method': 'RSS',
                    'collected_at': datetime.now().isoformat()
                }
                articles.append(article)
            
            print(f"✅ RSS: {len(articles)}件収集完了")
            return articles
            
        except Exception as e:
            print(f"❌ RSSエラー {rss_url}: {str(e)}")
            return []

    def collect_from_html(self, url, selectors, max_articles=5):
        """HTMLページから記事収集"""
        try:
            print(f"HTML収集中: {url}")
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []
            
            # 見出しとリンクを取得
            headlines = soup.select(selectors['headlines'])[:max_articles]
            
            for headline in headlines:
                # リンクを取得
                link = headline.get('href') or headline.find('a')
                if link:
                    if hasattr(link, 'get'):
                        article_url = link.get('href')
                    else:
                        article_url = link
                    
                    # 相対URLを絶対URLに変換
                    if article_url and not article_url.startswith('http'):
                        article_url = urljoin(url, article_url)
                    
                    # タイトルを取得
                    title = headline.get_text(strip=True)
                    if title and article_url:
                        article = {
                            'title': title,
                            'url': article_url,
                            'published': 'N/A',
                            'summary': '',
                            'media': self.extract_media_name(url),
                            'collection_method': 'HTML',
                            'collected_at': datetime.now().isoformat()
                        }
                        articles.append(article)
            
            print(f"✅ HTML: {len(articles)}件収集完了")
            return articles
            
        except Exception as e:
            print(f"❌ HTMLエラー {url}: {str(e)}")
            return []

    def collect_all_news(self):
        """全ニュースソースから収集"""
        print("🚀 ニュース収集開始...")
        
        # RSS対応サイト
        rss_sources = [
            'https://rss.cnn.com/rss/edition.rss',
            'https://moxie.foxnews.com/google-publisher/latest.xml',
            'https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml',
            'https://feeds.content.dowjones.io/public/rss/RSSUSnews',
            'https://feeds.feedburner.com/breitbart',
            'https://feeds.bbci.co.uk/news/rss.xml',
            'https://www.theguardian.com/world/rss',
        ]
        
        # HTML抽出サイト（RSSがない/不安定な場合）
        html_sources = [
            {
                'url': 'https://www.telegraph.co.uk/',
                'selectors': {'headlines': 'h3 a, h2 a'}
            },
            {
                'url': 'https://www.spectator.co.uk/',
                'selectors': {'headlines': 'h3 a, h2 a'}
            }
        ]
        
        all_articles = []
        
        # RSS収集
        for rss_url in rss_sources:
            articles = self.collect_from_rss(rss_url, max_articles=3)
            all_articles.extend(articles)
            time.sleep(1)  # サーバー負荷軽減
        
        # HTML収集
        for html_source in html_sources:
            articles = self.collect_from_html(
                html_source['url'], 
                html_source['selectors'], 
                max_articles=3
            )
            all_articles.extend(articles)
            time.sleep(1)  # サーバー負荷軽減
        
        # 重複除去
        seen_urls = set()
        unique_articles = []
        for article in all_articles:
            if article['url'] not in seen_urls:
                seen_urls.add(article['url'])
                unique_articles.append(article)
        
        self.articles = unique_articles
        print(f"🎉 収集完了: {len(unique_articles)}件の記事")
        
        return unique_articles

    def save_results(self):
        """結果をJSONファイルに保存"""
        output_data = {
            'collection_time': datetime.now().isoformat(),
            'total_articles': len(self.articles),
            'sources_summary': self._get_sources_summary(),
            'articles': self.articles
        }
        
        with open('news_output.json', 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 結果を保存しました: news_output.json")
        
        # サマリー表示
        print("\n📊 収集サマリー:")
        for media, count in self._get_sources_summary().items():
            print(f"  {media}: {count}件")

    def _get_sources_summary(self):
        """メディア別記事数のサマリー"""
        summary = {}
        for article in self.articles:
            media = article['media']
            summary[media] = summary.get(media, 0) + 1
        return dict(sorted(summary.items(), key=lambda x: x[1], reverse=True))

def main():
    collector = NewsCollector()
    collector.collect_all_news()
    collector.save_results()

if __name__ == "__main__":
    main()
