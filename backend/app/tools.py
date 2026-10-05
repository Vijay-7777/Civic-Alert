import requests
import json
import re
from typing import Dict, Any, List, Optional
from .config import NEWS_API_KEY, OPENWEATHER_API_KEY, WEATHER_API_KEY
# Import RAG utilities lazily inside functions to avoid heavy deps at import time
from .db import fetch_report, list_reports

def fetch_google_news_rss(query: Optional[str] = None, country_code: str = "IN", language: str = "en") -> List[Dict[str, Any]]:
    try:
        base = "https://news.google.com/rss"
        if query:
            url = f"{base}/search?q={requests.utils.quote(query)}&hl={language}-{country_code}&gl={country_code}&ceid={country_code}:{language}"
        else:
            url = f"{base}/headlines?hl={language}-{country_code}&gl={country_code}&ceid={country_code}:{language}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CivicAlert/1.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        items: List[Dict[str, Any]] = []
        if resp.status_code == 200:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(resp.text)
            for item in root.findall('.//item')[:8]:
                title = (item.findtext('title') or '').strip()
                link = (item.findtext('link') or '').strip()
                m = re.search(r'https?://(?:www\.)?([^/]+)', link)
                source = m.group(1) if m else 'Google News'
                if title and link:
                    items.append({"title": title, "description": "", "source": source, "url": link})
        return items
    except Exception:
        return []

def get_news(query: Optional[str] = None, lat: Optional[float] = None, lon: Optional[float] = None, limit: int = 5) -> Dict[str, Any]:
    try:
        q = (query or "").strip()
        regional_terms: List[str] = []
        if lat and lon:
            nearby = get_nearby_cities(lat, lon)
            for t in nearby:
                if t and t not in regional_terms:
                    regional_terms.append(t)
        cities_bias = []
        for name in ["Bhimtal", "Nainital", "Haldwani", "Dehradun", "Uttarakhand"]:
            if q.lower().find(name.lower()) != -1:
                cities_bias.append(name)
        terms = cities_bias or regional_terms
        if terms:
            q = (q + " " + " ".join(terms)).strip()
        if not q:
            q = "Uttarakhand India latest news"

        local_tokens = ["bhimtal", "nainital", "haldwani"]
        force_local = any(t in q.lower() for t in local_tokens) or ("local" in q.lower() and terms)

        q_local = q
        if force_local:
            add = "Uttarakhand latest news"
            q_local = (q + " " + add).strip()

        items: List[Dict[str, Any]] = []
        rss_items = fetch_google_news_rss(q_local)[:limit]
        items = rss_items

        if not items:
            bias = "site:timesofindia.indiatimes.com OR site:ndtv.com OR site:hindustantimes.com OR site:indianexpress.com OR site:tribuneindia.com OR site:amarujala.com OR site:jagran.com"
            ddg = search_news_duckduckgo(f"{q_local} {bias}", max_results=limit)
            combined = ddg or []
            items = [{
                "title": a.get("title", ""),
                "description": a.get("description", ""),
                "source": a.get("source", "Web"),
                "url": a.get("url", "")
            } for a in combined if a.get("url")]

        enriched: List[Dict[str, Any]] = []
        for it in items[:limit]:
            url = it.get("url", "")
            title = it.get("title", "")
            desc = it.get("description", "")
            src = it.get("source", "Web")
            if url:
                info = extract_page_info(url)
                title = info.get("title") or title
                desc = info.get("description") or desc
                src = info.get("source") or src
            enriched.append({
                "title": title,
                "description": desc,
                "source": src,
                "url": url
            })

        return {
            "success": True if enriched else False,
            "data": enriched,
            "message": "News fetched successfully" if enriched else "No articles found"
        }
    except Exception as e:
        return {"success": False, "error": str(e), "message": "Failed to fetch news"}

def fetch_rss_generic(url: str, limit: int = 8) -> List[Dict[str, Any]]:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CivicAlert/1.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return []
        import xml.etree.ElementTree as ET
        root = ET.fromstring(resp.text)
        items: List[Dict[str, Any]] = []
        for item in root.findall('.//item')[:limit]:
            title = (item.findtext('title') or '').strip()
            link = (item.findtext('link') or '').strip()
            m = re.search(r'https?://(?:www\.)?([^/]+)', link)
            source = m.group(1) if m else 'RSS'
            if title and link:
                items.append({"title": title, "description": "", "source": source, "url": link})
        return items
    except Exception:
        return []
def reverse_geocode(lat: float, lon: float) -> Dict[str, Any]:
    """Reverse geocode coordinates to get location info"""
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
        headers = {"User-Agent": "CivicAlert/1.0"}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            address = data.get("address", {})
            
            location_info = {
                "city": address.get("city", address.get("town", address.get("village", ""))),
                "state": address.get("state", ""),
                "country": address.get("country", ""),
                "postcode": address.get("postcode", ""),
                "full_address": data.get("display_name", "")
            }
            
            return {
                "success": True,
                "data": location_info,
                "message": "Location information fetched successfully"
            }
        else:
            return {
                "success": False,
                "error": f"Geocoding API error: {response.status_code}",
                "message": "Failed to fetch location information"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to fetch location information"
        }

def get_india_news() -> Dict[str, Any]:
    """Get latest India news"""
    try:
        # Prefer NewsAPI if configured
        if NEWS_API_KEY:
            url = f"https://newsapi.org/v2/top-headlines?country=in&apiKey={NEWS_API_KEY}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                articles = data.get("articles", [])[:5]
                news_items = []
                for article in articles:
                    news_items.append({
                        "title": article.get("title", ""),
                        "description": article.get("description", ""),
                        "source": article.get("source", {}).get("name", ""),
                        "url": article.get("url", "")
                    })
                return {"success": True, "data": news_items, "message": "India news fetched successfully"}
        # Fallback: Google News RSS for India (no API key required)
        news_items = fetch_google_news_rss()
        if not news_items:
            # Try search fallback
            news_items = fetch_google_news_rss("India")
        if not news_items:
            # Try major Indian outlets RSS
            rss_candidates = [
                "https://indianexpress.com/section/india/feed/",
                "https://feeds.feedburner.com/ndtvnews-top-stories",
                "https://www.hindustantimes.com/rss/india-news",
                "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms"
            ]
            for u in rss_candidates:
                news_items = fetch_rss_generic(u, limit=8)
                if news_items:
                    break
        if news_items:
            return {"success": True, "data": news_items, "message": "India news fetched successfully (RSS)"}
        # Final fallback: web search biased to Indian outlets
        bias_query = "India news site:timesofindia.indiatimes.com OR site:hindustantimes.com OR site:indianexpress.com OR site:ndtv.com OR site:economictimes.com"
        web_articles = search_news_duckduckgo(bias_query, max_results=5) or search_news_google(bias_query, max_results=5)
        if web_articles:
            items: List[Dict[str, Any]] = []
            for a in web_articles:
                items.append({
                    "title": a.get("title", ""),
                    "description": a.get("description", ""),
                    "source": a.get("source", "Web"),
                    "url": a.get("url", "")
                })
            return {"success": True, "data": items, "message": "India news fetched via web search"}
        return {"success": False, "error": "No articles", "message": "Failed to fetch India news"}
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to fetch India news"
        }

def search_news_duckduckgo(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Search for news using DuckDuckGo search"""
    try:
        # Use DuckDuckGo instant answer API first (better for news)
        # Then fallback to HTML search
        search_query = f"{query} news"
        
        # Try instant answer API first
        instant_url = f"https://api.duckduckgo.com/?q={requests.utils.quote(search_query)}&format=json&no_html=1&skip_disambig=1"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        try:
            response = requests.get(instant_url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Check for related topics or abstract
                if data.get("AbstractText"):
                    articles = [{
                        "title": data.get("Heading", query),
                        "description": data.get("AbstractText", "")[:200],
                        "source": data.get("AbstractSource", "DuckDuckGo"),
                        "url": data.get("AbstractURL", "")
                    }]
                    if articles[0]["url"]:
                        return articles
        except:
            pass
        
        # Fallback to HTML search with better filtering
        search_url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(search_query)}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5"
        }
        
        response = requests.get(search_url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            html = response.text
            articles = []
            
            # Better parsing - look for result links
            # DuckDuckGo uses different class names, try multiple patterns
            link_patterns = [
                r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
                r'<a[^>]*class="[^"]*result[^"]*"[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
                r'<a[^>]*href="([^"]*)"[^>]*class="[^"]*result[^"]*"[^>]*>(.*?)</a>'
            ]
            
            seen_urls = set()
            query_lower = query.lower()
            
            for pattern in link_patterns:
                matches = re.finditer(pattern, html, re.DOTALL)
                for match in matches:
                    if len(articles) >= max_results:
                        break
                    
                    url = match.group(1)
                    title_html = match.group(2)
                    title = re.sub(r'<[^>]+>', '', title_html).strip()
                    
                    # Filter out non-news results
                    if not title or len(title) < 15:
                        continue
                    
                    # Skip if title doesn't seem news-related or is about LLMs/tech tutorials
                    title_lower = title.lower()
                    skip_keywords = ['raspberry pi', 'llm', 'local llm', 'tutorial', 'how to', 'guide', 'install', 'pypi', 'mcp-agent', 'show hn', 'hacker news']
                    if any(keyword in title_lower for keyword in skip_keywords):
                        continue
                    
                    
                    # Skip if we've seen this URL
                    if url in seen_urls:
                        continue
                    
                    # Validate URL
                    if not (url.startswith('http') or url.startswith('//')):
                        continue
                    
                    # Normalize URL
                    if url.startswith('//'):
                        url = 'https:' + url
                    
                    # Extract domain name as source
                    source_match = re.search(r'https?://(?:www\.)?([^/]+)', url)
                    source = source_match.group(1) if source_match else "Unknown"
                    
                    # Extract snippet if available
                    snippet = ""
                    # Look for snippet near this link
                    snippet_match = re.search(r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>', html[html.find(match.group(0)):html.find(match.group(0))+500], re.DOTALL)
                    if snippet_match:
                        snippet = re.sub(r'<[^>]+>', '', snippet_match.group(1)).strip()[:200]
                    
                    articles.append({
                        "title": title,
                        "description": snippet,
                        "source": source,
                        "url": url
                    })
                    seen_urls.add(url)
                
                if len(articles) >= max_results:
                    break
            
            return articles[:max_results]
    except Exception as e:
        print(f"DuckDuckGo search error: {str(e)}")
    
    return []

def search_news_google(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Search for news using Google search (fallback)"""
    try:
        # Use Google search with news filter
        search_url = f"https://www.google.com/search?q={query}+news&tbm=nws"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = requests.get(search_url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            html = response.text
            articles = []
            seen_urls = set()

            for m in re.finditer(r'<a[^>]+href="/url\?q=([^"]+)"[^>]*>', html):
                if len(articles) >= max_results:
                    break
                url = m.group(1)
                if not url or url in seen_urls:
                    continue
                if re.search(r'^https?://(?:www\.)?(?:google\.|policies\.google\.)', url):
                    continue
                title_segment = html[max(0, m.start()-300):min(len(html), m.end()+300)]
                tm = re.search(r'<h3[^>]*>(.*?)</h3>', title_segment, re.DOTALL)
                title = re.sub(r'<[^>]+>', '', tm.group(1)).strip() if tm else ''
                if not title or len(title) < 8:
                    continue
                sm = re.search(r'https?://(?:www\.)?([^/]+)', url)
                source = sm.group(1) if sm else 'Web'
                articles.append({"title": title, "description": "", "source": source, "url": url})
                seen_urls.add(url)
            return articles
    except Exception as e:
        print(f"Google search error: {str(e)}")
    
    return []

def extract_page_info(url: str) -> Dict[str, str]:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CivicAlert/1.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return {}
        html = resp.text
        title = ""
        desc = ""
        m = re.search(r"<meta[^>]*property=\"og:title\"[^>]*content=\"(.*?)\"", html, re.IGNORECASE)
        if m:
            title = m.group(1).strip()
        if not title:
            m = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE|re.DOTALL)
            if m:
                title = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        m = re.search(r"<meta[^>]*name=\"description\"[^>]*content=\"(.*?)\"", html, re.IGNORECASE)
        if m:
            desc = m.group(1).strip()
        if not desc:
            m = re.search(r"<meta[^>]*property=\"og:description\"[^>]*content=\"(.*?)\"", html, re.IGNORECASE)
            if m:
                desc = m.group(1).strip()
        sm = re.search(r"https?://(?:www\.)?([^/]+)", url)
        src = sm.group(1) if sm else "Web"
        return {"title": title, "description": desc, "source": src}
    except:
        return {}

def get_nearby_cities(lat: float, lon: float, radius_km: float = 50) -> List[str]:
    """Get nearby cities within a radius using reverse geocoding"""
    try:
        # Use Nominatim to search for nearby places
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&zoom=10"
        headers = {"User-Agent": "CivicAlert/1.0"}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            address = data.get("address", {})
            
            # Get state/district for broader search
            state = address.get("state", "")
            district = address.get("state_district", "")
            region = address.get("region", "")
            
            nearby_cities = []
            if state:
                nearby_cities.append(state)
            if district:
                nearby_cities.append(district)
            if region:
                nearby_cities.append(region)
            
            return nearby_cities
    except:
        pass
    return []

def get_local_news(city: str, lat: Optional[float] = None, lon: Optional[float] = None, try_neighbors: bool = True) -> Dict[str, Any]:
    """Get local news for a specific city, with fallback to neighboring areas and web search"""
    try:
        # If no News API key, use web search directly
        if not NEWS_API_KEY:
            print(f"No News API key, using web search for {city}...")
            # Try Google News RSS search first for Indian region
            rss_articles = fetch_google_news_rss(f"{city} India")
            web_articles = []
            if rss_articles:
                web_articles = rss_articles
            else:
                qualifier = " India"
                query_city = f"{city}{qualifier} news"
                web_articles = search_news_duckduckgo(query_city, max_results=5)
                if not web_articles:
                    web_articles = search_news_google(query_city, max_results=5)
            if web_articles:
                news_items: List[Dict[str, Any]] = []
                for article in web_articles:
                    news_items.append({
                        "title": article.get("title", ""),
                        "description": article.get("description", ""),
                        "source": article.get("source", "Web"),
                        "url": article.get("url", ""),
                        "location": city
                    })
                return {
                    "success": True,
                    "data": news_items,
                    "message": f"Found news for {city} via web search"
                }
            return {
                "success": False,
                "error": "News API key not configured",
                "message": "News API key is not set and web search didn't return results. Please configure NEWS_API_KEY in your environment variables."
            }
        
        # Try multiple search strategies with location-specific queries
        search_queries = [
            f"{city} news",  # City with "news" keyword (most specific)
            f"{city} latest news",  # City with "latest news"
            f"{city} breaking news",  # City with "breaking news"
            city,  # Direct city name
        ]
        
        # Add state/region if available for broader search
        state = None
        if lat and lon:
            location_result = reverse_geocode(lat, lon)
            if location_result.get("success"):
                state = location_result["data"].get("state", "")
                if state and state.lower() != city.lower():
                    search_queries.append(f"{state} news")
                    search_queries.append(f"{city} {state} news")
        
        # If we have coordinates, try to get state/region for broader search
        if lat and lon and try_neighbors:
            nearby_areas = get_nearby_cities(lat, lon)
            for area in nearby_areas:
                if area and area.lower() != city.lower():
                    search_queries.append(area)
                    search_queries.append(f"{area} news")
        
        all_articles = []
        tried_queries = []
        
        # Try each search query
        for query in search_queries:
            if query in tried_queries:
                continue
            tried_queries.append(query)
            
            try:
                # Bias queries toward Indian sources
                sources_bias = "(timesofindia OR hindustantimes OR indianexpress OR ndtv OR economictimes OR thehindu)"
                q = f"{query} {sources_bias}"
                url = f"https://newsapi.org/v2/everything?q={q}&apiKey={NEWS_API_KEY}&sortBy=publishedAt&language=en&pageSize=10"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    articles = data.get("articles", [])
                    
                    # Filter out articles with no title or description
                    valid_articles = [a for a in articles if a.get("title") and a.get("title") != "[Removed]"]
                    
                    # Add source location info to articles
                    for article in valid_articles:
                        article['_search_query'] = query
                        all_articles.append(article)
                    
                    # If we found enough articles from primary city, break
                    if query == city and len(valid_articles) >= 3:
                        break
            except:
                continue
        
        # Remove duplicates based on title
        seen_titles = set()
        unique_articles = []
        for article in all_articles:
            title = article.get("title", "").lower()
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_articles.append(article)
        
        # Limit to 5 articles, prioritizing primary city results
        primary_city_articles = [a for a in unique_articles if a.get('_search_query') == city]
        other_articles = [a for a in unique_articles if a.get('_search_query') != city]
        
        news_items = []
        # Add primary city articles first
        for article in primary_city_articles[:5]:
            news_items.append({
                "title": article.get("title", ""),
                "description": article.get("description", ""),
                "source": article.get("source", {}).get("name", ""),
                "url": article.get("url", ""),
                "location": article.get('_search_query', city)
            })
        
        # Fill remaining slots with other articles
        remaining = 5 - len(news_items)
        for article in other_articles[:remaining]:
            news_items.append({
                "title": article.get("title", ""),
                "description": article.get("description", ""),
                "source": article.get("source", {}).get("name", ""),
                "url": article.get("url", ""),
                "location": article.get('_search_query', 'nearby area')
            })
        
        if len(news_items) == 0:
            # Last resort: try broader search with state/region
            if lat and lon:
                location_result = reverse_geocode(lat, lon)
                if location_result.get("success"):
                    state = location_result["data"].get("state", "")
                    if state and state.lower() != city.lower():
                        return get_local_news(state, lat, lon, try_neighbors=False)
            
            # If News API failed, try DuckDuckGo/Google search
            print(f"No results from News API for {city}, trying web search...")
            web_articles = search_news_duckduckgo(f"{city} news", max_results=5)
            
            if not web_articles:
                # Try Google as fallback
                web_articles = search_news_google(f"{city} news", max_results=5)
            
            if web_articles:
                news_items = []
                for article in web_articles:
                    news_items.append({
                        "title": article.get("title", ""),
                        "description": article.get("description", ""),
                        "source": article.get("source", "Web"),
                        "url": article.get("url", ""),
                        "location": city
                    })
                
                return {
                    "success": True,
                    "data": news_items,
                    "message": f"Found news for {city} via web search"
                }
            
            return {
                "success": False,
                "error": "No articles found",
                "message": f"Couldn't find any recent news articles for {city} or nearby areas. The location might be too small or there might be no recent news coverage."
            }
        
        # Determine message based on whether we found primary city news or nearby news
        if any(item.get("location") == city for item in news_items):
            message = f"Local news for {city} fetched successfully"
        else:
            message = f"Found news from nearby areas (no specific news for {city})"
        
        return {
            "success": True,
            "data": news_items,
            "message": message
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to fetch local news for {city}: {str(e)}"
        }

def get_weather(lat: float, lon: float) -> Dict[str, Any]:
    """Get weather for given coordinates"""
    try:
        url = f"https://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={lat},{lon}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            weather_info = {
                "temperature": data["current"]["temp_c"],
                "feels_like": data["current"]["feelslike_c"],
                "humidity": data["current"]["humidity"],
                "description": data["current"]["condition"]["text"],
                "city": data["location"]["name"],
                "country": data["location"]["country"]
            }
            
            return {
                "success": True,
                "data": weather_info,
                "message": "Weather information fetched successfully"
            }
        else:
            return {
                "success": False,
                "error": f"Weather API error: {response.status_code}",
                "message": "Failed to fetch weather information"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to fetch weather information"
        }

def geocode_location(location_name: str) -> Dict[str, Any]:
    """Geocode a location name to get coordinates"""
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={location_name}&format=json&limit=1"
        headers = {"User-Agent": "CivicAlert/1.0"}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                location = data[0]
                location_info = {
                    "lat": float(location.get("lat", 0)),
                    "lon": float(location.get("lon", 0)),
                    "display_name": location.get("display_name", location_name),
                    "city": location.get("address", {}).get("city", location.get("address", {}).get("town", location_name))
                }
                
                return {
                    "success": True,
                    "data": location_info,
                    "message": f"Location '{location_name}' found successfully"
                }
            else:
                return {
                    "success": False,
                    "error": "Location not found",
                    "message": f"Could not find location '{location_name}'"
                }
        else:
            return {
                "success": False,
                "error": f"Geocoding API error: {response.status_code}",
                "message": "Failed to geocode location"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to geocode location: {str(e)}"
        }

def rag_local_issues(query: str, lat: Optional[float] = None, lon: Optional[float] = None) -> Dict[str, Any]:
    """Search local issues using RAG"""
    try:
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"rag_local_issues called: query='{query}', lat={lat}, lon={lon}")
        # Lazy import to avoid sentence-transformers dependency unless needed
        from .rag import search_local_issues
        from .db import list_reports
        # If coordinates provided, add location context to query
        if lat and lon:
            location_result = reverse_geocode(lat, lon)
            if location_result["success"]:
                d = location_result["data"]
                names = []
                for k in ["city", "town", "village", "suburb"]:
                    v = str(d.get(k) or "").strip()
                    if v:
                        names.append(v)
                disp = str(d.get("display_name") or "")
                if disp:
                    # Prefer explicit Bhimtal mention if present in display name
                    if "bhimtal" in disp.lower():
                        names.append("Bhimtal")
                # Deduplicate while preserving order
                seen = set()
                area = " ".join([x for x in names if not (x in seen or seen.add(x))])
                enhanced_query = f"{query} in {area}" if area else query
            else:
                enhanced_query = query
            logger.info(f"rag_local_issues enhanced_query='{enhanced_query}'")
        else:
            enhanced_query = query

        # Enrich query with nearby location tokens from existing reports
        try:
            nearby_tokens: List[str] = []
            if lat and lon:
                try:
                    reps = list_reports({})
                    def _near(r):
                        try:
                            rl = float(r.get("latitude") or 0.0)
                            ro = float(r.get("longitude") or 0.0)
                            if rl == 0.0 and ro == 0.0:
                                return False
                            from math import radians, sin, cos, sqrt, atan2
                            R = 6371.0
                            dlat = radians(rl - lat)
                            dlon = radians(ro - lon)
                            a = sin(dlat/2)**2 + cos(radians(lat))*cos(radians(rl))*sin(dlon/2)**2
                            c = 2*atan2(sqrt(a), sqrt(1-a))
                            return (R*c) <= 30.0
                        except:
                            return False
                    content_tokens: List[str] = []
                    for r in reps:
                        if _near(r):
                            locs = str(r.get("location") or "").lower()
                            for tok in re.findall(r"[A-Za-z]{4,}", locs):
                                if tok not in nearby_tokens:
                                    nearby_tokens.append(tok)
                            title = str(r.get("title") or "").lower()
                            desc = str(r.get("description") or "").lower()
                            for tok in re.findall(r"[A-Za-z]{4,}", title + " " + desc):
                                content_tokens.append(tok)
                    if nearby_tokens:
                        key_terms = []
                        for t in nearby_tokens:
                            if t in ("india", "highway", "office", "chief", "resorts"):
                                continue
                            key_terms.append(t)
                        if key_terms:
                            enhanced_query = f"{enhanced_query} {' '.join(key_terms[:3])}"
                        # If query is generic, boost with domain keywords from nearby reports
                        q_tokens = [t.lower() for t in re.findall(r"[A-Za-z]{3,}", query or "")]
                        generic_set = {"issues", "issue", "near", "local", "here", "around", "me"}
                        if (not query) or all(t in generic_set for t in q_tokens):
                            domain = ["pothole", "garbage", "leakage", "road", "damage", "water", "accident"]
                            boosts = []
                            seenb = set()
                            for tok in content_tokens:
                                if tok in domain and tok not in seenb:
                                    boosts.append(tok)
                                    seenb.add(tok)
                            if boosts:
                                enhanced_query = f"{enhanced_query} {' '.join(boosts[:3])}"
                except Exception:
                    pass
        except Exception:
            pass

        # Search issues
        try:
            issues = search_local_issues(enhanced_query, limit=10)
        except Exception:
            issues = []
        if not issues:
            area_terms: List[str] = []
            if lat and lon:
                loc = reverse_geocode(lat, lon)
                if loc.get("success"):
                    d = loc["data"]
                    for k in ["city", "state", "region"]:
                        v = d.get(k)
                        if v:
                            area_terms.append(v.lower())
            q_tokens = [t.lower() for t in re.findall(r"[A-Za-z]{3,}", query or "")]
            generic_set = {"issues", "issue", "near", "local", "here", "around", "me"}
            generic_query = (not query) or all(t in generic_set for t in q_tokens)
            reports = list_reports({})
            def near(r):
                try:
                    if lat is None or lon is None:
                        return True
                    rl = float(r.get("latitude") or 0.0)
                    ro = float(r.get("longitude") or 0.0)
                    if rl == 0.0 and ro == 0.0:
                        return False
                    from math import radians, sin, cos, sqrt, atan2
                    R = 6371.0
                    dlat = radians(rl - lat)
                    dlon = radians(ro - lon)
                    a = sin(dlat/2)**2 + cos(radians(lat))*cos(radians(rl))*sin(dlon/2)**2
                    c = 2*atan2(sqrt(a), sqrt(1-a))
                    return (R*c) <= 30.0
                except:
                    return False
            fallback: List[Dict[str, Any]] = []
            for r in reports:
                title = str(r.get("title") or "").lower()
                desc = str(r.get("description") or "").lower()
                locs = str(r.get("location") or "").lower()
                if area_terms and not any(t in locs for t in area_terms):
                    if lat and lon and not near(r):
                        continue
                if (not generic_query) and q_tokens and not any(t in title or t in desc for t in q_tokens):
                    continue
                fallback.append({
                    "id": r.get("reportId") or r.get("id"),
                    "title": r.get("title"),
                    "description": r.get("description"),
                    "location": r.get("location"),
                    "latitude": r.get("latitude"),
                    "longitude": r.get("longitude"),
                })
            if lat and lon and fallback:
                def _dist(i):
                    try:
                        rl = float(i.get("latitude") or 0.0)
                        ro = float(i.get("longitude") or 0.0)
                        if rl == 0.0 and ro == 0.0:
                            return 1e9
                        from math import radians, sin, cos, sqrt, atan2
                        R = 6371.0
                        dlat = radians(rl - lat)
                        dlon = radians(ro - lon)
                        a = sin(dlat/2)**2 + cos(radians(lat))*cos(radians(rl))*sin(dlon/2)**2
                        c = 2*atan2(sqrt(a), sqrt(1-a))
                        return R*c
                    except:
                        return 1e9
                fallback = sorted(fallback, key=_dist)
            logger.info(f"rag_local_issues using fallback count={len(fallback)}")
            issues = fallback[:10]
        else:
            logger.info(f"rag_local_issues vector result count={len(issues)}")

        # Remove Bengaluru/Bangalore/Koramangala entries from final results
        try:
            def _allow(i):
                loc = str(i.get("location") or "").lower()
                return not any(k in loc for k in ("bengaluru", "bangalore", "koramangala"))
            filtered = [i for i in issues if _allow(i)]
            if len(filtered) != len(issues):
                logger.info(f"rag_local_issues filtered out {len(issues)-len(filtered)} Bengaluru items")
            issues = filtered
        except Exception:
            pass

        try:
            preview = []
            for i in issues[:3]:
                t = str(i.get("title") or i.get("description") or "")
                s = i.get("score")
                if s is not None:
                    preview.append(f"{t[:60]} (score={s:.3f})")
                else:
                    preview.append(t[:60])
            logger.info("rag_local_issues preview: " + "; ".join(preview))
        except Exception:
            pass

        return {
            "success": True,
            "data": issues,
            "message": f"Found {len(issues)} local issues"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to search local issues"
        }

def track_report(report_id: str) -> Dict[str, Any]:
    """Track a specific report by ID (supports both numeric and UUID formats)"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"track_report called with report_id: {report_id}")
        
        if not report_id:
            error_msg = "No report ID provided"
            logger.error(error_msg)
            return {
                "success": False,
                "error": "missing_report_id",
                "message": "No report ID provided. Please provide a valid report ID."
            }
            
        # Ensure report_id is a string and normalize variants
        original_report_id = str(report_id).strip()
        # Preserve dashes (common in UUIDs); also build a no-dash variant to try
        cleaned_id = ''.join(c for c in original_report_id if c.isalnum() or c == '-')
        no_dash_id = cleaned_id.replace('-', '')
        
        logger.info(f"Looking up report. original: {original_report_id} cleaned: {cleaned_id} no-dash: {no_dash_id}")
        
        # Try in order: original, cleaned, no-dash
        report = fetch_report(original_report_id) or fetch_report(cleaned_id) or fetch_report(no_dash_id)
        
        if not report:
            # Also try numeric ID if applicable
            if original_report_id.isdigit():
                logger.info(f"Trying with numeric ID: {original_report_id}")
                report = fetch_report(original_report_id)
                
            if not report:
                error_msg = f"Report {original_report_id} not found in database"
                logger.warning(error_msg)
                return {
                    "success": False,
                    "error": "report_not_found",
                    "message": f"Report {original_report_id} not found. Please check the report ID and try again.",
                    "suggestions": [
                        "Make sure you entered the correct report ID",
                        "Check for any typos in the report ID",
                        "If you just submitted the report, please wait a moment and try again"
                    ]
                }
            
        logger.info(f"Found report: {report.get('reportId')} - {report.get('title')}")
        
        # Get status with fallback to 'pending' if not set
        status = str(report.get("status", "pending")).lower()
        
        # Format the response to include all necessary fields
        response = {
            "success": True,
            "data": {
                "id": str(report.get("id", "")),
                "reportId": str(report.get("reportId", cleaned_id)),
                "type": str(report.get("type", "unknown")),
                "title": str(report.get("title", "No title")),
                "description": str(report.get("description", "No description")),
                "status": status,
                "createdAt": str(report.get("createdAt", "Unknown date")),
                "location": {
                    "name": str(report.get("location", "Unknown location")),
                    "lat": report.get("latitude"),
                    "lon": report.get("longitude")
                },
                "reporter": {
                    "name": str(report.get("reporterName", "Anonymous")),
                    "email": report.get("reporterEmail"),
                    "phone": report.get("reporterPhone")
                },
                "department": {
                    "id": report.get("departmentId"),
                    "name": str(report.get("departmentName", "No department assigned"))
                }
            },
            "message": f"Report {report.get('reportId', cleaned_id)} found"
        }
        
        logger.debug(f"Returning response: {response}")
        return response
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Error in track_report: {error_trace}")
        
        error_details = {
            "success": False,
            "error": "server_error",
            "message": "An error occurred while processing your request. Please try again later.",
            "details": {
                "report_id": original_report_id if 'original_report_id' in locals() else 'unknown',
                "error_type": type(e).__name__,
                "error_message": str(e)
            }
        }
        
        logger.error(f"Error details: {error_details}")
        return error_details
