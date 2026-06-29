from flask import Flask, render_template, request, jsonify
import requests
import re
import json
import pandas as pd
import os
from fuzzywuzzy import fuzz

app = Flask(__name__)

# TechSpecs API Configuration
TECHSPECS_API_KEY = "3be24c26-938e-4507-bb01-5a96f838b661"
TECHSPECS_API_ID = "68628ac4b363e86de2ae7e7a"
BASE_URL = "https://api.techspecs.io/v5"
headers = {"accept": "application/json", "X-API-KEY": TECHSPECS_API_KEY, "X-API-ID": TECHSPECS_API_ID}

# Groq AI Configuration (Much higher limits than Gemini!)
GROQ_API_KEY = "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"
GROQ_BASE_URL = "https://api.groq.com/openai/v1/chat/completions"
if GROQ_API_KEY:
    print("✅ Groq AI configured successfully! (14,400 requests/day)")
    model_available = True
else:
    print("⚠️ Groq API key not configured")
    model_available = False

# CSV Fallback Configuration
CSV_FILE_PATH = "laptop_specs_enhanced.csv"
api_limit_reached = False  # Global flag to track API status

def load_csv_data():
    """Load laptop data from CSV file"""
    try:
        if os.path.exists(CSV_FILE_PATH):
            df = pd.read_csv(CSV_FILE_PATH)
            print(f"✅ CSV data loaded successfully! {len(df)} laptops available.")
            return df
        else:
            print(f"⚠️ CSV file not found: {CSV_FILE_PATH}")
            return None
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        return None

# Load CSV data at startup
csv_data = load_csv_data()

def analyze_user_intent_and_get_data(user_message):
    """Analyze user intent and get relevant laptop data"""
    message_lower = user_message.lower()
    
    # Simple greetings - no need for laptop data
    greetings = ['hi', 'hello', 'hey', 'sup', 'what\'s up', 'yo', 'hiya', 'heyo', 'howdy', 'greetings', 'good morning', 'good afternoon', 'good evening', 'hola', 'bonjour', 'ciao', 'salut', 'hallo', 'ola', 'hej', 'hi there']
    if any(greeting in message_lower for greeting in greetings) and len(message_lower) <= 15:
        return {'intent': 'greeting', 'data': []}
    
    # Extract budget from message
    budget_match = re.search(r'\$?([0-9,]+)', user_message)
    budget = None
    if budget_match:
        try:
            budget = int(budget_match.group(1).replace(',', ''))
        except ValueError:
            pass
    
    # Extract brand mentions
    brands = ['asus', 'dell', 'hp', 'lenovo', 'apple', 'acer', 'msi', 'razer', 'alienware']
    mentioned_brands = [brand for brand in brands if brand in message_lower]
    brand = mentioned_brands[0] if mentioned_brands else None
    
    # Determine query type
    if any(word in message_lower for word in ['gaming', 'game', 'gamer']):
        # Check if they specifically want handheld gaming devices
        handheld_keywords = ['handheld', 'portable gaming', 'steam deck', 'rog ally', 'legion go', 'portable device']
        negative_indicators = ['not', "don't", "no", "avoid", "except", "without", "exclude"]
        
        wants_handheld = False
        has_negative = any(neg in message_lower for neg in negative_indicators)
        
        # Only set wants_handheld if positive mention without negative context
        if any(word in message_lower for word in handheld_keywords) and not has_negative:
            wants_handheld = True
        
        if wants_handheld:
            query = 'handheld gaming device'
            intent = 'handheld_recommendation'
        else:
            query = 'gaming laptop'
            intent = 'gaming_recommendation'
    elif any(word in message_lower for word in ['business', 'work', 'office', 'professional']):
        query = 'business laptop'
        intent = 'business_recommendation'
    elif any(word in message_lower for word in ['student', 'school', 'college', 'university', 'cheap', 'budget']):
        query = 'budget laptop'
        intent = 'student_recommendation'
    elif any(word in message_lower for word in ['recommend', 'suggest', 'find', 'looking for', 'need']):
        query = 'laptop'
        intent = 'general_recommendation'
    elif any(word in message_lower for word in ['spec', 'specification', 'feature', 'performance']):
        query = 'laptop'
        intent = 'spec_inquiry'
    else:
        # Search for specific models/brands mentioned
        if brand or any(word in message_lower for word in ['laptop', 'computer', 'pc', 'proart', 'studiobook', 'macbook', 'thinkpad', 'xps']):
            query = user_message
            intent = 'specific_search'
        else:
            return {'intent': 'general', 'data': []}
    
    # Get relevant laptop data - use higher limit for chatbot to get more options
    # For chatbot, don't apply strict budget filter to show full range of options
    chatbot_budget = budget if budget and budget < 2000 else None  # Only apply budget for low budgets
    laptop_data = search_laptops(query, 10, chatbot_budget, brand)
    
    return {
        'intent': intent,
        'data': laptop_data,
        'budget': budget,
        'brand': brand,
        'query': query
    }

def create_smart_prompt(user_message, response_data):
    """Create intelligent prompt based on user intent"""
    intent = response_data['intent']
    laptop_data = response_data['data']
    budget = response_data.get('budget')
    brand = response_data.get('brand')
    
    # Handle simple greetings
    if intent == 'greeting':
        return f"""The user said: "{user_message}"

This is a simple greeting. Respond naturally and briefly (1-2 sentences max). Ask how you can help them find a laptop.

Keep it casual and friendly. Don't give laptop recommendations unless asked."""
    
    # Handle when no laptop data is available
    if not laptop_data:
        return f"""User message: "{user_message}"

No specific laptop data available. Provide a helpful response about what you can do to help them find laptops. Be brief (2-3 sentences max).

Mention that you can help with:
- Gaming laptops
- Business/work laptops
- Budget/student laptops
- Specific brand or budget recommendations"""
    
    # Create detailed laptop context with specifications
    laptop_context = "\n".join([
        f"""- {laptop['brand']} {laptop['model']}
  • Category: {laptop['category']}
  • Price: {laptop['specifications'].get('price', 'Price not available')}
  • CPU: {laptop['specifications'].get('cpu', 'N/A')}
  • RAM: {laptop['specifications'].get('ram', 'N/A')}
  • GPU: {laptop['specifications'].get('gpu', 'N/A')}
  • Storage: {laptop['specifications'].get('storage', 'N/A')}
  • Screen: {laptop['specifications'].get('screen_size', 'N/A')}" {laptop['specifications'].get('resolution', '')}"""
        for laptop in laptop_data[:3]  # Limit to top 3
    ])
    
    # Extract user context from message
    user_context = f"""User Context:
- Message: "{user_message}"
- Budget: {'$' + str(budget) if budget else 'Not specified'}
- Brand preference: {brand if brand else 'No preference'}
- Use case: {intent.replace('_', ' ').title()}"""
    
    # Create intent-specific prompts with better context
    if intent == 'gaming_recommendation':
        return f"""{user_context}

Available Gaming Laptops:
{laptop_context}

You are helping a gamer find the perfect laptop. Consider their specific gaming needs and budget. 

Provide a personalized recommendation:
1. Pick the BEST 1-2 laptops from the list that match their needs
2. Explain WHY these are good for gaming (GPU, performance, value)
3. Be specific about gaming capabilities
4. Keep response conversational but informative (under 150 words)

Focus on actual gaming performance, not generic features."""
    
    elif intent == 'handheld_recommendation':
        return f"""{user_context}

Available Handheld Gaming Devices:
{laptop_context}

You are helping someone find a portable gaming device. Focus on portability and gaming on-the-go.

Provide a personalized recommendation:
1. Pick the BEST 1-2 devices from the list
2. Explain WHY these are good for portable gaming
3. Mention battery life, portability, and gaming capabilities
4. Keep response conversational (under 150 words)"""
    
    elif intent == 'business_recommendation':
        return f"""{user_context}

Available Business Laptops:
{laptop_context}

You are helping a professional find a work laptop. Consider productivity, reliability, and professional needs.

Provide a personalized recommendation:
1. Pick the BEST 1-2 laptops from the list for work
2. Explain WHY these are good for business (performance, portability, features)
3. Focus on productivity and professional use
4. Keep response conversational (under 150 words)"""
    
    elif intent == 'student_recommendation':
        return f"""{user_context}

Available Student/Budget Laptops:
{laptop_context}

You are helping a student find an affordable laptop that meets their needs. Consider value, basic performance, and budget.

Provide a personalized recommendation:
1. Pick the BEST 1-2 laptops from the list for students
2. Explain WHY these offer great value (price, features, performance)
3. Focus on student needs and budget-friendliness
4. Keep response conversational (under 150 words)"""
    
    elif intent == 'spec_inquiry':
        return f"""{user_context}

Available Laptops:
{laptop_context}

The user is asking about laptop specifications or features. 

Provide a helpful response:
1. Answer their specific question about specs/features
2. Use the laptop data above to give examples
3. Explain what to look for in clear terms
4. Keep response informative but easy to understand (under 150 words)"""
    
    else:
        # General recommendation or specific search
        return f"""{user_context}

Relevant Laptops Found:
{laptop_context}

The user has a general laptop question or is looking for something specific.

Provide a personalized response:
1. If they're looking for specific laptops, mention what you found
2. If it's a general question, give a tailored recommendation
3. Consider their budget and preferences
4. Be helpful and specific (under 150 words)

Always recommend actual laptops from the list above when possible."""

def get_laptop_summary_for_chat(limit=3):
    """Get a brief summary of available laptops for chat context"""
    try:
        global csv_data
        if csv_data is not None and not csv_data.empty:
            # Get a diverse sample
            sample_laptops = csv_data.sample(min(limit, len(csv_data)))
            return [f"{row['Company']} {row['Product']}" for _, row in sample_laptops.iterrows()]
        return []
    except Exception:
        return []

def get_fallback_response(user_message, response_data):
    """Generate rule-based responses when AI is unavailable"""
    intent = response_data.get('intent', 'general')
    laptop_data = response_data.get('data', [])
    budget = response_data.get('budget')
    brand = response_data.get('brand')
    
    message_lower = user_message.lower()
    
    # Handle greetings
    if intent == 'greeting':
        return "Hey there! 👋 How can I help you find the perfect laptop?"
    
    # Handle when no laptop data is available
    if not laptop_data:
        if any(word in message_lower for word in ['gaming', 'game']):
            return "I can help you find gaming laptops! Tell me your budget and preferred brand for the best recommendations."
        elif any(word in message_lower for word in ['business', 'work']):
            return "Looking for a business laptop? I can suggest professional laptops for work. What's your budget?"
        elif any(word in message_lower for word in ['student', 'budget', 'cheap']):
            return "Need an affordable laptop for school or basic use? I can find budget-friendly options. What's your price range?"
        else:
            return "I can help you find laptops for gaming, business, student use, or general computing. What type of laptop are you looking for?"
    
    # Handle specific intents with data
    if intent == 'gaming_recommendation':
        top_laptop = laptop_data[0]
        price = top_laptop['specifications'].get('price', 'Contact for price')
        return f"For gaming, I'd recommend the {top_laptop['brand']} {top_laptop['model']} ({price}). It's designed for gaming performance. Would you like to see more gaming options?"
    
    elif intent == 'handheld_recommendation':
        if laptop_data:
            top_laptop = laptop_data[0]
            price = top_laptop['specifications'].get('price', 'Contact for price')
            return f"For portable gaming, check out the {top_laptop['brand']} {top_laptop['model']} ({price}). Perfect for gaming on the go!"
        else:
            return "Handheld gaming devices like Steam Deck or ROG Ally are great for portable gaming. Would you like me to search for available models?"
    
    elif intent == 'business_recommendation':
        top_laptop = laptop_data[0]
        price = top_laptop['specifications'].get('price', 'Contact for price')
        return f"For business use, the {top_laptop['brand']} {top_laptop['model']} ({price}) is a solid choice for professional work. Want to see more business laptops?"
    
    elif intent == 'student_recommendation':
        top_laptop = laptop_data[0]
        price = top_laptop['specifications'].get('price', 'Contact for price')
        return f"For students, the {top_laptop['brand']} {top_laptop['model']} ({price}) offers great value for everyday computing tasks."
    
    elif intent == 'specific_search':
        if laptop_data:
            results_count = len(laptop_data)
            top_laptop = laptop_data[0]
            price = top_laptop['specifications'].get('price', 'Contact for price')
            return f"I found {results_count} match{'es' if results_count != 1 else ''} for '{user_message}'. The {top_laptop['brand']} {top_laptop['model']} ({price}) looks promising."
        else:
            return f"I couldn't find exact matches for '{user_message}'. Try searching for a different model or ask for recommendations by usage type (gaming, business, student)."
    
    else:
        # General recommendation
        if laptop_data:
            top_laptop = laptop_data[0]
            price = top_laptop['specifications'].get('price', 'Contact for price')
            return f"Based on your query, I'd suggest the {top_laptop['brand']} {top_laptop['model']} ({price}). What specific features are you looking for?"
        else:
            return "I can help you find the perfect laptop! Tell me what you'll use it for (gaming, work, school) and your budget, and I'll suggest the best options."

def search_laptops_csv(query, limit=5, budget=None, brand=None):
    """Search laptops in CSV data as fallback"""
    global csv_data
    
    if csv_data is None or csv_data.empty:
        print("❌ CSV data not available for fallback")
        return []
    
    try:
        query_lower = query.lower()
        keyword_found = False  # Initialize at function level
        
        # Create searchable text for each laptop
        csv_data['search_text'] = (
            csv_data['Company'].fillna('').astype(str) + ' ' +
            csv_data['Product'].fillna('').astype(str) + ' ' +
            csv_data['TypeName'].fillna('').astype(str) + ' ' +
            csv_data['CPU_Type'].fillna('').astype(str) + ' ' +
            csv_data['GPU_Type'].fillna('').astype(str)
        ).str.lower()
        
        # Filter based on query keywords
        filtered_df = csv_data.copy()
        
        # Check if user is specifically asking for handheld/portable gaming devices
        # Don't trigger if they mention "not" or "don't want" handheld devices
        wants_handheld = False
        
        # Check for positive mentions of handheld devices
        handheld_keywords = [
            'handheld', 'portable gaming', 'steam deck', 'rog ally', 'legion go', 
            'gpd', 'onexplayer', 'portable device', 'gaming handheld'
        ]
        
        # Check for negative indicators
        negative_indicators = ['not', "don't", "no", "avoid", "except", "without", "exclude"]
        has_negative = any(neg in query_lower for neg in negative_indicators)
        
        # Only set wants_handheld if positive mention without negative context
        if any(word in query_lower for word in handheld_keywords) and not has_negative:
            wants_handheld = True
        
        # Filter out handheld gaming devices unless specifically requested
        if not wants_handheld:
            # Exclude devices with very small screens (typically handhelds)
            handheld_devices = [
                'steam deck', 'rog ally', 'legion go', 'gpd win', 'onexplayer', 
                'win max', 'valve steam deck'
            ]
            
            # Filter out handheld devices by name and screen size
            for device in handheld_devices:
                filtered_df = filtered_df[~filtered_df['Product'].str.lower().str.contains(device, na=False)]
            
            # Also filter by screen size - exclude devices with screens smaller than 11 inches
            filtered_df = filtered_df[
                (filtered_df['Inches'] >= 11) | (pd.isna(filtered_df['Inches']))
            ]
            
            print(f"🚫 Handheld devices filtered out -> {len(filtered_df)} laptops remaining")
        
        # Apply brand filter (case-insensitive)
        if brand and brand.strip():
            brand_lower = brand.lower()
            filtered_df = filtered_df[
                filtered_df['Company'].str.lower().str.contains(brand_lower, na=False)
            ]
            print(f"🏷️ Brand filter applied: {brand} -> {len(filtered_df)} laptops")
        
        # Apply budget filter (convert to Euro, assuming input is USD)
        if budget and budget > 0:
            # Convert USD to Euro (approximate rate: 1 USD = 0.92 EUR for more accuracy)
            budget_euro = budget * 0.92
            filtered_df = filtered_df[
                filtered_df['Price (Euro)'] <= budget_euro
            ]
            print(f"💰 Budget filter applied: ${budget} (€{budget_euro:.0f}) -> {len(filtered_df)} laptops")
        
        # Enhanced filtering based on usage types
        if 'gaming' in query_lower:
            # First try to find dedicated gaming laptops
            gaming_df = filtered_df[
                filtered_df['TypeName'].str.lower().str.contains('gaming', na=False)
            ]
            
            # If no dedicated gaming laptops, look for high-performance ones
            if gaming_df.empty:
                gaming_df = filtered_df[
                    (filtered_df['GPU_Type'].str.lower().str.contains('rtx|radeon|geforce', na=False)) &
                    (~filtered_df['GPU_Type'].str.lower().str.contains('intel|iris|uhd', na=False))
                ]
            
            # If still empty, look for any laptop with dedicated GPU
            if gaming_df.empty:
                gaming_df = filtered_df[
                    (filtered_df['GPU_Company'].str.lower().str.contains('nvidia|amd', na=False)) &
                    (~filtered_df['GPU_Company'].str.lower().str.contains('intel', na=False))
                ]
            
            filtered_df = gaming_df if not gaming_df.empty else filtered_df
        elif 'business' in query_lower or 'work' in query_lower:
            filtered_df = filtered_df[
                (filtered_df['TypeName'].str.lower().str.contains('ultrabook|notebook|workstation', na=False))
            ]
        elif 'student' in query_lower or 'budget' in query_lower:
            filtered_df = filtered_df[
                (filtered_df['Price (Euro)'] <= 1000) & 
                (filtered_df['TypeName'].str.lower().str.contains('notebook|ultrabook', na=False))
            ]
        else:
            # General search - use intelligent keyword extraction
            if query_lower not in ['laptop', 'laptops', '']:
                # Extract important keywords from query
                important_keywords = []
                query_words = query_lower.split()
                
                # Remove common stop words and keep important terms
                stop_words = ['tell', 'me', 'about', 'i', 'want', 'need', 'looking', 'for', 'the', 'a', 'an']
                important_words = [word for word in query_words if word not in stop_words and len(word) > 2]
                
                # Try to find matches for each important keyword
                keyword_found = False
                if important_words:
                    original_size = len(filtered_df)
                    for keyword in important_words:
                        keyword_matches = filtered_df[filtered_df['search_text'].str.contains(keyword, case=False, na=False)]
                        if not keyword_matches.empty:
                            # Sort keyword matches by relevance - exact model name matches first
                            exact_matches = keyword_matches[keyword_matches['Product'].str.lower().str.contains(keyword, case=False, na=False)]
                            other_matches = keyword_matches[~keyword_matches['Product'].str.lower().str.contains(keyword, case=False, na=False)]
                            
                            # Combine with exact matches first
                            if not exact_matches.empty:
                                filtered_df = pd.concat([exact_matches, other_matches])
                            else:
                                filtered_df = keyword_matches
                            
                            keyword_found = True
                            print(f"🔍 Keyword '{keyword}' found {len(filtered_df)} matches ({len(exact_matches)} exact)")
                            break
                
                # If no keyword matches, try full substring matching
                # Check if any filtering happened (considering brand/budget filters might have been applied)
                if len(filtered_df) == original_size and not brand and not budget:  # No filtering happened
                    substring_matches = filtered_df[filtered_df['search_text'].str.contains(query_lower, case=False, na=False)]
                    
                    if not substring_matches.empty:
                        filtered_df = substring_matches
                    else:
                        # If no substring matches, use fuzzy matching
                        scores = filtered_df['search_text'].apply(
                            lambda x: fuzz.partial_ratio(query_lower, x)
                        )
                        filtered_df = filtered_df[scores >= 25]  # Lower threshold for more results
                        filtered_df = filtered_df.loc[scores.sort_values(ascending=False).index]
        
        # Sort by relevance and price - show variety of price ranges
        if not filtered_df.empty:
            # If we found specific keyword matches, prioritize by relevance (don't sort by price)
            if keyword_found:
                # Keep original order for keyword matches (most relevant first)
                pass
            elif budget and budget > 3000:
                # Sort by price descending first to show premium options
                filtered_df = filtered_df.sort_values(['Price (Euro)'], ascending=[False])
            else:
                # For lower budgets, prioritize affordable options
                filtered_df = filtered_df.sort_values(['Price (Euro)'], ascending=[True])
        
        # Transform to match API format
        results = []
        for _, laptop in filtered_df.head(limit).iterrows():
            transformed_item = {
                'brand': str(laptop.get('Company', 'Unknown Brand')),
                'model': str(laptop.get('Product', 'Unknown Model')),
                'category': str(laptop.get('TypeName', 'Laptop')),
                'version': f"{laptop.get('CPU_Type', '')} | {laptop.get('RAM (GB)', '')}GB | {laptop.get('Memory', '')}",
                'id': f"csv_{len(results)}",
                'image': '',  # No images in CSV
                'specifications': {
                    'screen_size': f"{laptop.get('Inches', 'N/A')}" if pd.notna(laptop.get('Inches')) else 'N/A',
                    'resolution': str(laptop.get('ScreenResolution', 'N/A')),
                    'cpu': str(laptop.get('CPU_Type', 'N/A')),
                    'ram': f"{laptop.get('RAM (GB)', 'N/A')}GB" if pd.notna(laptop.get('RAM (GB)')) else 'N/A',
                    'storage': str(laptop.get('Memory', 'N/A')),
                    'gpu': str(laptop.get('GPU_Type', 'N/A')),
                    'os': str(laptop.get('OpSys', 'N/A')),
                    'weight': f"{laptop.get('Weight (kg)', 'N/A')}kg" if pd.notna(laptop.get('Weight (kg)')) else 'N/A',
                    'price': f"€{laptop.get('Price (Euro)', 'N/A')}" if pd.notna(laptop.get('Price (Euro)')) else 'N/A'
                }
            }
            results.append(transformed_item)
        
        print(f"📊 CSV fallback: Found {len(results)} results for '{query}'")
        return results
        
    except Exception as e:
        print(f"❌ CSV search error: {e}")
        return []

def search_laptops(query, limit=5, budget=None, brand=None):
    """Search for laptops using API with CSV fallback"""
    global api_limit_reached
    
    # If we know API limit is reached, go straight to CSV
    if api_limit_reached:
        print(f"🔄 Using CSV fallback for query: {query}")
        return search_laptops_csv(query, limit, budget, brand)
    
    # Try API first
    params = {
        "q": query,
        "category": "Laptops"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/products/search", headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'data' in data and data['data']:
                # Transform the data structure to match what our frontend expects
                transformed_data = []
                for item in data['data'][:limit]:
                    if 'Product' in item:
                        product = item['Product']
                        transformed_item = {
                            'brand': product.get('Brand', 'Unknown Brand'),
                            'model': product.get('Model', 'Unknown Model'),
                            'category': product.get('Category', 'Laptop'),
                            'version': product.get('Version', ''),
                            'id': product.get('id', ''),
                            'image': item.get('Image', ''),
                            'specifications': {}  # Empty for now since basic API doesn't include specs
                        }
                        transformed_data.append(transformed_item)
                
                print(f"✅ API success: Found {len(transformed_data)} results for '{query}'")
                return transformed_data
            else:
                print(f"⚠️ No data found in API response for query: {query}")
                
        elif response.status_code == 402:
            print(f"💳 API rate limit reached! Switching to CSV fallback for query: {query}")
            api_limit_reached = True  # Set global flag
            return search_laptops_csv(query, limit, budget, brand)
        else:
            print(f"❌ API Error {response.status_code} for query: {query}")
            
    except Exception as e:
        print(f"❌ API Error for query '{query}': {e}")
    
    # If API fails for any reason, try CSV fallback
    print(f"🔄 API failed, trying CSV fallback for query: {query}")
    return search_laptops_csv(query, limit, budget, brand)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/recommend', methods=['POST'])
def recommend():
    try:
        data = request.get_json()
        usage = data.get('usage', 'general')
        budget = data.get('budget')
        brand = data.get('brand')
        
        # Convert budget to integer if provided
        if budget:
            try:
                budget = int(budget)
            except (ValueError, TypeError):
                budget = None
        
        print(f"🎯 Recommendation request: usage={usage}, budget=${budget}, brand={brand}")
        
        # Simple recommendation logic based on usage
        if usage == 'gaming':
            query = 'gaming laptop'
        elif usage == 'business':
            query = 'business laptop'
        elif usage == 'student':
            query = 'budget laptop'
        else:
            query = 'laptop'
        
        recommendations = search_laptops(query, 6, budget, brand)
        
        return jsonify({
            'success': True,
            'recommendations': recommendations
        })
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get recommendations'
        })

@app.route('/search', methods=['POST'])
def search():
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({'success': False, 'error': 'No search query provided'})
        
        print(f"🔍 Search request: query={query}")
        
        results = search_laptops(query, 8)
        
        return jsonify({
            'success': True,
            'results': results
        })
    except Exception as e:
        print(f"Search error: {e}")
        return jsonify({
            'success': False,
            'error': 'Search failed'
        })

@app.route('/api-status')
def api_status():
    """Check current API status and CSV fallback info"""
    global api_limit_reached, csv_data
    
    csv_available = csv_data is not None and not csv_data.empty
    csv_count = len(csv_data) if csv_available else 0
    
    return jsonify({
        'api_limit_reached': api_limit_reached,
        'csv_fallback_available': csv_available,
        'csv_laptop_count': csv_count,
        'current_mode': 'CSV Fallback' if api_limit_reached else 'API Mode'
    })

@app.route('/reset-api', methods=['POST'])
def reset_api():
    """Reset API limit flag (for testing or when limit resets)"""
    global api_limit_reached
    
    api_limit_reached = False
    print("🔄 API limit flag reset - will try API again")
    
    return jsonify({
        'success': True,
        'message': 'API limit flag reset successfully',
        'current_mode': 'API Mode'
    })

@app.route('/memory-stats')
def memory_stats():
    """Get detailed memory usage statistics"""
    try:
        stats = conversation_memory.get_memory_stats()
        return jsonify({
            'success': True,
            'memory_stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/clear-memory', methods=['POST'])
def clear_memory():
    """Clear all conversation memory to free up space"""
    try:
        conversation_memory.clear_all_sessions()
        return jsonify({
            'success': True,
            'message': 'All conversation memory cleared successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

# Import the AI training system and conversation memory
from ai_training_system import LAPTOP_EXPERT_SYSTEM_PROMPT, create_enhanced_prompt, LaptopAITrainer
from conversation_memory import ConversationMemory, create_contextual_prompt

# Initialize the AI trainer and conversation memory with strict limits
ai_trainer = LaptopAITrainer()
conversation_memory = ConversationMemory(
    max_messages=10,        # Reduced from 20 to save memory
    session_timeout_minutes=30,  # Reduced from 60 to 30 minutes
    max_sessions=25,        # Max 25 concurrent users
    max_memory_mb=50        # Max 50MB memory usage
)

def call_groq_api(prompt, use_enhanced_training=True):
    """Call Groq API for AI responses with enhanced training"""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Use the enhanced system prompt with laptop expertise
    system_prompt = LAPTOP_EXPERT_SYSTEM_PROMPT if use_enhanced_training else "You are a helpful laptop consultant."
    
    data = {
        "model": "llama3-70b-8192",  # Much smarter 70B model for better recommendations
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user", 
                "content": prompt
            }
        ],
        "max_tokens": 400,  # Increased for more detailed responses
        "temperature": 0.7  # Balanced creativity and accuracy
    }
    
    try:
        response = requests.post(GROQ_BASE_URL, headers=headers, json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result['choices'][0]['message']['content'].strip()
            return ai_response
        else:
            print(f"❌ Groq API Error {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Groq API Error: {e}")
        return None

def call_groq_api_with_history(conversation_history):
    """Call Groq API with full conversation history for context-aware responses"""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "llama3-70b-8192",  # Much smarter 70B model
        "messages": conversation_history,  # Send full conversation context
        "max_tokens": 400,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(GROQ_BASE_URL, headers=headers, json=data, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result['choices'][0]['message']['content'].strip()
            print(f"🧠 Context-aware response generated (using {len(conversation_history)} messages)")
            return ai_response
        else:
            print(f"❌ Groq API Error {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Groq API Error: {e}")
        return None

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'success': False, 'error': 'No message provided'})
        
        # Check if Groq API is configured
        if not model_available:
            return jsonify({
                'success': False,
                'error': 'Groq AI not configured. Please check your API key.'
            })
        
        # Get session ID for conversation memory
        session_id = conversation_memory.get_session_id(request)
        print(f"💬 Chat request [{session_id[:8]}]: {user_message}")
        
        # Add user message to conversation history
        conversation_memory.add_message(session_id, 'user', user_message)
        
        # Monitor memory usage
        memory_stats = conversation_memory.get_memory_stats()
        print(f"💾 Memory: {memory_stats['memory_usage_mb']}MB/{memory_stats['memory_limit_mb']}MB ({memory_stats['memory_usage_percent']}%) | Sessions: {memory_stats['active_sessions']}/{memory_stats['session_limit']}")
        
        # Analyze user intent and get relevant data
        response_data = analyze_user_intent_and_get_data(user_message)
        
        try:
            # Get conversation history for context
            conversation_history = conversation_memory.get_conversation_history(session_id, include_system_prompt=True)
            
            # If we have conversation history, use it directly with the API
            if len(conversation_history) > 1:  # More than just system prompt
                # Add current message to conversation
                conversation_history.append({
                    'role': 'user',
                    'content': user_message
                })
                
                # Use conversation history with Groq API
                ai_response = call_groq_api_with_history(conversation_history)
            else:
                # First message - use enhanced prompt with training examples
                enhanced_prompt = create_enhanced_prompt(user_message, response_data['data'])
                ai_response = call_groq_api(enhanced_prompt, use_enhanced_training=True)
            
            if ai_response:
                # Add AI response to conversation history
                conversation_memory.add_message(session_id, 'assistant', ai_response)
                
                return jsonify({
                    'success': True,
                    'response': ai_response
                })
            else:
                # If Groq fails, use fallback
                fallback_response = get_fallback_response(user_message, response_data)
                conversation_memory.add_message(session_id, 'assistant', fallback_response)
                
                return jsonify({
                    'success': True,
                    'response': fallback_response
                })
            
        except Exception as ai_error:
            print(f"AI API error: {ai_error}")
            # Fallback to rule-based responses when AI is unavailable
            fallback_response = get_fallback_response(user_message, response_data)
            conversation_memory.add_message(session_id, 'assistant', fallback_response)
            
            return jsonify({
                'success': True,
                'response': fallback_response
            })
        
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({
            'success': False,
            'error': 'Sorry, I had trouble processing that. Could you try rephrasing?'
        })

if __name__ == '__main__':
    print("Starting Laptop AI Recommender...")
    print("Open your browser and go to: http://localhost:8080")
    app.run(debug=True, port=8080, host='127.0.0.1')
