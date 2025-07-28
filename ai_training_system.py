"""
AI Training System for Laptop Recommendations
This module contains advanced prompting techniques to make the AI smarter for laptop recommendations
"""

# Enhanced system prompt with laptop expertise
LAPTOP_EXPERT_SYSTEM_PROMPT = """You are an expert laptop consultant with 10+ years of experience helping customers find the perfect laptop. You have deep knowledge about:

LAPTOP EXPERTISE:
- Gaming laptops: GPU performance (RTX 4070/4080 for high-end, RTX 4050/4060 for budget gaming), CPU requirements, cooling systems
- Business laptops: Professional features, portability, battery life, security features
- Student laptops: Budget-friendly options, durability, basic performance needs
- Creative work: High-resolution displays, color accuracy, powerful CPUs for video/photo editing

GPU KNOWLEDGE:
- RTX 4090/4080: Top-tier gaming, 4K ultra settings
- RTX 4070/4060: Great 1440p gaming, good value
- RTX 4050: Entry-level gaming, 1080p high settings
- Integrated graphics: Office work, light gaming only

CPU KNOWLEDGE:
- Intel i9/AMD Ryzen 9: High-end performance, content creation
- Intel i7/AMD Ryzen 7: Excellent gaming and productivity
- Intel i5/AMD Ryzen 5: Good balance for most users
- Intel i3/AMD Ryzen 3: Budget options, basic tasks

PRICE RANGES:
- Under $800: Budget/student laptops with basic specs
- $800-$1200: Mid-range gaming, good business laptops
- $1200-$2000: High-performance gaming, premium business
- $2000+: Flagship gaming, workstation-class laptops

COMMUNICATION STYLE:
- Be conversational but knowledgeable
- Ask follow-up questions to understand needs better
- Explain technical terms in simple language
- Give specific model recommendations with reasons
- Mention price-to-performance value
- Consider the user's primary use case and budget

Always provide actionable advice and specific laptop recommendations from the available data."""

# Few-shot learning examples to teach the AI better responses
TRAINING_EXAMPLES = [
    {
        "user_input": "I'm a student who wants to game on weekends. Budget is $1000.",
        "context": "Budget gaming laptops available with RTX 4050, Ryzen 5 processors",
        "ideal_response": """Perfect! For a student gamer with a $1000 budget, I'd recommend the **Acer Nitro 5** or **ASUS TUF Gaming A15**. Here's why:

**Acer Nitro 5 (~$950)**:
- RTX 4050 GPU: Handles most games at 1080p high settings (60+ FPS)
- Ryzen 5 7535HS: Great for both gaming and schoolwork
- 16GB RAM: Smooth multitasking between games and school apps

This hits the sweet spot for student gaming - powerful enough for AAA games but won't break the bank. The RTX 4050 can run games like Cyberpunk 2077 at medium-high settings with good frame rates.

What types of games do you mainly play? That might help me fine-tune the recommendation!"""
    },
    {
        "user_input": "Best laptop for work meetings and presentations?",
        "context": "Business laptops with good displays, professional features",
        "ideal_response": """For work meetings and presentations, you want reliability and professionalism. I'd recommend:

**Dell XPS 13 or ThinkPad X1 Carbon**:
- **Excellent webcam & microphone**: Critical for video calls
- **High-resolution display**: Makes presentations crisp and clear
- **Long battery life**: 8-10 hours for all-day meetings
- **Professional design**: Looks great in business settings
- **Fast wake-up**: Intel Evo certification means instant-on from sleep

The ThinkPad has the legendary keyboard if you type a lot, while the XPS 13 has a more modern design. Both have excellent build quality and business-grade reliability.

What's your budget range? And do you need to run any specific software for work?"""
    }
]

def create_enhanced_prompt(user_message, laptop_data, training_examples=True):
    """Create enhanced prompt with training examples and expertise"""
    
    # Build laptop context
    laptop_context = ""
    if laptop_data:
        laptop_context = "\n".join([
            f"""**{laptop['brand']} {laptop['model']}** (€{laptop['specifications'].get('price', 'N/A')})
   • CPU: {laptop['specifications'].get('cpu', 'N/A')}
   • GPU: {laptop['specifications'].get('gpu', 'N/A')}
   • RAM: {laptop['specifications'].get('ram', 'N/A')}
   • Storage: {laptop['specifications'].get('storage', 'N/A')}
   • Screen: {laptop['specifications'].get('screen_size', 'N/A')}\" {laptop['specifications'].get('resolution', '')}"""
            for laptop in laptop_data[:3]
        ])
    
    # Include training examples if requested
    examples_section = ""
    if training_examples:
        examples_section = f"""
EXAMPLE INTERACTIONS (Learn from these):

{chr(10).join([f"User: {ex['user_input']}" + chr(10) + f"Expert Response: {ex['ideal_response']}" + chr(10) for ex in TRAINING_EXAMPLES])}

NOW RESPOND TO THE ACTUAL USER:"""
    
    enhanced_prompt = f"""{LAPTOP_EXPERT_SYSTEM_PROMPT}

{examples_section}

AVAILABLE LAPTOPS:
{laptop_context}

USER MESSAGE: "{user_message}"

Provide an expert recommendation following the style from the examples above. Be specific, helpful, and ask follow-up questions to better understand their needs."""

    return enhanced_prompt

# Advanced prompting techniques
class LaptopAITrainer:
    def __init__(self):
        self.conversation_history = []
        self.user_preferences = {}
    
    def add_user_preference(self, user_id, preference_type, value):
        """Learn user preferences over time"""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {}
        self.user_preferences[user_id][preference_type] = value
    
    def get_personalized_prompt(self, user_id, message, laptop_data):
        """Create personalized prompt based on user history"""
        base_prompt = create_enhanced_prompt(message, laptop_data)
        
        # Add personalization if we have user history
        if user_id in self.user_preferences:
            prefs = self.user_preferences[user_id]
            personalization = f"""
USER PROFILE (Remember these preferences):
- Previous interests: {', '.join([f"{k}: {v}" for k, v in prefs.items()])}

Consider these preferences in your recommendation."""
            base_prompt += personalization
        
        return base_prompt
    
    def learn_from_interaction(self, user_message, ai_response, user_feedback=None):
        """Learn from user interactions (for future improvement)"""
        interaction = {
            'user_message': user_message,
            'ai_response': ai_response,
            'feedback': user_feedback,
            'timestamp': str(pd.Timestamp.now())
        }
        self.conversation_history.append(interaction)
        
        # Analyze for patterns (could be enhanced with ML later)
        if user_feedback == 'positive':
            print(f"✅ Good response pattern logged: {user_message[:50]}...")
        elif user_feedback == 'negative':
            print(f"❌ Poor response pattern logged: {user_message[:50]}...")

# Domain-specific knowledge base
LAPTOP_KNOWLEDGE_BASE = {
    "gaming_requirements": {
        "competitive_esports": "High refresh rate (144Hz+), low latency, RTX 4060+",
        "aaa_gaming": "RTX 4070+ for 1440p, RTX 4080+ for 4K",
        "indie_gaming": "RTX 4050 or GTX 1660 sufficient",
        "vr_gaming": "RTX 4070+ minimum, high-end CPU"
    },
    "business_features": {
        "security": "TPM 2.0, fingerprint reader, Windows Hello",
        "portability": "Under 3lbs, 8+ hour battery",
        "durability": "MIL-STD-810G certification, spill-resistant keyboard"
    },
    "student_priorities": {
        "budget": "Under $1000 ideal, $600-800 minimum viable",
        "durability": "Good build quality for 4+ years of use",
        "versatility": "Handle schoolwork + light gaming/creativity"
    }
}

def get_domain_knowledge(category, subcategory):
    """Get specific domain knowledge for recommendations"""
    return LAPTOP_KNOWLEDGE_BASE.get(category, {}).get(subcategory, "")

if __name__ == "__main__":
    # Example usage
    trainer = LaptopAITrainer()
    
    # Simulate user interaction
    test_message = "I'm a computer science student who loves gaming"
    test_laptop_data = [
        {
            'brand': 'ASUS',
            'model': 'TUF Gaming A15',
            'specifications': {
                'cpu': 'Ryzen 7 7735HS',
                'gpu': 'RTX 4050',
                'ram': '16GB',
                'storage': '512GB SSD',
                'price': '999'
            }
        }
    ]
    
    enhanced_prompt = create_enhanced_prompt(test_message, test_laptop_data)
    print("Enhanced prompt created with training examples and expertise!")
    print(f"Prompt length: {len(enhanced_prompt)} characters")
