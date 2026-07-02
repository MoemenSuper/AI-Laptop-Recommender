import re


BRANDS = ["asus", "dell", "hp", "lenovo", "apple", "acer", "msi", "razer", "alienware"]
GREETINGS = [
    "hi",
    "hello",
    "hey",
    "sup",
    "what's up",
    "yo",
    "hiya",
    "heyo",
    "howdy",
    "greetings",
    "good morning",
    "good afternoon",
    "good evening",
    "hola",
    "bonjour",
    "ciao",
    "salut",
    "hallo",
    "ola",
    "hej",
    "hi there",
]
HANDHELD_KEYWORDS = [
    "handheld",
    "portable gaming",
    "steam deck",
    "rog ally",
    "legion go",
    "portable device",
]
NEGATIVE_INDICATORS = ["not", "don't", "no", "avoid", "except", "without", "exclude"]


def analyze_user_intent_and_get_data(user_message, catalog):
    message_lower = user_message.lower()

    if any(greeting in message_lower for greeting in GREETINGS) and len(message_lower) <= 15:
        return {"intent": "greeting", "data": []}

    budget = extract_budget(user_message)
    brand = first_mentioned_brand(message_lower)
    intent, query = classify_query(message_lower, brand, user_message)

    if intent == "general":
        return {"intent": "general", "data": []}

    chatbot_budget = budget if budget and budget < 2000 else None
    laptop_data = catalog.search(query, limit=10, budget=chatbot_budget, brand=brand)

    return {
        "intent": intent,
        "data": laptop_data,
        "budget": budget,
        "brand": brand,
        "query": query,
    }


def extract_budget(user_message):
    budget_match = re.search(r"\$?([0-9,]+)", user_message)
    if not budget_match:
        return None

    try:
        return int(budget_match.group(1).replace(",", ""))
    except ValueError:
        return None


def first_mentioned_brand(message_lower):
    mentioned_brands = [brand for brand in BRANDS if brand in message_lower]
    return mentioned_brands[0] if mentioned_brands else None


def classify_query(message_lower, brand, original_message):
    if any(word in message_lower for word in ["gaming", "game", "gamer"]):
        has_negative = any(negative in message_lower for negative in NEGATIVE_INDICATORS)
        wants_handheld = any(word in message_lower for word in HANDHELD_KEYWORDS) and not has_negative
        if wants_handheld:
            return "handheld_recommendation", "handheld gaming device"
        return "gaming_recommendation", "gaming laptop"

    if any(word in message_lower for word in ["business", "work", "office", "professional"]):
        return "business_recommendation", "business laptop"

    if any(word in message_lower for word in ["student", "school", "college", "university", "cheap", "budget"]):
        return "student_recommendation", "budget laptop"

    if any(word in message_lower for word in ["recommend", "suggest", "find", "looking for", "need"]):
        return "general_recommendation", "laptop"

    if any(word in message_lower for word in ["spec", "specification", "feature", "performance"]):
        return "spec_inquiry", "laptop"

    laptop_words = ["laptop", "computer", "pc", "proart", "studiobook", "macbook", "thinkpad", "xps"]
    if brand or any(word in message_lower for word in laptop_words):
        return "specific_search", original_message

    return "general", None


def get_fallback_response(user_message, response_data):
    intent = response_data.get("intent", "general")
    laptop_data = response_data.get("data", [])
    message_lower = user_message.lower()

    if intent == "greeting":
        return "Hey there! How can I help you find the perfect laptop?"

    if not laptop_data:
        if any(word in message_lower for word in ["gaming", "game"]):
            return "I can help you find gaming laptops. Tell me your budget and preferred brand for the best recommendations."
        if any(word in message_lower for word in ["business", "work"]):
            return "Looking for a business laptop? I can suggest professional laptops for work. What's your budget?"
        if any(word in message_lower for word in ["student", "budget", "cheap"]):
            return "Need an affordable laptop for school or basic use? I can find budget-friendly options. What's your price range?"
        return "I can help you find laptops for gaming, business, student use, or general computing. What type of laptop are you looking for?"

    top_laptop = laptop_data[0]
    laptop_name = f"{top_laptop['brand']} {top_laptop['model']}"
    price = top_laptop["specifications"].get("price", "Contact for price")

    if intent == "gaming_recommendation":
        return f"For gaming, I'd recommend the {laptop_name} ({price}). It's designed for gaming performance. Would you like to see more gaming options?"

    if intent == "handheld_recommendation":
        return f"For portable gaming, check out the {laptop_name} ({price}). Perfect for gaming on the go."

    if intent == "business_recommendation":
        return f"For business use, the {laptop_name} ({price}) is a solid choice for professional work. Want to see more business laptops?"

    if intent == "student_recommendation":
        return f"For students, the {laptop_name} ({price}) offers good value for everyday computing tasks."

    if intent == "specific_search":
        results_count = len(laptop_data)
        return f"I found {results_count} match{'es' if results_count != 1 else ''} for '{user_message}'. The {laptop_name} ({price}) looks promising."

    return f"Based on your query, I'd suggest the {laptop_name} ({price}). What specific features are you looking for?"
