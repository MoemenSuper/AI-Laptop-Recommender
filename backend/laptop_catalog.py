import os

import pandas as pd
import requests
from fuzzywuzzy import fuzz


HANDHELD_KEYWORDS = [
    "handheld",
    "portable gaming",
    "steam deck",
    "rog ally",
    "legion go",
    "gpd",
    "onexplayer",
    "portable device",
    "gaming handheld",
]
HANDHELD_DEVICES = [
    "steam deck",
    "rog ally",
    "legion go",
    "gpd win",
    "onexplayer",
    "win max",
    "valve steam deck",
]
NEGATIVE_INDICATORS = ["not", "don't", "no", "avoid", "except", "without", "exclude"]
STOP_WORDS = {"tell", "me", "about", "i", "want", "need", "looking", "for", "the", "a", "an"}


class LaptopCatalog:
    def __init__(self, csv_file_path, techspecs_config):
        self.csv_file_path = csv_file_path
        self.techspecs_config = techspecs_config
        self.api_limit_reached = not techspecs_config.configured
        self.csv_data = self._load_csv_data()

    def search(self, query, limit=5, budget=None, brand=None):
        if self.api_limit_reached:
            print(f"Using CSV fallback for query: {query}")
            return self._search_csv(query, limit, budget, brand)

        api_results = self._search_api(query, limit)
        if api_results is not None:
            return api_results

        print(f"API failed, trying CSV fallback for query: {query}")
        return self._search_csv(query, limit, budget, brand)

    def status(self):
        csv_available = self.csv_data is not None and not self.csv_data.empty
        return {
            "api_limit_reached": self.api_limit_reached,
            "csv_fallback_available": csv_available,
            "csv_laptop_count": len(self.csv_data) if csv_available else 0,
            "current_mode": "CSV Fallback" if self.api_limit_reached else "API Mode",
        }

    def reset_api_limit(self):
        self.api_limit_reached = not self.techspecs_config.configured

    def _load_csv_data(self):
        try:
            if not os.path.exists(self.csv_file_path):
                print(f"CSV file not found: {self.csv_file_path}")
                return None

            data = pd.read_csv(self.csv_file_path)
            print(f"CSV data loaded. {len(data)} laptops available.")
            return data
        except Exception as error:
            print(f"Error loading CSV: {error}")
            return None

    def _search_api(self, query, limit):
        if not self.techspecs_config.configured:
            print("TechSpecs API credentials not configured.")
            return None

        try:
            response = requests.get(
                f"{self.techspecs_config.base_url}/products/search",
                headers=self.techspecs_config.headers,
                params={"q": query, "category": "Laptops"},
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                products = data.get("data") or []
                if not products:
                    print(f"No data found in API response for query: {query}")
                    return None

                results = [self._api_product_to_laptop(item) for item in products[:limit]]
                results = [item for item in results if item is not None]
                print(f"API success: Found {len(results)} results for '{query}'")
                return results

            if response.status_code == 402:
                print(f"API rate limit reached. Switching to CSV fallback for query: {query}")
                self.api_limit_reached = True
                return None

            print(f"API error {response.status_code} for query: {query}")
            return None
        except Exception as error:
            print(f"API error for query '{query}': {error}")
            return None

    def _search_csv(self, query, limit, budget=None, brand=None):
        if self.csv_data is None or self.csv_data.empty:
            print("CSV data not available for fallback")
            return []

        try:
            query_lower = query.lower()
            filtered = self.csv_data.copy()
            filtered["search_text"] = self._build_search_text(filtered)

            filtered = self._filter_handheld_devices(filtered, query_lower)
            filtered = self._filter_brand(filtered, brand)
            filtered = self._filter_budget(filtered, budget)
            filtered, keyword_found = self._filter_usage_or_keywords(filtered, query_lower, brand, budget)
            filtered = self._sort_results(filtered, keyword_found, budget)

            results = [
                self._csv_row_to_laptop(laptop, index)
                for index, (_, laptop) in enumerate(filtered.head(limit).iterrows())
            ]
            print(f"CSV fallback: Found {len(results)} results for '{query}'")
            return results
        except Exception as error:
            print(f"CSV search error: {error}")
            return []

    def _build_search_text(self, data):
        return (
            self._string_column(data, "Company") + " " +
            self._string_column(data, "Product") + " " +
            self._string_column(data, "TypeName") + " " +
            self._string_column(data, "CPU_Type") + " " +
            self._string_column(data, "GPU_Type")
        ).str.lower()

    def _filter_handheld_devices(self, data, query_lower):
        has_negative = any(negative in query_lower for negative in NEGATIVE_INDICATORS)
        wants_handheld = any(word in query_lower for word in HANDHELD_KEYWORDS) and not has_negative
        if wants_handheld:
            return data

        filtered = data
        product_names = self._string_column(filtered, "Product").str.lower()
        for device in HANDHELD_DEVICES:
            filtered = filtered[~product_names.str.contains(device, na=False)]
            product_names = self._string_column(filtered, "Product").str.lower()

        screen_sizes = pd.to_numeric(filtered["Inches"], errors="coerce")
        filtered = filtered[(screen_sizes >= 11) | (screen_sizes.isna())]
        print(f"Handheld devices filtered out -> {len(filtered)} laptops remaining")
        return filtered

    def _filter_brand(self, data, brand):
        if not brand or not brand.strip():
            return data

        filtered = data[self._string_column(data, "Company").str.lower().str.contains(brand.lower(), na=False)]
        print(f"Brand filter applied: {brand} -> {len(filtered)} laptops")
        return filtered

    def _filter_budget(self, data, budget):
        if not budget or budget <= 0:
            return data

        budget_euro = budget * 0.92
        prices = pd.to_numeric(data["Price (Euro)"], errors="coerce")
        filtered = data[prices <= budget_euro]
        print(f"Budget filter applied: ${budget} (EUR {budget_euro:.0f}) -> {len(filtered)} laptops")
        return filtered

    def _filter_usage_or_keywords(self, data, query_lower, brand, budget):
        if "gaming" in query_lower:
            return self._filter_gaming(data), False

        if "business" in query_lower or "work" in query_lower:
            pattern = "ultrabook|notebook|workstation"
            return data[self._contains(data, "TypeName", pattern)], False

        if "student" in query_lower or "budget" in query_lower:
            prices = pd.to_numeric(data["Price (Euro)"], errors="coerce")
            is_student_type = self._contains(data, "TypeName", "notebook|ultrabook")
            return data[(prices <= 1000) & is_student_type], False

        if query_lower in ["laptop", "laptops", ""]:
            return data, False

        original_size = len(data)
        important_words = [
            word for word in query_lower.split()
            if word not in STOP_WORDS and len(word) > 2
        ]

        for keyword in important_words:
            keyword_matches = data[data["search_text"].str.contains(keyword, case=False, na=False)]
            if keyword_matches.empty:
                continue

            exact_matches = keyword_matches[
                self._string_column(keyword_matches, "Product").str.contains(keyword, case=False, na=False)
            ]
            other_matches = keyword_matches.drop(exact_matches.index)
            filtered = pd.concat([exact_matches, other_matches]) if not exact_matches.empty else keyword_matches
            print(f"Keyword '{keyword}' found {len(filtered)} matches ({len(exact_matches)} exact)")
            return filtered, True

        if len(data) == original_size and not brand and not budget:
            substring_matches = data[data["search_text"].str.contains(query_lower, case=False, na=False)]
            if not substring_matches.empty:
                return substring_matches, False

            scores = data["search_text"].apply(lambda value: fuzz.partial_ratio(query_lower, value))
            matching_scores = scores[scores >= 25].sort_values(ascending=False)
            return data.loc[matching_scores.index], False

        return data, False

    def _filter_gaming(self, data):
        gaming = data[self._contains(data, "TypeName", "gaming")]
        if not gaming.empty:
            return gaming

        dedicated_gpu = (
            self._contains(data, "GPU_Type", "rtx|radeon|geforce") &
            ~self._contains(data, "GPU_Type", "intel|iris|uhd")
        )
        gaming = data[dedicated_gpu]
        if not gaming.empty:
            return gaming

        gpu_company = (
            self._contains(data, "GPU_Company", "nvidia|amd") &
            ~self._contains(data, "GPU_Company", "intel")
        )
        return data[gpu_company] if not data[gpu_company].empty else data

    def _sort_results(self, data, keyword_found, budget):
        if data.empty or keyword_found:
            return data

        sorted_data = data.copy()
        sorted_data["_price_euro"] = pd.to_numeric(sorted_data["Price (Euro)"], errors="coerce")

        if budget and budget > 3000:
            return sorted_data.sort_values("_price_euro", ascending=False).drop(columns=["_price_euro"])

        return sorted_data.sort_values("_price_euro", ascending=True).drop(columns=["_price_euro"])

    def _api_product_to_laptop(self, item):
        product = item.get("Product")
        if not product:
            return None

        return {
            "brand": product.get("Brand", "Unknown Brand"),
            "model": product.get("Model", "Unknown Model"),
            "category": product.get("Category", "Laptop"),
            "version": product.get("Version", ""),
            "id": product.get("id", ""),
            "image": item.get("Image", ""),
            "specifications": {},
        }

    def _csv_row_to_laptop(self, laptop, index):
        return {
            "brand": str(laptop.get("Company", "Unknown Brand")),
            "model": str(laptop.get("Product", "Unknown Model")),
            "category": str(laptop.get("TypeName", "Laptop")),
            "version": f"{laptop.get('CPU_Type', '')} | {laptop.get('RAM (GB)', '')}GB | {laptop.get('Memory', '')}",
            "id": f"csv_{index}",
            "image": "",
            "specifications": {
                "screen_size": self._format_value(laptop.get("Inches")),
                "resolution": str(laptop.get("ScreenResolution", "N/A")),
                "cpu": str(laptop.get("CPU_Type", "N/A")),
                "ram": self._format_value(laptop.get("RAM (GB)"), suffix="GB"),
                "storage": str(laptop.get("Memory", "N/A")),
                "gpu": str(laptop.get("GPU_Type", "N/A")),
                "os": str(laptop.get("OpSys", "N/A")),
                "weight": self._format_value(laptop.get("Weight (kg)"), suffix="kg"),
                "price": self._format_value(laptop.get("Price (Euro)"), prefix="EUR "),
            },
        }

    @staticmethod
    def _contains(data, column, pattern):
        return data[column].fillna("").astype(str).str.lower().str.contains(pattern, na=False, regex=True)

    @staticmethod
    def _string_column(data, column):
        return data[column].fillna("").astype(str)

    @staticmethod
    def _format_value(value, prefix="", suffix=""):
        if pd.isna(value):
            return "N/A"
        return f"{prefix}{value}{suffix}"
