import gradio as gr
import requests
import os
import json
import re
from dotenv import load_dotenv
from datetime import datetime
import time

# Load environment variables
load_dotenv()

class VirtualBookClub:
    def __init__(self):
        # Configuration from environment variables
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
        self.open_library_base = "https://openlibrary.org"
        
        # Environment-based configuration - OPTIMIZED FOR PHI3:MINI
        self.model = os.getenv("OLLAMA_MODEL", "phi3:mini")
        self.gradio_theme = os.getenv("GRADIO_THEME", "soft")
        
        # Rate limiting (follows guidelines best practices)
        self.last_request_time = None
        self.min_request_interval = 1.0
        
        # SPEED-OPTIMIZED TIMEOUTS for Phi3:mini
        self.OLLAMA_TIMEOUT = 30      
        self.API_TIMEOUT = 10       
        self.DESCRIPTION_TIMEOUT = 6  
        self.ANALYSIS_TIMEOUT = 120    

    def _rate_limit(self):
        """Rate limiting for API calls"""
        if self.last_request_time:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_request_interval:
                time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()

    def check_ollama_availability(self):
        """Check if Ollama is available with optimized timeout"""
        try:
            print(f"🔍 Testing Ollama connection to {self.ollama_url} with model {self.model}...")
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model,
                    "prompt": "Hello",
                    "stream": False
                },
                timeout=self.OLLAMA_TIMEOUT
            )
            
            if response.status_code == 200:
                result = response.json()
                if "response" in result:
                    print("✅ Ollama connection successful!")
                    return True, "Ollama is available and responding"
                else:
                    print("❌ Ollama responded but no response field")
                    return False, "Ollama responded but format unexpected"
            else:
                print(f"❌ Ollama returned status {response.status_code}")
                return False, f"Ollama returned status {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            print("❌ Ollama connection refused")
            return False, "Ollama server not running (connection refused)"
        except requests.exceptions.Timeout:
            print("❌ Ollama connection timed out")
            return False, f"Ollama server timeout after {self.OLLAMA_TIMEOUT} seconds"
        except Exception as e:
            print(f"❌ Ollama error: {e}")
            return False, f"Ollama error: {str(e)}"
    
    def search_books_by_genre(self, genre, limit=20):
        """Search books with more flexible filtering and source URLs"""
        # Input validation
        if not genre or not genre.strip():
            return "❌ Please enter a valid genre"
        
        # Remove emoji and clean the genre name for API search
        genre = genre.strip()
        # Remove emoji by taking everything after the first space, or the whole string if no space
        if ' ' in genre:
            genre = genre.split(' ', 1)[1].lower()
        else:
            genre = genre.lower()

        try:
            # Rate limiting
            self._rate_limit()
            
            # Search for books with the specified subject (genre)
            search_url = f"{self.open_library_base}/search.json"
            params = {
                "subject": genre,
                "limit": min(limit * 2, 40),  # Get more results to filter from
                "has_fulltext": "true",
                "language": "eng"
            }
            
            response = requests.get(search_url, params=params, timeout=self.API_TIMEOUT)
            
            if response.status_code != 200:
                return f"❌ Open Library API Error: Status code {response.status_code}"
            
            data = response.json()
            books = []
            
            for book in data.get("docs", []):
                # More flexible filtering - only require title and author
                if (book.get("title") and 
                    book.get("author_name") and 
                    book.get("first_publish_year")):
                    
                    # Create Open Library URL for the book
                    book_key = book.get("key", "")
                    book_url = f"{self.open_library_base}{book_key}" if book_key else "Not available"
                    
                    book_info = {
                        "title": book.get("title", "Unknown Title"),
                        "authors": book.get("author_name", ["Unknown Author"]),
                        "first_publish_year": book.get("first_publish_year", "Unknown"),
                        "subjects": book.get("subject", [genre]) if book.get("subject") else [genre],
                        "language": book.get("language", ["English"]),
                        "page_count": book.get("number_of_pages_median", "Unknown"),
                        "key": book_key,
                        "cover_id": book.get("cover_i"),
                        "isbn": book.get("isbn", []),
                        "publisher": book.get("publisher", ["Unknown Publisher"])[:3],
                        "rating": book.get("ratings_average", "No rating available"),
                        "description": "Description will be fetched separately",
                        "source_url": book_url,  # Add source URL
                        "search_api_url": response.url  # Add API URL used for search
                    }
                    
                    description = self.get_book_description(book_info["key"])
                    book_info["description"] = description
                    
                    books.append(book_info)
                    
                    if len(books) >= limit:
                        break
            
            if books:
                return books
            else:
                # If no books found with current search, try alternative search terms
                alternative_genres = {
                    'psychology': 'psychology',
                    'fantasy': 'fantasy fiction',
                    'self-help': 'self help',
                    'science fiction': 'science fiction',
                    'sci-fi': 'science fiction'
                }
                
                if genre in alternative_genres:
                    # Try alternative search
                    params["subject"] = alternative_genres[genre]
                    response = requests.get(search_url, params=params, timeout=self.API_TIMEOUT)
                    
                    if response.status_code == 200:
                        data = response.json()
                        for book in data.get("docs", []):
                            if (book.get("title") and 
                                book.get("author_name") and 
                                book.get("first_publish_year")):
                                
                                book_key = book.get("key", "")
                                book_url = f"{self.open_library_base}{book_key}" if book_key else "Not available"
                                
                                book_info = {
                                    "title": book.get("title", "Unknown Title"),
                                    "authors": book.get("author_name", ["Unknown Author"]),
                                    "first_publish_year": book.get("first_publish_year", "Unknown"),
                                    "subjects": [genre],
                                    "language": book.get("language", ["English"]),
                                    "page_count": book.get("number_of_pages_median", "Unknown"),
                                    "key": book_key,
                                    "cover_id": book.get("cover_i"),
                                    "isbn": book.get("isbn", []),
                                    "publisher": book.get("publisher", ["Unknown Publisher"])[:3],
                                    "rating": book.get("ratings_average", "No rating available"),
                                    "description": "Description will be fetched separately",
                                    "source_url": book_url,
                                    "search_api_url": response.url
                                }
                                
                                description = self.get_book_description(book_info["key"])
                                book_info["description"] = description
                                
                                books.append(book_info)
                                
                                if len(books) >= limit:
                                    break
                
                return books if books else f"No books found for genre '{genre}'. Try: fiction, mystery, romance, biography, history, philosophy, or literature."
            
        except requests.exceptions.Timeout:
            return "❌ Error: Request timed out. Please try again."
        except Exception as e:
            return f"❌ Error searching books: {str(e)}"
    
    def get_book_description(self, book_key):
        """Get book description with timeout"""
        try:
            if not book_key:
                return "No description available."
                
            book_url = f"{self.open_library_base}{book_key}.json"
            response = requests.get(book_url, timeout=self.DESCRIPTION_TIMEOUT)
            
            if response.status_code == 200:
                book_data = response.json()
                
                description = ""
                if isinstance(book_data.get("description"), dict):
                    description = book_data["description"].get("value", "")
                elif isinstance(book_data.get("description"), str):
                    description = book_data["description"]
                
                if description:
                    description = re.sub(r'<[^>]+>', '', description)
                    description = re.sub(r'\s+', ' ', description).strip()
                    if len(description) > 500:
                        description = description[:500] + "..."
                
                return description or "No description available."
            else:
                return "Description not available."
                
        except Exception as e:
            return "Description not available."
    
    def format_books_display(self, books, genre):
        """Format books for display in Gradio with source information"""
        if isinstance(books, str):  # Error message
            return books
        
        if not books:
            return f"No books found for genre '{genre}'."
        
        output = f"# 📚 {genre.title()} Books ({len(books)} found)\n\n"
        output += f"**Source**: Open Library API - https://openlibrary.org/search.json?subject={genre}\n\n"
        
        for i, book in enumerate(books, 1):
            output += f"## {i}. {book['title']}\n"
            
            # Authors
            authors = ", ".join(book['authors'][:3])
            if len(book['authors']) > 3:
                authors += f" and {len(book['authors']) - 3} others"
            output += f"**By:** {authors}\n\n"
            
            # Publication info
            output += f"**Published:** {book['first_publish_year']}\n"
            if book['page_count'] != "Unknown":
                output += f"**Pages:** {book['page_count']}\n"
            
            # Publishers
            if book['publisher'][0] != "Unknown Publisher":
                publishers = ", ".join(book['publisher'])
                output += f"**Publisher:** {publishers}\n"
            
            # Rating
            if isinstance(book['rating'], (int, float)):
                output += f"**Rating:** {book['rating']:.1f}/5\n"
            
            # Source URL
            if book.get('source_url') and book['source_url'] != "Not available":
                output += f"**📖 View on Open Library:** [{book['source_url']}]({book['source_url']})\n"
            
            output += "\n"
            
            # Description
            if book['description'] and book['description'] != "No description available.":
                output += f"**Description:** {book['description']}\n\n"
            
            # Subjects/Tags
            if book['subjects']:
                subjects = ", ".join(book['subjects'])
                output += f"**Subjects:** {subjects}\n\n"
            
            # Cover image (if available)
            if book['cover_id']:
                cover_url = f"https://covers.openlibrary.org/b/id/{book['cover_id']}-M.jpg"
                output += f"![Book Cover]({cover_url})\n\n"
            
            output += "---\n\n"
        
        return output

    def analyze_book_with_ollama(self, book, analysis_type="summary"):
        """Analyze book using Phi3:mini - simple working prompts"""
        if not book:
            return "❌ No book selected for analysis."
        
        print(f"🤖 Starting Phi3:mini analysis for '{book['title']}'...")
        
        # Check Ollama availability
        available, status = self.check_ollama_availability()
        if not available:
            return f"❌ Ollama Error: {status}\n\nTo fix:\n1. Open new terminal\n2. Run: ollama serve\n3. Try again"
        
        # SIMPLE WORKING PROMPTS based on successful test
        prompts = {
            "summary": f"""Analyze the book "{book['title']}" by {book['authors'][0]}. Give me:

            "summary": f"""Analyze the book "{book['title']}" by {book['authors'][0]}. Give me:
📖 **PLOT**: (2-3 sentences about the main story)
👤 **CHARACTERS**: (main character and their motivation)
🎭 **THEMES**: (key themes explored)
✍️ **STYLE**: (writing style and significance)""",

"discussion": f"""Create discussion questions for "{book['title']}" by {book['authors'][0]}. Give me:
👤 **CHARACTER QUESTION**: (about the main character)
🎭 **THEME QUESTION**: (about the main themes)
📖 **PLOT QUESTION**: (about the central conflict)
🌍 **MODERN RELEVANCE**: (how it relates to today)""",

"reading_guide": f"""Create a reading guide for "{book['title']}" by {book['authors'][0]}. Give me:
📅 **BEFORE READING**: (what to expect)
📖 **WHILE READING**: (what to watch for)
📝 **AFTER READING**: (key takeaways)
📚 **SIMILAR BOOKS**: (recommendations)""",

"recommendation": f"""Write a recommendation for "{book['title']}" by {book['authors'][0]}. Give me:
👥 **WHO SHOULD READ**: (target audience)
💡 **WHY READ**: (what makes it special)
🎯 **WHAT YOU'LL GAIN**: (benefits of reading)
📚 **SIMILAR BOOKS**: (if you like this, try...)"""


        }

        prompt = prompts.get(analysis_type, prompts["summary"])
        
        try:
            print("🔄 Sending simple request to Phi3:mini...")
            
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.6,
                        "top_p": 0.9,
                        "num_predict": 400,
                        "num_ctx": 2048

                    },

                    "keep_alive": "10m"
                },

                timeout=self.ANALYSIS_TIMEOUT  # Reduced timeout since it should be fast
            )
            
            print(f"📨 Received response with status {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                analysis = result.get("response", "No analysis generated")
                
                if analysis and len(analysis.strip()) > 10:
                    metadata = f"\n\n---\n*Generated by {self.model} on {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n*Book source: {book.get('source_url', 'Open Library')}*"
                    print("✅ Phi3:mini analysis completed successfully!")
                    return analysis + metadata
                else:
                    return "❌ Error: Empty response generated. Please try again."
            else:
                return f"❌ Error: Ollama returned status code {response.status_code}"
                
        except requests.exceptions.Timeout:
            return f"❌ Error: Analysis timed out after {self.ANALYSIS_TIMEOUT} seconds. Please try again."
        except requests.exceptions.ConnectionError:
            return "❌ Error: Cannot connect to Ollama. Please ensure Ollama is running."
        except Exception as e:
            return f"❌ Error during analysis: {str(e)}"


# Initialize the app
app = VirtualBookClub()

# Create Gradio Interface
with gr.Blocks(title="Virtual Book Club", theme=app.gradio_theme) as demo:
    gr.Markdown("""# 📚 Virtual Book Club
    
Discover books by genre and get AI-powered summaries, discussion questions, and reading guides!
    
*Powered by Open Library API and Phi3:mini AI*""")
    
    # Global state for books
    books_state = gr.State([])
    selected_book_state = gr.State(None)
    
    with gr.Row():
        # Left column: Book search and selection
        with gr.Column(scale=1):
            gr.Markdown("## 🔍 Find Books")
            
            genre_input = gr.Dropdown(
                choices=[
                    "📚 fiction", "🕵️ mystery", "💕 romance", "🚀 science fiction", "🏰 fantasy", 
                    "👤 biography", "🌍 history", "🤔 philosophy", "🧠 psychology", "💪 self-help",
                    "⚔️ adventure", "😱 thriller", "🎭 drama", "😄 comedy", "👻 horror",
                    "📝 poetry", "🎨 art", "🎵 music", "✈️ travel", "🍳 cooking", "📚 literature"
                ],
                label="Select Genre",
                value="📚 fiction",
                info="Choose a genre to explore"
            )

            search_btn = gr.Button("🔍 Search Books", variant="primary")
            
            book_selector = gr.Dropdown(
                choices=[],
                label="Select a Book",
                info="Choose a book for AI analysis",
                interactive=True,
                allow_custom_value=False
            )
            
            gr.Markdown("### 📊 Analysis Options")
            analysis_type = gr.Radio(
                choices=[
                    ("📖 Book Summary & Analysis", "summary"),
                    ("💬 Discussion Questions", "discussion"), 
                    ("📚 Reading Guide", "reading_guide"),
                    ("⭐ Reading Recommendation", "recommendation")
                ],
                label="Analysis Type",
                value="summary",
                info="Choose what type of analysis you'd like"
            )
            
            analyze_btn = gr.Button("🤖 Generate Analysis", variant="secondary")
        
        # Right column: Results display
        with gr.Column(scale=2):
            with gr.Tabs():
                with gr.Tab("📚 Book Search Results"):
                    books_display = gr.Markdown("Search for books by genre to get started!")
                
                with gr.Tab("🤖 AI Analysis"):
                    analysis_display = gr.Markdown("Select a book and analysis type, then click 'Generate Analysis'")
    
    # Status indicator
    status_display = gr.Markdown("")
    
    # Functions for Gradio interface
    def search_and_update(genre):
        """Search for books and update the interface"""
        books = app.search_books_by_genre(genre, limit=20)
        
        if isinstance(books, str):  # Error message
            return books, gr.Dropdown(choices=[]), [], None, f"❌ Search failed: {books}"
        
        # Format books display
        books_display_formatted = app.format_books_display(books, genre)
        
        # Create dropdown choices with better formatting
        book_choices = []
        for i, book in enumerate(books):
            choice = f"{i+1}. {book['title']} by {', '.join(book['authors'][:2])}"
            if len(book['authors']) > 2:
                choice += " et al."
            book_choices.append(choice)
        
        status = f"✅ Found {len(books)} books in {genre}"
        
        # Return updated dropdown with new choices
        updated_dropdown = gr.Dropdown(
            choices=book_choices,
            label="Select a Book",
            info="Choose a book for AI analysis",
            interactive=True,
            allow_custom_value=False,
            value=None  # Clear previous selection
        )
        
        return books_display_formatted, updated_dropdown, books, None, status
    
    def select_book_from_dropdown(book_choice, books):
        """Select book from dropdown with better error handling"""
        if not book_choice or not books:
            return None, "Please search for books first"
        
        try:
            # Extract book index from choice (format: "1. Title by Author")
            book_index = int(book_choice.split('.')[0]) - 1
            if 0 <= book_index < len(books):
                selected_book = books[book_index]
                status = f"📖 Selected: {selected_book['title']} by {', '.join(selected_book['authors'][:2])}"
                return selected_book, status
            else:
                return None, "❌ Invalid book selection"
        except (ValueError, IndexError, AttributeError):
            return None, "❌ Error selecting book: Please try again"
        except Exception as e:
            return None, f"❌ Error selecting book: {str(e)}"
    
    def perform_analysis(selected_book, analysis_type):
        """Perform AI analysis on selected book"""
        if not selected_book:
            return "❌ Please select a book first"
        
        analysis = app.analyze_book_with_ollama(selected_book, analysis_type)
        return analysis
    
    # Connect events
    search_btn.click(
        search_and_update,
        inputs=[genre_input],
        outputs=[books_display, book_selector, books_state, selected_book_state, status_display]
    )
    
    book_selector.change(
        select_book_from_dropdown,
        inputs=[book_selector, books_state],
        outputs=[selected_book_state, status_display]
    )
    
    analyze_btn.click(
        perform_analysis,
        inputs=[selected_book_state, analysis_type],
        outputs=[analysis_display]
    )
    
    # Add examples
    gr.Examples(
        examples=[
            ["🕵️ mystery"],
            ["🚀 science fiction"], 
            ["💕 romance"],
            ["🤔 philosophy"],
            ["👤 biography"],
            ["🏰 fantasy"],
            ["📚 literature"],
            ["🌍 history"]
        ],
        inputs=[genre_input]
    )

# Startup checks and launch
if __name__ == "__main__":
    print("=" * 50)
    print("🚀 VIRTUAL BOOK CLUB STARTUP (PHI3:MINI OPTIMIZED)")
    print("=" * 50)
    
    # Check Ollama availability at startup
    available, status = app.check_ollama_availability()
    print(f"🤖 Ollama ({app.model}): {'✅' if available else '❌'} {status}")
    
    # Check Open Library availability
    try:
        test_response = requests.get("https://openlibrary.org/search.json?subject=fiction&limit=1", timeout=5)
        if test_response.status_code == 200:
            print("📚 Open Library API: ✅ Available")
        else:
            print("📚 Open Library API: ❌ Not responding correctly")
    except:
        print("📚 Open Library API: ❌ Connection failed")
    
    print(f"🎨 Theme: {app.gradio_theme}")
    print(f"🔧 Model: {app.model}")
    print(f"⏱️ Ollama Timeout: {app.OLLAMA_TIMEOUT} seconds")
    print(f"⏱️ Analysis Timeout: {app.ANALYSIS_TIMEOUT} seconds")
    
    if not available:
        print("\n⚠️  WARNING: AI analysis won't work until Ollama is running!")
        print("💡 To fix this:")
        print("   1. Open a new terminal")
        print("   2. Run: ollama serve")
        print("   3. Refresh this application")
    else:
        print("\n✅ ALL SYSTEMS READY!")
    
    print("\n🌐 Starting Virtual Book Club interface...")
    print("=" * 50)
    
    demo.launch(share=True, server_name="0.0.0.0", server_port=7860)