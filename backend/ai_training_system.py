LAPTOP_EXPERT_SYSTEM_PROMPT = """You are a laptop consultant. Match the buyer's use case, budget, and constraints to the available laptop data.

Laptop expertise:
- Gaming laptops: GPU performance, CPU requirements, cooling, and value.
- Business laptops: portability, reliability, battery life, webcams, and security.
- Student laptops: price, durability, battery life, and enough performance for schoolwork.
- Creative work: display quality, color accuracy, CPU power, GPU power, RAM, and storage.

Useful buying rules:
- RTX 4090/4080: top-tier gaming and heavy creative work.
- RTX 4070/4060: strong gaming performance and good value.
- RTX 4050: entry-level 1080p gaming.
- Integrated graphics: office work, schoolwork, media, and light gaming only.
- Intel i9/Ryzen 9: high-end performance.
- Intel i7/Ryzen 7: strong gaming and productivity.
- Intel i5/Ryzen 5: good balance for most users.
- Intel i3/Ryzen 3: budget/basic tasks.

Response rules:
- Use short sentences.
- Explain technical terms in plain language.
- Recommend models from the available laptop data.
- Name the tradeoff behind each recommendation.
- Ask one follow-up question if the buyer left out budget, use case, or size.
"""


TRAINING_EXAMPLES = [
    {
        "user_input": "I'm a student who wants to game on weekends. Budget is $1000.",
        "context": "Budget gaming laptops available with RTX 4050, Ryzen 5 processors.",
        "ideal_response": (
            "For a student gamer around $1000, I would look for an RTX 4050 or RTX 4060 "
            "laptop with 16GB RAM. That gives you smooth 1080p gaming while still being "
            "good for schoolwork. If the available list includes an Acer Nitro, ASUS TUF, "
            "or Lenovo LOQ in that range, compare those first."
        ),
    },
    {
        "user_input": "Best laptop for work meetings and presentations?",
        "context": "Business laptops with good displays, webcams, microphones, and battery life.",
        "ideal_response": (
            "For meetings and presentations, prioritize battery life, a sharp display, a good "
            "webcam, and reliable sleep/wake behavior. A ThinkPad, Dell XPS/Latitude, or HP "
            "EliteBook style machine fits this job better than a gaming laptop, even if "
            "the gaming laptop has more raw power."
        ),
    },
]


LAPTOP_KNOWLEDGE_BASE = {
    "gaming_requirements": {
        "competitive_esports": "High refresh rate display, low latency, and RTX 4060 or better.",
        "aaa_gaming": "RTX 4070 or better for high settings, with enough cooling to sustain performance.",
        "indie_gaming": "RTX 4050 or strong integrated graphics can be enough.",
        "vr_gaming": "RTX 4070 or better with a strong CPU.",
    },
    "business_features": {
        "security": "TPM, fingerprint reader, Windows Hello, and good update support.",
        "portability": "Lightweight chassis and 8+ hour practical battery life.",
        "durability": "Strong hinge, keyboard, and chassis quality.",
    },
    "student_priorities": {
        "budget": "Under $1000 is ideal when performance needs are moderate.",
        "durability": "Good build quality matters if it will be carried daily.",
        "versatility": "Enough CPU/RAM for schoolwork plus light creative work or gaming.",
    },
}


def create_enhanced_prompt(user_message, laptop_data, training_examples=True):
    laptop_context = format_laptop_context(laptop_data)
    examples_section = format_training_examples() if training_examples else ""

    return f"""{LAPTOP_EXPERT_SYSTEM_PROMPT}

{examples_section}

Available laptops:
{laptop_context}

User message: "{user_message}"

Use the available laptop data. Recommend one or two models. Explain the tradeoff in plain language."""


def format_laptop_context(laptop_data):
    if not laptop_data:
        return "No matching laptop data was found."

    return "\n".join(format_laptop(laptop) for laptop in laptop_data[:3])


def format_laptop(laptop):
    specs = laptop.get("specifications", {})
    return (
        f"- {laptop.get('brand', 'Unknown')} {laptop.get('model', 'Unknown')}\n"
        f"  Price: {specs.get('price', 'N/A')}\n"
        f"  CPU: {specs.get('cpu', 'N/A')}\n"
        f"  GPU: {specs.get('gpu', 'N/A')}\n"
        f"  RAM: {specs.get('ram', 'N/A')}\n"
        f"  Storage: {specs.get('storage', 'N/A')}\n"
        f"  Screen: {specs.get('screen_size', 'N/A')} {specs.get('resolution', '')}"
    )


def format_training_examples():
    examples = []
    for example in TRAINING_EXAMPLES:
        examples.append(
            f"Example user: {example['user_input']}\n"
            f"Example context: {example['context']}\n"
            f"Example answer: {example['ideal_response']}"
        )

    return "Example interactions:\n\n" + "\n\n".join(examples)


def get_domain_knowledge(category, subcategory):
    return LAPTOP_KNOWLEDGE_BASE.get(category, {}).get(subcategory, "")
