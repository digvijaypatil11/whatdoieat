import json

# Data Quality Hotfix: Corrected signature flags on items
data = {
  "restaurant_name": "Sangam Chettinad Indian Cuisine",
  "cuisine_type": "Authentic South Indian & Chettinad",
  "location": "6001 W Parmer Ln Ste 140, Austin, TX 78727",
  "phone": "+1 512-770-1104",
  "last_updated": "2026-06-05",
  "hours": {
    "Weekday_Lunch": "11:30 AM - 2:30 PM",
    "Weekday_Dinner": "5:30 PM - 10:00 PM (Friday until 10:30 PM)",
    "Weekend_Breakfast_Tiffin": "8:30 AM - 10:00 AM",
    "Weekend_Lunch": "12:00 PM - 3:00 PM",
    "Weekend_Dinner": "5:30 PM - 10:00 PM (Saturday until 10:30 PM)"
  },
  "dietary_tags": ["Vegetarian", "Vegan Options", "Gluten-Free Friendly", "Dairy-Free Options"],
  "known_unlisted_items": [
    {
      "name": "Saag",
      "note": "Off-menu or seasonal item mentioned in customer reviews. Not part of the standard catalog."
    }
  ],
  "menu": [
    {
      "category": "Steamed Tiffin & Vegetarian Starters",
      "items": [
        {
          "name": "3-Piece Idli",
          "price": 9.95,
          "description": "Traditional steamed savory rice cakes made from a fermented black lentil (urad dal) and rice batter. Served hot with a side of sambar and three varieties of house chutneys.",
          "tags": ["Vegetarian", "Vegan", "Gluten-Free"],
          "spice_level": "none",
          "is_signature": False,
          "mentioned_in_reviews": [],
          "popular": False
        },
        {
          "name": "Medhu Vadai (3 pieces)",
          "price": 9.95,
          "description": "Crispy, deep-fried South Indian savory donuts made from split black lentil batter, infused with black pepper, ginger, and curry leaves.",
          "tags": ["Vegetarian", "Vegan", "Gluten-Free"],
          "spice_level": "mild",
          "is_signature": False,
          "mentioned_in_reviews": [],
          "popular": False
        },
        {
          "name": "Traditional Samosas (2 pieces)",
          "price": 6.45,
          "description": "Crispy pastry turnovers filled with a savory spiced potato and pea mixture.",
          "tags": ["Vegetarian", "Vegan Option"],
          "spice_level": "mild",
          "is_signature": False,
          "mentioned_in_reviews": ["rev_sangam_001"],
          "popular": True
        },
        {
          "name": "Gobi 65",
          "price": 12.45,
          "description": "Fresh cauliflower florets marinated in a spicy, house-blend Chettinad masala and deep-fried to crispy perfection.",
          "tags": ["Vegetarian", "Vegan Option"],
          "spice_level": "medium",
          "is_signature": False,
          "mentioned_in_reviews": [],
          "popular": False
        }
      ]
    },
    {
      "category": "South Indian Tiffin Crepes (Dosas & Uthappams)",
      "items": [
        {
          "name": "Masala Dosa",
          "price": 13.45,
          "description": "A thin, crispy golden rice and lentil crepe stuffed with a mildly spiced, aromatic mashed potato and onion masala.",
          "tags": ["Vegetarian", "Gluten-Free"],
          "spice_level": "mild",
          "is_signature": True,
          "mentioned_in_reviews": ["rev_sangam_001", "rev_sangam_004"],
          "popular": True
        },
        {
          "name": "Mysore Masala Dosa",
          "price": 14.45,
          "description": "A variant of the classic crisp dosa layered with a fiery, vibrant red garlic and spice chutney on the inside before being filled with spiced potato masala.",
          "tags": ["Vegetarian", "Gluten-Free"],
          "spice_level": "hot",
          "is_signature": False,
          "mentioned_in_reviews": [],
          "popular": False
        },
        {
          "name": "Onion Chili Uthappam",
          "price": 13.95,
          "description": "Thick, pancake-like South Indian rice crepe topped with a generous layer of finely chopped red onions and hot green chilies, cooked directly into the batter.",
          "tags": ["Vegetarian", "Gluten-Free"],
          "spice_level": "hot",
          "is_signature": False,
          "mentioned_in_reviews": ["rev_sangam_005"],
          "popular": False
        }
      ]
    },
    {
      "category": "Non-Vegetarian Appetizers",
      "items": [
        {
          "name": "Chennai Style Chicken 65",
          "price": 17.45,
          "description": "Tender, boneless chicken cubes marinated in a deep red blend of ginger, garlic, yogurt, and fiery Southern Indian spices, fried to a juicy crisp.",
          "tags": ["Nut-Free"],
          "spice_level": "medium",
          "is_signature": False,
          "mentioned_in_reviews": [],
          "popular": False
        },
        {
          "name": "Sangam Special Pepper Chicken (Dry)",
          "price": 18.45,
          "description": "A signature dry appetizer featuring tender boneless chicken wok-tossed with freshly crushed black pepper, caramelized shallots, garlic, and traditional Chettinad spices.",
          "tags": ["Gluten-Free"],
          "spice_level": "hot",
          "is_signature": True,
          "mentioned_in_reviews": [],
          "popular": True
        },
        {
          "name": "Chettinad Mutton Kola Urundai",
          "price": 19.45,
          "description": "Minced goat meat combined with aromatic spices, fresh herbs, and finely chopped shallots, shaped into round balls and fried until deeply crisp on the outside.",
          "tags": ["Nut-Free"],
          "spice_level": "medium",
          "is_signature": False,
          "mentioned_in_reviews": [],
          "popular": False
        }
      ]
    },
    {
      "category": "Traditional Chettinad & Regional Entrees",
      "items": [
        {
          "name": "Chicken Chettinad Curry",
          "price": 14.45,
          "description": "A classic, complex Southern Indian curry made with fresh chicken simmered in a dark, intensely aromatic gravy of roasted coconut paste, fennel, and star anise.",
          "tags": ["Gluten-Free"],
          "spice_level": "hot",
          "is_signature": True, # Confirmed True
          "mentioned_in_reviews": [],
          "popular": True # Confirmed True
        },
        {
          "name": "Chicken Tikka Masala",
          "price": 15.95,
          "description": "Chunks of roasted marinated chicken cooked in a smooth, mildly spiced, creamy tomato sauce.",
          "tags": ["Gluten-Free", "Nut-Free"],
          "spice_level": "medium",
          "is_signature": False,
          "mentioned_in_reviews": ["rev_sangam_001", "rev_sangam_003"],
          "popular": True
        },
        {
          "name": "Mutton Sukka Varuval",
          "price": 22.45,
          "description": "Tender, succulent chunks of boneless goat meat pan-roasted to a semi-dry consistency with an overload of caramelized onions, garlic, ginger, and signature Chettinad spices.",
          "tags": ["Gluten-Free"],
          "spice_level": "hot",
          "is_signature": True,
          "mentioned_in_reviews": [],
          "popular": True
        },
        {
          "name": "Ennai Kathirikai Kulambu",
          "price": 13.95,
          "description": "Whole baby eggplants lightly fried and stuffed with a rich ground masala paste, simmered slowly in a tangy, deeply savory tamarind and oil gravy.",
          "tags": ["Vegetarian", "Vegan", "Gluten-Free"],
          "spice_level": "medium",
          "is_signature": False,
          "mentioned_in_reviews": [],
          "popular": False
        }
      ]
    },
    {
      "category": "Breads & Rice",
      "items": [
        {
          "name": "Parotta (2 pieces)",
          "price": 4.45,
          "description": "A famous South Indian layered flatbread made from refined flour, skillfully stretched, rolled, and pan-griddled with ghee until flaky and multi-layered.",
          "tags": ["Vegetarian"],
          "spice_level": "none",
          "is_signature": False, # Hotfixed to False
          "mentioned_in_reviews": [],
          "popular": False
        },
        {
          "name": "Garlic Naan",
          "price": 4.45,
          "description": "Soft and pillowy leavened flatbread baked freshly in a clay tandoor oven, brushed with melted butter and topped with plenty of minced aromatic garlic.",
          "tags": ["Vegetarian"],
          "spice_level": "none",
          "is_signature": False,
          "mentioned_in_reviews": [],
          "popular": False
        },
        {
          "name": "Chicken Biryani",
          "price": 13.45,
          "description": "Fragrant long-grain basmati rice cooked layered over marinated chicken, infused with a blend of whole spices, mint, coriander, and saffron.",
          "tags": ["Gluten-Free"],
          "spice_level": "medium",
          "is_signature": True, # Confirmed True
          "mentioned_in_reviews": ["rev_sangam_004"],
          "popular": True # Confirmed True
        }
      ]
    }
  ],
  "google_reviews": [
    {
      "review_id": "rev_sangam_001",
      "author": "Adrienne K.",
      "rating": 5,
      "timestamp": "2024-11-25",
      "text": "This is hands down our favorite Indian place in north Austin and it is always packed for a reason! The Chicken Tikka Masala is excellent—not overwhelmingly sweet or creamy, and has a great medium spice level. The samosas were incredibly crispy and the Masala Dosa was perfectly tasty and huge."
    },
    {
      "review_id": "rev_sangam_002",
      "author": "Sohaila N.",
      "rating": 5,
      "timestamp": "2025-03-10",
      "text": "The most authentic South Indian food in Austin by a long shot! We've come here for breakfast, lunch, and dinner, and have loved it every time. Their weekend banana leaf breakfast feast was absolute heaven. Come hungry because the portions are incredibly generous and the staff are wonderful."
    },
    {
      "review_id": "rev_sangam_003",
      "author": "Catherine E.",
      "rating": 3,
      "timestamp": "2026-02-09",
      "text": "The packaging for delivery was excellent, but I personally found the curries a little bland for my taste (specifically the saag and tikka masala). They tasted a lot better as leftovers the next day once the flavors settled. I wasn't a fan of the huge onions and green peppers in the gravy, but the portion sizing was good."
    },
    {
      "review_id": "rev_sangam_004",
      "author": "Roger M.",
      "rating": 5,
      "timestamp": "2024-09-21",
      "text": "The attention to detail and food quality here are exceptional. I ordered the plain biryani rice (Kuska) and a Masala Dosa. To my delight, they packed everything beautifully and included delicious potato masala inside the dosa. The accompanying chutneys and sambar were phenomenal. Eat the dosa immediately while it's still crisp!"
    },
    {
      "review_id": "rev_sangam_005",
      "author": "Saif M.",
      "rating": 2,
      "timestamp": "2025-09-21",
      "text": "Highly disappointed with the pricing and sizing of the Tiffin items lately. I ordered the Uthappam and got 2 small pancakes for nearly $15. The taste is totally fine, but the quantity has drastically reduced from what they used to serve. The chutneys are tiny now too. They need to either make the utthapams larger or drop the price back down."
    }
  ]
}

# Overwrite the data with clean records
file_name = "sangam_chettinad_data.json"
with open(file_name, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4)

print(f"Data Quality Fix complete! Clean data written to '{file_name}'.")