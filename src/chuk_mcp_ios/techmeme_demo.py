#!/usr/bin/env python3
"""
Techmeme News Demo for iOS Simulator
Fetches current tech news from Techmeme and displays it in iOS Safari with screenshots.
"""

import subprocess
import json
import time
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import quote_plus

class TechmemeNewsDemo:
    """Demo that fetches Techmeme news and displays it in iOS simulator."""
    
    def __init__(self):
        self.simctl_path = "xcrun simctl"
        self.session_udid = None
        self.news_data = []
        self.output_dir = "techmeme_demo"
        
    def run_command(self, command: str, timeout: Optional[int] = None) -> subprocess.CompletedProcess:
        """Execute a shell command and return the result."""
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                check=True,
                timeout=timeout
            )
            return result
        except subprocess.CalledProcessError as e:
            print(f"Error executing command: {command}")
            print(f"Error: {e.stderr}")
            raise e
    
    def setup_output_directory(self):
        """Create output directory for screenshots and data."""
        os.makedirs(self.output_dir, exist_ok=True)
        print(f"📁 Output directory: {self.output_dir}")
    
    def fetch_techmeme_news(self) -> List[Dict[str, str]]:
        """Fetch current news headlines from Techmeme."""
        print("📰 Fetching current tech news from Techmeme...")
        
        try:
            # Fetch Techmeme homepage
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get('https://www.techmeme.com/', headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            news_items = []
            
            # Try multiple selectors to find stories
            selectors = [
                'div.item',  # Main story containers
                'div.ii',    # Alternative story containers
                'div.rhov'   # River items
            ]
            
            for selector in selectors:
                items = soup.select(selector)
                if items:
                    print(f"✅ Found {len(items)} items using selector: {selector}")
                    break
            
            for item in items[:15]:  # Get more stories to have options
                try:
                    # Try different headline selectors
                    headline_elem = (item.find('a', class_='ourh') or 
                                   item.find('a', href=True) or
                                   item.find('strong'))
                    
                    if not headline_elem:
                        continue
                    
                    headline = headline_elem.get_text(strip=True)
                    if len(headline) < 10:  # Skip very short headlines
                        continue
                    
                    link = headline_elem.get('href', '')
                    
                    # Make URL absolute
                    if link.startswith('/'):
                        link = 'https://www.techmeme.com' + link
                    elif not link.startswith('http'):
                        continue  # Skip invalid links
                    
                    # Extract source/domain if available
                    source_elem = item.find('cite') or item.find('span', class_='src')
                    source = source_elem.get_text(strip=True) if source_elem else 'Tech News'
                    
                    # Extract snippet if available
                    snippet_elem = item.find('div', class_='itemt') or item.find('p')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else headline
                    
                    # Clean up snippet
                    snippet = snippet[:200] + '...' if len(snippet) > 200 else snippet
                    
                    news_items.append({
                        'headline': headline,
                        'link': link,
                        'source': source,
                        'snippet': snippet,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                except Exception as e:
                    print(f"Warning: Failed to parse news item: {e}")
                    continue
            
            # Remove duplicates based on headline
            seen_headlines = set()
            unique_items = []
            for item in news_items:
                if item['headline'] not in seen_headlines:
                    seen_headlines.add(item['headline'])
                    unique_items.append(item)
            
            news_items = unique_items[:10]  # Take top 10 unique stories
            
            if news_items:
                print(f"✅ Successfully parsed {len(news_items)} news stories from Techmeme")
                return news_items
            else:
                print("⚠️  No news items found, using sample news...")
                return self.get_sample_news()
            
        except Exception as e:
            print(f"❌ Failed to fetch Techmeme news: {e}")
            print("Using sample news instead...")
            return self.get_sample_news()
    
    def get_sample_news(self) -> List[Dict[str, str]]:
        """Get sample tech news if fetching fails."""
        return [
            {
                'headline': 'Apple Vision Pro gets new developer tools and spatial computing features',
                'link': 'https://developer.apple.com/',
                'source': 'Apple Developer',
                'snippet': 'Apple announces new APIs and frameworks for spatial computing development, including enhanced hand tracking and eye tracking capabilities for Vision Pro applications.',
                'timestamp': datetime.now().isoformat()
            },
            {
                'headline': 'OpenAI releases GPT-4 Turbo with improved reasoning and lower costs',
                'link': 'https://openai.com/',
                'source': 'OpenAI',
                'snippet': 'The latest model offers 50% cost reduction while maintaining high performance, with new capabilities for multimodal input processing.',
                'timestamp': datetime.now().isoformat()
            },
            {
                'headline': 'Meta announces Quest 3 VR headset with mixed reality capabilities',
                'link': 'https://www.meta.com/',
                'source': 'Meta',
                'snippet': 'The new Quest 3 features improved passthrough technology and enhanced graphics processing for immersive mixed reality experiences.',
                'timestamp': datetime.now().isoformat()
            },
            {
                'headline': 'Google unveils Gemini AI model with multimodal capabilities',
                'link': 'https://deepmind.google/',
                'source': 'Google DeepMind',
                'snippet': 'Gemini can process text, images, audio, and video simultaneously, representing a significant advance in AI model architecture.',
                'timestamp': datetime.now().isoformat()
            },
            {
                'headline': 'Tesla Full Self-Driving beta expands to new regions',
                'link': 'https://www.tesla.com/',
                'source': 'Tesla',
                'snippet': 'The FSD beta is now available in additional markets, with improved neural network performance and reduced intervention rates.',
                'timestamp': datetime.now().isoformat()
            },
            {
                'headline': 'Microsoft Copilot integrates with Windows 11 for enhanced productivity',
                'link': 'https://www.microsoft.com/',
                'source': 'Microsoft',
                'snippet': 'The AI assistant is now deeply integrated into the Windows experience, offering contextual help and automation across applications.',
                'timestamp': datetime.now().isoformat()
            }
        ]
    
    def save_news_data(self, news_items: List[Dict[str, str]]):
        """Save news data to JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        news_file = os.path.join(self.output_dir, f"techmeme_news_{timestamp}.json")
        
        data = {
            'fetch_time': datetime.now().isoformat(),
            'source': 'Techmeme.com',
            'total_stories': len(news_items),
            'stories': news_items
        }
        
        with open(news_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"💾 News data saved: {news_file}")
        return news_file
    
    def setup_simulator(self) -> str:
        """Set up and boot an iOS simulator."""
        print("📱 Setting up iOS simulator...")
        
        # Get available simulators
        result = self.run_command(f"{self.simctl_path} list devices --json")
        data = json.loads(result.stdout)
        
        # Find an iPhone simulator
        for runtime_name, devices in data['devices'].items():
            for device in devices:
                if ('iPhone' in device['name'] and 
                    device.get('isAvailable', True) and
                    'iOS' in runtime_name):
                    
                    udid = device['udid']
                    name = device['name']
                    state = device['state']
                    
                    print(f"📱 Selected: {name} ({udid[:8]}...)")
                    
                    # Boot if not already booted
                    if state != 'Booted':
                        print("🚀 Booting simulator...")
                        self.run_command(f"{self.simctl_path} boot {udid}")
                        
                        # Wait for boot
                        for i in range(30):
                            time.sleep(1)
                            check_result = self.run_command(f"{self.simctl_path} list devices --json")
                            check_data = json.loads(check_result.stdout)
                            
                            for rt, devs in check_data['devices'].items():
                                for dev in devs:
                                    if dev['udid'] == udid and dev['state'] == 'Booted':
                                        print("✅ Simulator booted successfully")
                                        time.sleep(3)  # Allow full initialization
                                        return udid
                        
                        raise Exception("Timeout waiting for simulator to boot")
                    else:
                        print("✅ Simulator already booted")
                        return udid
        
        raise Exception("No suitable iPhone simulator found")
    
    def take_screenshot(self, filename: str, description: str = ""):
        """Take a screenshot of the current simulator state."""
        if not self.session_udid:
            raise Exception("No simulator session available")
        
        filepath = os.path.join(self.output_dir, filename)
        self.run_command(f"{self.simctl_path} io {self.session_udid} screenshot '{filepath}'")
        
        desc_text = f" - {description}" if description else ""
        print(f"📸 Screenshot saved: {filename}{desc_text}")
        return filepath
    
    def open_url_in_safari(self, url: str, wait_time: int = 3):
        """Open a URL in Safari and wait for it to load."""
        print(f"🔗 Opening in Safari: {url}")
        self.run_command(f"{self.simctl_path} openurl {self.session_udid} '{url}'")
        time.sleep(wait_time)
    
    def create_news_summary_page(self, news_items: List[Dict[str, str]]) -> str:
        """Create a simple HTML page with news summaries."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tech News Summary - {timestamp}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 20px;
            background-color: #f5f5f7;
            color: #1d1d1f;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
        }}
        .news-item {{
            background: white;
            margin: 15px 0;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .headline {{
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
            color: #1d1d1f;
        }}
        .source {{
            color: #6e6e73;
            font-size: 14px;
            margin-bottom: 8px;
        }}
        .snippet {{
            color: #424245;
            line-height: 1.4;
            margin-bottom: 10px;
        }}
        .read-more {{
            color: #007aff;
            text-decoration: none;
            font-weight: 500;
        }}
        .timestamp {{
            color: #8e8e93;
            font-size: 12px;
            text-align: center;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📰 Tech News Summary</h1>
        <p>Latest from Techmeme.com</p>
        <p>Updated: {timestamp}</p>
    </div>
    
    <div class="news-container">
"""
        
        for i, item in enumerate(news_items, 1):
            html_content += f"""
        <div class="news-item">
            <div class="headline">{i}. {item['headline']}</div>
            <div class="source">Source: {item['source']}</div>
            <div class="snippet">{item['snippet']}</div>
            <a href="{item['link']}" class="read-more">Read full story →</a>
        </div>
"""
        
        html_content += f"""
    </div>
    
    <div class="timestamp">
        Generated on {timestamp} | Total stories: {len(news_items)}
    </div>
</body>
</html>
"""
        
        # Save HTML file
        html_file = os.path.join(self.output_dir, "techmeme_summary.html")
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Create file:// URL for local access
        file_url = f"file://{os.path.abspath(html_file)}"
        print(f"📄 News summary page created: {html_file}")
        return file_url
    
    def run_demo(self):
        """Run the complete Techmeme news demo."""
        print("🍎 Techmeme News Demo for iOS Simulator")
        print("=" * 50)
        
        try:
            # Setup
            self.setup_output_directory()
            
            # Fetch news
            self.news_data = self.fetch_techmeme_news()
            
            # Save news data
            self.save_news_data(self.news_data)
            
            # Setup simulator
            self.session_udid = self.setup_simulator()
            
            # Take initial screenshot
            self.take_screenshot("01_home_screen.png", "Home screen")
            
            # Create local news summary page
            summary_url = self.create_news_summary_page(self.news_data)
            
            # Open news summary in Safari
            print("\n📰 Displaying news summary...")
            self.open_url_in_safari(summary_url, wait_time=4)
            self.take_screenshot("02_news_summary.png", "Local news summary page")
            
            # Open actual Techmeme website
            print("\n🌐 Opening Techmeme website...")
            self.open_url_in_safari("https://www.techmeme.com/", wait_time=5)
            self.take_screenshot("03_techmeme_website.png", "Techmeme.com homepage")
            
            # Demonstrate news story access
            print("\n📖 Opening individual news stories...")
            for i, story in enumerate(self.news_data[:3]):  # Open first 3 stories
                print(f"   Opening story {i+1}: {story['headline'][:50]}...")
                self.open_url_in_safari(story['link'], wait_time=4)
                filename = f"04_story_{i+1}.png"
                self.take_screenshot(filename, f"Story {i+1}: {story['source']}")
                time.sleep(1)
            
            # Return to home screen using a more reliable method
            print("\n🏠 Returning to home screen...")
            try:
                # Method 1: Try pressing home button
                self.run_command(f"{self.simctl_path} device {self.session_udid} simulate_hardware_keyboard home")
            except:
                try:
                    # Method 2: Try opening another app then home
                    self.run_command(f"{self.simctl_path} launch {self.session_udid} com.apple.mobilesafari")
                    time.sleep(1)
                except:
                    print("⚠️  Could not return to home screen, continuing...")
            
            time.sleep(2)
            self.take_screenshot("05_final_state.png", "Final state")
            
            # Generate report
            self.generate_demo_report()
            
            print(f"\n✅ Demo completed successfully!")
            print(f"📁 All files saved in: {self.output_dir}/")
            self.print_summary()
            
        except Exception as e:
            print(f"\n❌ Demo failed: {e}")
            if self.session_udid:
                try:
                    self.take_screenshot("error_screenshot.png", "Error state")
                except:
                    pass
            raise
    
    def generate_demo_report(self):
        """Generate a summary report of the demo."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(self.output_dir, f"demo_report_{timestamp}.json")
        
        # Count generated files
        screenshots = [f for f in os.listdir(self.output_dir) if f.endswith('.png')]
        
        report = {
            'demo_info': {
                'name': 'Techmeme News Demo',
                'timestamp': datetime.now().isoformat(),
                'simulator_udid': self.session_udid,
                'status': 'completed'
            },
            'news_data': {
                'total_stories': len(self.news_data),
                'stories_accessed': min(3, len(self.news_data)),
                'source': 'Techmeme.com'
            },
            'generated_files': {
                'screenshots': len(screenshots),
                'html_files': 1,
                'json_files': 1,
                'total_files': len(os.listdir(self.output_dir))
            },
            'screenshots_taken': screenshots
        }
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📊 Demo report generated: {report_file}")
    
    def print_summary(self):
        """Print a summary of the demo results."""
        print(f"\n📊 Demo Summary:")
        print(f"   📰 News stories fetched: {len(self.news_data)}")
        print(f"   📸 Screenshots taken: {len([f for f in os.listdir(self.output_dir) if f.endswith('.png')])}")
        print(f"   📱 Simulator used: {self.session_udid[:8] if self.session_udid else 'N/A'}...")
        print(f"   📁 Output directory: {self.output_dir}")
        
        print(f"\n📰 Top Stories:")
        for i, story in enumerate(self.news_data[:5], 1):
            print(f"   {i}. {story['headline'][:60]}...")
            print(f"      Source: {story['source']}")

def main():
    """Main entry point."""
    import sys
    
    # Check if we're in quiet mode
    quiet_mode = '--quiet' in sys.argv
    
    if not quiet_mode:
        print("📰 Techmeme News Demo")
        print("This demo fetches current tech news and displays it in iOS Safari")
        print()
        
        response = input("Start demo? (Y/n): ").strip().lower()
        if response not in ['', 'y', 'yes']:
            print("Demo cancelled")
            return
    
    try:
        demo = TechmemeNewsDemo()
        demo.run_demo()
        
        if not quiet_mode:
            # Ask about cleanup
            response = input(f"\n🗑️  Keep simulator running? (Y/n): ").strip().lower()
            if response in ['n', 'no']:
                if demo.session_udid:
                    demo.run_command(f"{demo.simctl_path} shutdown {demo.session_udid}")
                    print("✅ Simulator shutdown")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()