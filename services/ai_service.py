import openai
import json
import os
import datetime
from typing import List


class AIService:
    def __init__(self, config):
        self.config = config
        self.client = None
        self.initialize_client()
    
    def initialize_client(self):
        """Initialize Azure OpenAI client"""
        azure_api_key = self.config['api_keys'].get('azure_openai_key')
        azure_endpoint = self.config['api_keys'].get('azure_openai_endpoint')
        
        if not azure_api_key or not azure_endpoint:
            # Fallback to regular OpenAI
            openai_key = self.config['api_keys'].get('openai')
            if not openai_key:
                raise ValueError("Neither Azure OpenAI nor OpenAI API key configured in config.yaml")
            
            print("🔄 Using regular OpenAI API")
            self.client = openai.OpenAI(api_key=openai_key)
        else:
            print("🔄 Using Azure OpenAI API")
            self.client = openai.AzureOpenAI(
                api_key=azure_api_key,
                azure_endpoint=azure_endpoint,
                api_version="2024-02-01"
            )
    
    def get_items_list(self, prompt: str, max_items: int = 30) -> List[str]:
        """
        Generate a list of items based on the prompt
        
        Args:
            prompt: The topic/category (e.g., "body parts", "animals", "colors")
            max_items: Maximum number of items to generate
            
        Returns:
            List of item names
        """
        try:
            # Check cache first
            cache_key = f"{prompt}_{max_items}".replace(" ", "_").lower()
            cache_file = os.path.join('cache', f'{cache_key}.json')
            
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                    items = cached_data.get('items', [])
                    if isinstance(items, list):
                        print(f"Loaded {len(items)} items from cache")
                        return items
                    else:
                        print(f"Cache data invalid, items is not a list: {type(items)}")
                        # Remove invalid cache file
                        os.remove(cache_file)
            
            # Generate new list using AI
            system_prompt = f"""
            Generate a list of {max_items} common and educational items for the category: "{prompt}".
            
            Requirements:
            - Items should be simple, clear, and educational
            - Suitable for flashcards/learning
            - Each item should be 1-3 words maximum
            - No duplicates
            - Return ONLY a JSON array of strings
            - No explanations or additional text
            
            Example format: ["item1", "item2", "item3"]
            """
            
            # Use deployment name for Azure OpenAI, model name for regular OpenAI
            model_name = self.config['api_keys'].get('azure_openai_deployment', 'gpt-4')
            
            response = self.client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Generate items for: {prompt}"}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            # Parse the response
            content = response.choices[0].message.content.strip()
            
            # Try to extract JSON from the response
            try:
                # Remove any markdown formatting
                if content.startswith('```json'):
                    content = content[7:]
                if content.endswith('```'):
                    content = content[:-3]
                
                items = json.loads(content)
                
                if not isinstance(items, list):
                    raise ValueError("Response is not a list")
                
                # Limit to max_items
                items = items[:max_items]
                
                # Cache the result
                os.makedirs('cache', exist_ok=True)
                cache_data = {
                    'prompt': prompt,
                    'items': items,
                    'generated_at': datetime.datetime.now().isoformat()
                }
                
                with open(cache_file, 'w') as f:
                    json.dump(cache_data, f, indent=2)
                
                print(f"Generated {len(items)} items for '{prompt}'")
                return items
                
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON response: {e}")
                print(f"Raw response: {content}")
                
                # Fallback: try to extract items from text
                lines = content.split('\n')
                items = []
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#') and not line.startswith('//'):
                        # Remove quotes and clean up
                        item = line.strip('"\'[](),')
                        if item and len(item.split()) <= 3:
                            items.append(item)
                
                return items[:max_items] if items else self._get_fallback_items(prompt, max_items)
                
        except Exception as e:
            error_msg = str(e)
            print(f"Error generating items: {e}")
            
            # Check if it's a quota/billing error
            if 'quota' in error_msg.lower() or 'billing' in error_msg.lower():
                print("🚨 OpenAI API quota exceeded - using fallback content")
            elif 'rate_limit' in error_msg.lower():
                print("🚨 OpenAI API rate limit exceeded - using fallback content")
            else:
                print("🚨 OpenAI API error - using fallback content")
                
            return self._get_fallback_items(prompt, max_items)
    
    def _get_fallback_items(self, prompt: str, max_items: int) -> List[str]:
        """Fallback items when AI generation fails"""
        fallback_data = {
            'body parts': ['head', 'eyes', 'nose', 'mouth', 'ears', 'neck', 'shoulders', 'arms', 'hands', 'fingers', 'chest', 'stomach', 'back', 'legs', 'knees', 'feet', 'toes'],
            'animals': ['cat', 'dog', 'bird', 'fish', 'elephant', 'lion', 'tiger', 'bear', 'rabbit', 'horse', 'cow', 'pig', 'sheep', 'chicken', 'duck'],
            'colors': ['red', 'blue', 'green', 'yellow', 'orange', 'purple', 'pink', 'brown', 'black', 'white', 'gray'],
            'fruits': ['apple', 'banana', 'orange', 'strawberry', 'grape', 'watermelon', 'pineapple', 'mango', 'peach', 'cherry'],
            'vegetables': ['carrot', 'broccoli', 'tomato', 'potato', 'onion', 'lettuce', 'cucumber', 'pepper', 'corn', 'peas'],
            'seasons': ['spring', 'summer', 'autumn', 'winter', 'blooming', 'sunshine', 'leaves', 'snow', 'rain', 'flowers', 'harvest', 'frost', 'warmth', 'cold', 'breeze'],
            'weather': ['sunny', 'cloudy', 'rainy', 'snowy', 'windy', 'stormy', 'foggy', 'humid', 'dry', 'hot', 'cold', 'warm', 'cool', 'freezing', 'thunder'],
            'nature': ['tree', 'flower', 'grass', 'mountain', 'river', 'ocean', 'forest', 'desert', 'valley', 'lake', 'beach', 'sky', 'cloud', 'sun', 'moon']
        }
        
        # Find the best match with more flexible matching
        prompt_lower = prompt.lower()
        
        # Direct key matches
        for key, items in fallback_data.items():
            if key in prompt_lower or prompt_lower in key:
                print(f"📝 Using fallback data for '{key}' based on prompt '{prompt}'")
                return items[:max_items]
        
        # Keyword-based matching
        keyword_mappings = {
            'season': 'seasons',
            'seasonal': 'seasons',
            'weather': 'weather',
            'nature': 'nature',
            'outdoor': 'nature',
            'animal': 'animals',
            'pet': 'animals',
            'color': 'colors',
            'colour': 'colors',
            'fruit': 'fruits',
            'vegetable': 'vegetables',
            'body': 'body parts',
            'anatomy': 'body parts'
        }
        
        for keyword, category in keyword_mappings.items():
            if keyword in prompt_lower:
                print(f"📝 Using fallback data for '{category}' based on keyword '{keyword}' in prompt '{prompt}'")
                return fallback_data[category][:max_items]
        
        # Default fallback - use a more generic list instead of body parts
        print(f"⚠️ No specific fallback found for '{prompt}', using generic nature items")
        return fallback_data['nature'][:max_items]
