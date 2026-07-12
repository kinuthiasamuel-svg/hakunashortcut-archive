#!/usr/bin/env python3
"""
Verify Hakunashortcut Substack RSS feed status and search for specific posts.
"""

import argparse
import sys
from datetime import datetime
from typing import Optional, List, Dict
import xml.etree.ElementTree as ET
from urllib.request import urlopen
from urllib.error import URLError, HTTPError


class SubstackRSSVerifier:
    """Verify and parse Substack RSS feeds."""
    
    def __init__(self, feed_url: str):
        self.feed_url = feed_url
        self.feed_data = None
        self.posts = []
        self.status = {
            "feed_accessible": False,
            "feed_valid": False,
            "total_posts": 0,
            "error": None
        }
    
    def fetch_feed(self) -> bool:
        """Fetch the RSS feed from the URL."""
        try:
            print(f"📡 Fetching RSS feed from: {self.feed_url}")
            with urlopen(self.feed_url, timeout=10) as response:
                self.feed_data = response.read().decode('utf-8')
                self.status["feed_accessible"] = True
                print(f"✅ Feed accessible (HTTP {response.status})")
                return True
        except HTTPError as e:
            self.status["error"] = f"HTTP Error {e.code}: {e.reason}"
            print(f"❌ HTTP Error: {e.code} - {e.reason}")
            return False
        except URLError as e:
            self.status["error"] = f"URL Error: {e.reason}"
            print(f"❌ URL Error: {e.reason}")
            return False
        except Exception as e:
            self.status["error"] = str(e)
            print(f"❌ Error fetching feed: {e}")
            return False
    
    def parse_feed(self) -> bool:
        """Parse the RSS feed XML."""
        if not self.feed_data:
            self.status["error"] = "No feed data to parse"
            return False
        
        try:
            print("\n🔍 Parsing RSS feed...")
            root = ET.fromstring(self.feed_data)
            
            # Find all items in the feed
            items = root.findall('.//item')
            
            if not items:
                print("⚠️  No items found in feed")
                self.status["total_posts"] = 0
                return True
            
            self.status["total_posts"] = len(items)
            print(f"✅ Feed is valid XML with {len(items)} posts")
            
            # Parse each item
            for item in items:
                post = self._parse_item(item)
                if post:
                    self.posts.append(post)
            
            self.status["feed_valid"] = True
            return True
        
        except ET.ParseError as e:
            self.status["error"] = f"XML Parse Error: {e}"
            print(f"❌ XML Parse Error: {e}")
            return False
        except Exception as e:
            self.status["error"] = str(e)
            print(f"❌ Error parsing feed: {e}")
            return False
    
    def _parse_item(self, item: ET.Element) -> Optional[Dict]:
        """Parse a single RSS item/post."""
        try:
            title_elem = item.find('title')
            link_elem = item.find('link')
            pub_date_elem = item.find('pubDate')
            description_elem = item.find('description')
            
            return {
                'title': title_elem.text if title_elem is not None else 'N/A',
                'link': link_elem.text if link_elem is not None else 'N/A',
                'pub_date': pub_date_elem.text if pub_date_elem is not None else 'N/A',
                'description': description_elem.text if description_elem is not None else 'N/A',
            }
        except Exception as e:
            print(f"Warning: Could not parse item: {e}")
            return None
    
    def search_posts(self, match_string: str) -> List[Dict]:
        """Search for posts matching a string (case-insensitive)."""
        if not match_string:
            return self.posts
        
        match_lower = match_string.lower()
        matching_posts = [
            post for post in self.posts
            if match_lower in post['title'].lower() or 
               match_lower in post['description'].lower()
        ]
        return matching_posts
    
    def display_status(self):
        """Display feed status information."""
        print("\n" + "=" * 70)
        print("📊 FEED STATUS REPORT")
        print("=" * 70)
        print(f"Feed URL:          {self.feed_url}")
        print(f"Accessible:        {'✅ Yes' if self.status['feed_accessible'] else '❌ No'}")
        print(f"Valid XML:         {'✅ Yes' if self.status['feed_valid'] else '❌ No'}")
        print(f"Total Posts:       {self.status['total_posts']}")
        if self.status['error']:
            print(f"Error:             {self.status['error']}")
        print("=" * 70)
    
    def display_posts(self, posts: List[Dict], title: str = "Posts"):
        """Display posts in a formatted table."""
        if not posts:
            print(f"\n❌ No {title.lower()} found")
            return
        
        print(f"\n✅ {title}: ({len(posts)} found)")
        print("-" * 70)
        
        for i, post in enumerate(posts, 1):
            print(f"\n{i}. {post['title']}")
            print(f"   Published: {post['pub_date']}")
            print(f"   Link: {post['link']}")
            if post['description'] and post['description'] != 'N/A':
                # Truncate description to 150 chars
                desc = post['description'][:150]
                if len(post['description']) > 150:
                    desc += "..."
                print(f"   Preview: {desc}")
        
        print("-" * 70)


def main():
    parser = argparse.ArgumentParser(
        description='Verify Hakunashortcut Substack RSS feed status',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python verify_substack_rss.py
  python verify_substack_rss.py --match "Infrastructure Lens"
  python verify_substack_rss.py -m "Python" -u https://example.substack.com/feed
        """
    )
    
    parser.add_argument(
        '-u', '--url',
        default='https://hakunashortcut.substack.com/feed',
        help='Substack RSS feed URL (default: hakunashortcut)'
    )
    
    parser.add_argument(
        '-m', '--match',
        type=str,
        help='Search for posts matching this string'
    )
    
    args = parser.parse_args()
    
    # Initialize verifier
    verifier = SubstackRSSVerifier(args.url)
    
    # Fetch and parse feed
    if not verifier.fetch_feed():
        verifier.display_status()
        return 1
    
    if not verifier.parse_feed():
        verifier.display_status()
        return 1
    
    # Display status
    verifier.display_status()
    
    # Search for matching posts if requested
    if args.match:
        print(f"\n🔎 Searching for posts matching: '{args.match}'")
        matching_posts = verifier.search_posts(args.match)
        verifier.display_posts(matching_posts, f"Matching Posts ({args.match})")
    else:
        verifier.display_posts(verifier.posts, "All Posts")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
