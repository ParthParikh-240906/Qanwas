"""Web search and content fetching for Qanwas"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import time
import config

# Try new package first, fall back to old
try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        print("[error] Please install ddgs: pip install ddgs")
        DDGS = None

def search_web(query: str, max_results: int = None) -> List[Dict]:
    """
    Search the web using DuckDuckGo (free, no API key needed)
    Returns list of dicts with 'title', 'link', 'snippet'
    """
    if max_results is None:
        max_results = config.MAX_SEARCH_RESULTS
    
    print(f"[searching web: {query}]")
    
    if DDGS is None:
        print("[error] DuckDuckGo search not available")
        return []
    
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            
            # Normalize results to have consistent keys
            normalized_results = []
            for r in results:
                normalized = {
                    'title': r.get('title', ''),
                    'link': r.get('link', r.get('href', '')),  # Handle both old and new
                    'snippet': r.get('snippet', r.get('body', r.get('description', '')))  # Handle both
                }
                # Skip results without links
                if normalized['link'] and normalized['link'].startswith('http'):
                    normalized_results.append(normalized)
            
            # Filter for trusted domains if possible
            trusted_results = [r for r in normalized_results if any(
                domain in r.get('link', '') for domain in config.TRUSTED_DOMAINS
            )]
            
            # Mix trusted + general results
            final_results = trusted_results + [r for r in normalized_results if r not in trusted_results]
            
            return final_results[:max_results]
    except Exception as e:
        print(f"[search error: {e}]")
        return []

def fetch_page_content(url: str, max_chars: int = None) -> str:
    """
    Fetch and extract readable text from a webpage
    """
    if max_chars is None:
        max_chars = config.MAX_PAGE_CHARS
    
    # Skip invalid URLs
    if not url or not url.startswith('http'):
        return ""
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, timeout=config.SEARCH_TIMEOUT, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            element.decompose()
        
        # Extract text
        text = soup.get_text(separator='\n', strip=True)
        
        # Clean up whitespace
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        text = '\n'.join(lines)
        
        return text[:max_chars]
    except Exception as e:
        print(f"[fetch error for {url}: {e}]")
        return ""

def search_and_fetch(query: str, fetch_pages: bool = True) -> List[Dict]:
    """
    Search web and optionally fetch full page content
    """
    results = search_web(query)
    
    if not fetch_pages or not results:
        return results
    
    enriched_results = []
    for result in results:
        link = result.get('link', '')
        if link:
            print(f"[fetching: {link}]")
            content = fetch_page_content(link)
        else:
            content = ""
        
        enriched_results.append({
            'title': result.get('title', ''),
            'link': link,
            'snippet': result.get('snippet', ''),
            'content': content
        })
        
        time.sleep(0.3)  # Be nice to servers
    
    return enriched_results

def build_context_from_results(results: List[Dict]) -> str:
    """
    Build a context string from search results for prompting
    """
    context_parts = []
    
    for i, result in enumerate(results, 1):
        content = result.get('content', '')
        snippet = result.get('snippet', '')
        
        # Use content if available, otherwise use snippet
        main_text = content if content else snippet
        
        context_parts.append(f"""
[Source {i}]
Title: {result.get('title', 'N/A')}
URL: {result.get('link', 'N/A')}
Snippet: {snippet}
Content: {main_text[:2000]}
""")
    
    return '\n---\n'.join(context_parts)

def format_sources(results: List[Dict]) -> str:
    """Format sources for display"""
    sources = []
    for i, result in enumerate(results, 1):
        link = result.get('link', '')
        title = result.get('title', 'N/A')
        if link:
            sources.append(f"[{i}] {title}: {link}")
        else:
            sources.append(f"[{i}] {title}")
    return '\n'.join(sources)