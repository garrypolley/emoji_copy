#!/usr/bin/env python3
"""Generate comprehensive emoji data using official Unicode emoji data."""

import json
import emoji
import re
import urllib.request

def clean_emoji_name(raw_name):
    """Clean up emoji names from the library format."""
    name = raw_name.strip(':')
    name = name.replace('_', ' ')
    name = ' '.join(word.capitalize() for word in name.split())
    return name

def get_base_name(emoji_name):
    """Extract base name from emoji, removing variant indicators."""
    name = emoji_name

    # Remove skin tone modifiers
    name = re.sub(r'\s+(Light|Medium\s+Light|Medium|Medium\s+Dark|Dark)\s+Skin\s+Tone.*$', '', name)

    # Remove hair style variants
    name = re.sub(r'\s+(Red|Curly|Wavy|Straight)\s+Hair.*$', '', name)

    # Remove gender prefixes but keep what comes after
    name = re.sub(r'^(Person|Man|Woman|Non.?Binary)\s+', '', name)

    # Remove common color suffixes
    name = re.sub(r'\s+(Red|Orange|Yellow|Green|Blue|Purple|Brown|Black|White|Light|Dark|Medium)$', '', name)

    # Remove trailing modifiers
    name = re.sub(r'\s+(Facing|Toward|Light|Dark)$', '', name)

    return name.strip()

def should_group(base_name, full_name):
    """Check if emoji should be grouped as a variant."""
    if base_name == full_name:
        return False

    has_variant = any(x in full_name for x in [
        'Skin Tone', 'Hair', 'Red', 'Orange', 'Yellow', 'Green', 'Blue',
        'Purple', 'Brown', 'Black', 'White', 'Curly', 'Wavy', 'Straight'
    ])

    return has_variant

def fetch_unicode_emoji_data():
    """Fetch official Unicode emoji test data with categories and subgroups."""
    try:
        url = "https://www.unicode.org/Public/17.0.0/emoji/emoji-test.txt"
        print(f"Fetching Unicode emoji data from {url}...")

        with urllib.request.urlopen(url) as response:
            data = response.read().decode('utf-8')

        # Parse the emoji-test.txt format
        # Format: code_point ; status ; emoji ; name
        # Also extract group and subgroup from comments
        emoji_to_category = {}
        current_group = "Symbols"
        current_subgroup = "Other"

        for line in data.split('\n'):
            line = line.strip()

            # Extract group from comment lines like: # group: Smileys & Emotion
            if line.startswith('# group:'):
                current_group = line.split('group:')[1].strip()
                continue

            # Extract subgroup from comment lines like: # subgroup: face-smiling
            if line.startswith('# subgroup:'):
                current_subgroup = line.split('subgroup:')[1].strip()
                continue

            if not line or line.startswith('#'):
                continue

            if ';' in line:
                parts = [p.strip() for p in line.split(';')]
                if len(parts) >= 4:
                    code_point_str = parts[0]
                    status = parts[1]

                    try:
                        # Handle code points (can be multiple like "1F1E6 1F1E8")
                        code_points = code_point_str.split()
                        if code_points:
                            # Get the first code point to determine category
                            first_cp = int(code_points[0], 16)
                            emoji_char = chr(first_cp)

                            if emoji_char not in emoji_to_category:
                                emoji_to_category[emoji_char] = current_group
                    except:
                        pass

        return emoji_to_category
    except Exception as e:
        print(f"Failed to fetch Unicode data: {e}")
        return {}

def get_category_from_name(emoji_name):
    """Get category based on emoji name."""
    name = emoji_name.lower()

    if any(x in name for x in ['face', 'smile', 'grin', 'laugh', 'cry', 'eye', 'mouth']):
        return "Smileys & Emotions"
    elif any(x in name for x in ['animal', 'cat', 'dog', 'bird', 'monkey', 'bear', 'panda', 'fish', 'bug', 'butterfly', 'lion', 'tiger', 'whale', 'shark', 'snake', 'frog', 'penguin']):
        return "Animals & Nature"
    elif any(x in name for x in ['plant', 'tree', 'flower', 'leaf', 'mushroom', 'cactus', 'herb', 'clover']):
        return "Animals & Nature"
    elif any(x in name for x in ['food', 'fruit', 'pizza', 'burger', 'rice', 'bread', 'apple', 'orange', 'banana', 'watermelon', 'grape', 'strawberry', 'meat', 'cake', 'candy', 'coffee', 'beer', 'wine']):
        return "Food & Drink"
    elif any(x in name for x in ['car', 'train', 'bus', 'airplane', 'rocket', 'ship', 'boat', 'bicycle', 'motorcycle', 'taxi', 'truck', 'travel']):
        return "Travel & Places"
    elif any(x in name for x in ['flag', 'country']):
        return "Flags"
    elif any(x in name for x in ['heart', 'star', 'diamond', 'gem', 'sparkle', 'sun', 'moon', 'cloud', 'fire', 'water', 'arrow', 'check', 'cross']):
        return "Symbols"
    else:
        return "Symbols"

def generate_emoji_data():
    """Generate emoji data using the emoji library with proper categories from Unicode data."""
    all_emojis = []
    seen = set()

    # Fetch Unicode category mapping
    unicode_categories = fetch_unicode_emoji_data()

    # Get all emojis from the library
    all_emoji_data = emoji.EMOJI_DATA

    for emoji_char, data in all_emoji_data.items():
        if emoji_char in seen:
            continue

        try:
            raw_name = data.get('en', emoji_char)
            name = clean_emoji_name(raw_name)

            if name == emoji_char or not name:
                continue

            # Get category from Unicode data first, fall back to name-based categorization
            if emoji_char in unicode_categories:
                category = unicode_categories[emoji_char]
            else:
                category = get_category_from_name(name)

            all_emojis.append({
                "emoji": emoji_char,
                "name": name,
                "category": category,
            })
            seen.add(emoji_char)
        except Exception as e:
            pass

    # Group variants
    grouped_emojis = {}
    variants_map = {}

    for emoji_item in all_emojis:
        name = emoji_item["name"]
        category = emoji_item["category"]
        base_name = get_base_name(name)

        if should_group(base_name, name):
            # This is a variant
            if base_name not in variants_map:
                variants_map[base_name] = []
            variants_map[base_name].append(emoji_item)
        else:
            # This is a base emoji
            if base_name not in grouped_emojis:
                grouped_emojis[base_name] = {
                    "emoji": emoji_item["emoji"],
                    "name": name,
                    "variants": [],
                    "category": category,
                    "searchable": f"{emoji_item['emoji']} {name}".lower()
                }

    # Add variants to their base emojis
    for base_name, variants in variants_map.items():
        if base_name in grouped_emojis:
            for variant in variants:
                grouped_emojis[base_name]["variants"].append({
                    "emoji": variant["emoji"],
                    "name": variant["name"]
                })
        else:
            # If base doesn't exist, create it from first variant
            if variants:
                first = variants[0]
                grouped_emojis[base_name] = {
                    "emoji": first["emoji"],
                    "name": base_name,
                    "variants": [{"emoji": v["emoji"], "name": v["name"]} for v in variants],
                    "category": first["category"],
                    "searchable": f"{first['emoji']} {base_name}".lower()
                }

    # Convert to list, sorted by category then name
    final_emojis = sorted(
        grouped_emojis.values(),
        key=lambda x: (x["category"], x["name"])
    )

    # Build category list
    categories = sorted(set(e["category"] for e in final_emojis))

    return {
        "emojis": final_emojis,
        "categories": categories,
        "totalCount": len(final_emojis),
        "variantCount": sum(len(e.get("variants", [])) for e in final_emojis)
    }

if __name__ == "__main__":
    data = generate_emoji_data()

    with open("emojis.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Generated {data['totalCount']} base emojis with {data['variantCount']} variants across {len(data['categories'])} categories:")
    for cat in data['categories']:
        count = sum(1 for e in data['emojis'] if e['category'] == cat)
        print(f"  - {cat}: {count}")
    print("Saved to emojis.json")
