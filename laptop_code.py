from flask import Flask, render_template, request, jsonify
import requests
import re
import time
from threading import Lock

app = Flask(__name__)

# API Configuration (from your existing code)
API_KEY = "4b63c96d-e120-4f9a-99dc-3b4da4d05ca3"
API_ID = "686279deb363e86de2ae7e6e"
BASE_URL = "https://api.techspecs.io/v5"
headers = {"accept": "application/json", "X-API-KEY": API_KEY, "X-API-ID": API_ID}

# Rate limiting
last_request_time = 0
request_lock = Lock()

class LaptopRecommender:
    def __init__(self):
        self.cache = {}
        
    def get_specs(self, model_name):
        """Get laptop specifications from API with rate limiting"""
        global last_request_time
        
        with request_lock:
            # Rate limiting - wait at least 1 second between requests
            current_time = time.time()
            time_since_last = current_time - last_request_time
            if time_since_last < 1:
                time.sleep(1 - time_since_last)
            
            # Check cache first
            if model_name in self.cache:
                return self.cache[model_name]
            
            params = {
                "q": model_name,
                "category": "Laptops"
            }
            
            try:
                response = requests.get(f"{BASE_URL}/products/search", headers=headers, params=params, timeout=10)
                last_request_time = time.time()
                
                if response.status_code == 200:
                    data = response.json()
                    self.cache[model_name] = data
                    return data
                else:
                    print(f"API Error: Status {response.status_code}")
                    return None
            except Exception as e:
                print(f"API Error: {e}")
                return None
    
    def search_laptops(self, query, limit=8):
        """Search for laptops using the API"""
        result = self.get_specs(query)
        if result and 'data' in result:
            return result['data'][:limit]
        return []
    
    def extract_price(self, price_text):
        """Extract numeric price from text"""
        if not price_text:
            return 0
        # Extract numbers from price text
        numbers = re.findall(r'\d+', str(price_text))
        if numbers:
            return int(numbers[0])
        return 0
    
    def get_spec_value(self, laptop, category, key):
        """Helper to safely get specification values"""
        specs = laptop.get('specifications', {})
        category_specs = specs.get(category, {})
        return category_specs.get(key, '')
    
    def recommend_by_preferences(self, budget=None, usage=None, brand_preference=None):
        """Recommend laptops based on user preferences"""
        # Define search terms based on usage
        if usage == 'gaming':
            search_terms = ['gaming laptop', 'RTX laptop', 'gaming notebook']
        elif usage == 'business':
            search_terms = ['business laptop', 'ultrabook', 'ThinkPad']
        elif usage == 'student':
            search_terms = ['budget laptop', 'student laptop', 'affordable laptop']
        else:
            search_terms = ['laptop', 'notebook', 'ultrabook']
        
        all_laptops = []
        
        # Search with each term
        for term in search_terms[:2]:  # Limit to 2 terms to avoid too many API calls
            try:
                laptops = self.search_laptops(term, 4)
                all_laptops.extend(laptops)
                time.sleep(1)  # Rate limiting between searches
            except Exception as e:
                print(f"Search error for term '{term}': {e}")
                continue
        
        # Remove duplicates
        seen_models = set()
        unique_laptops = []
        for laptop in all_laptops:
            model_key = f"{laptop.get('brand', '')}-{laptop.get('model', '')}"
            if model_key not in seen_models and len(unique_laptops) < 8:
                seen_models.add(model_key)
                unique_laptops.append(laptop)
        
        # Filter and score laptops
        scored_laptops = []
        for laptop in unique_laptops:
            # Budget filter
            if budget:
                price = self.extract_price(laptop.get('price'))
                if price > 0 and price > budget:
                    continue
            
            # Brand preference
            if brand_preference and laptop.get('brand'):
                if brand_preference.lower() not in laptop.get('brand', '').lower():
                    continue
            
            score = self.calculate_usage_score(laptop, usage)
            scored_laptops.append((laptop, score))
        
        # Sort by score and return top recommendations
        scored_laptops.sort(key=lambda x: x[1], reverse=True)
        return [laptop for laptop, score in scored_laptops[:6]]
    
    def calculate_usage_score(self, laptop, usage):
        """Calculate a score based on usage requirements"""
        score = 10  # Base score
        specs = laptop.get('specifications', {})
        
        # Get key specifications
        processor_info = str(specs.get('Processor', {})).lower()
        graphics_info = str(specs.get('Graphics', {})).lower()
        memory_info = str(specs.get('Memory', {})).lower()
        
        if usage == 'gaming':
            # Gaming laptops need good GPU, RAM, and processor
            if any(gpu in graphics_info for gpu in ['rtx', 'gtx', 'radeon']):
                score += 30
            if any(cpu in processor_info for cpu in ['i7', 'i9', 'ryzen 7', 'ryzen 9']):
                score += 25
            if any(ram in memory_info for ram in ['16gb', '32gb']):
                score += 20
        
        elif usage == 'business':
            # Business laptops prioritize reliability and performance
            if any(cpu in processor_info for cpu in ['i5', 'i7', 'ryzen 5', 'ryzen 7']):
                score += 25
            if 'ssd' in str(specs.get('Storage', {})).lower():
                score += 20
            # Business-friendly brands
            brand = laptop.get('brand', '').lower()
            if any(b in brand for b in ['thinkpad', 'dell', 'hp', 'lenovo']):
                score += 15
        
        elif usage == 'student':
            # Students need good value
            price = self.extract_price(laptop.get('price'))
            if 0 < price < 800:
                score += 25
            elif 800 <= price < 1200:
                score += 15
            if any(cpu in processor_info for cpu in ['i5', 'ryzen 5']):
                score += 20
        
        return score

# Initialize recommender
recommender = LaptopRecommender()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/recommend', methods=['POST'])
def recommend():
    try:
        data = request.get_json()
        
        budget = data.get('budget')
        usage = data.get('usage')
        brand = data.get('brand')
        
        # Convert budget to integer if provided
        if budget:
            try:
                budget = int(budget)
            except:
                budget = None
        
        recommendations = recommender.recommend_by_preferences(
            budget=budget,
            usage=usage,
            brand_preference=brand
        )
        
        return jsonify({
            'success': True,
            'recommendations': recommendations
        })
    
    except Exception as e:
        print(f"Recommendation error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get recommendations. Please try again.'
        })

@app.route('/search', methods=['POST'])
def search():
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({'success': False, 'error': 'No search query provided'})
        
        results = recommender.search_laptops(query, 8)
        
        return jsonify({
            'success': True,
            'results': results
        })
    
    except Exception as e:
        print(f"Search error: {e}")
        return jsonify({
            'success': False,
            'error': 'Search failed. Please try again.'
        })

if __name__ == '__main__':
    print("Starting Laptop AI Recommender...")
    print("Open your browser and go to: http://localhost:5000")
    app.run(debug=True, port=5000, host='0.0.0.0')
