#!/usr/bin/env python3
"""Generate comprehensive emoji data using the emoji library."""

import json
import os
import re
import emoji
from collections import defaultdict

def clean_emoji_name(raw_name):
    """Clean up emoji names from the library format."""
    name = raw_name.strip(':')
    name = name.replace('_', ' ')
    name = name.replace('&', 'and')
    name = ' '.join(word.capitalize() for word in name.split())
    return name

def extract_categories_from_name(raw_name):
    """Extract all categories from emoji name by splitting on underscores."""
    name = raw_name.strip(':')
    parts = name.split('_')

    # Clean up parts - remove numbers, short parts, and special cases
    categories = []
    for part in parts:
        # Skip numbers and very short parts
        if part.isdigit() or len(part) < 2:
            continue
        # Skip common connectors
        if part in ['with', 'and', 'of', 'for', 'in', 'on', 'at', 'to', 'by']:
            continue
        # Capitalize and add
        categories.append(part.capitalize())

    return categories

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

def generate_emoji_data():
    """Generate emoji data using the emoji library with categories extracted from names."""
    all_emojis = []
    seen = set()
    category_counts = defaultdict(int)

    # Get all emojis from the library
    all_emoji_data = emoji.EMOJI_DATA

    # First pass: collect all emojis and count categories
    for emoji_char, data in all_emoji_data.items():
        if emoji_char in seen:
            continue

        try:
            raw_name = data.get('en', '')
            if not raw_name or raw_name == emoji_char:
                continue

            name = clean_emoji_name(raw_name)
            if not name:
                continue

            # Extract categories from the name
            categories = extract_categories_from_name(raw_name)

            all_emojis.append({
                "emoji": emoji_char,
                "name": name,
                "raw_name": raw_name,
                "categories": categories,
            })
            seen.add(emoji_char)

            # Count categories
            for cat in categories:
                category_counts[cat] += 1
        except Exception as e:
            pass

    # Filter categories to only those with 3+ emojis
    valid_categories = {cat for cat, count in category_counts.items() if count >= 3}

    # Assign primary category (first valid one, or "Other")
    for emoji_item in all_emojis:
        valid_cats = [cat for cat in emoji_item['categories'] if cat in valid_categories]
        emoji_item['category'] = valid_cats[0] if valid_cats else 'Other'

    # Remove the temporary fields
    for emoji_item in all_emojis:
        del emoji_item['raw_name']
        del emoji_item['categories']

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
