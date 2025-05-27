#!/usr/bin/env python3
"""
Demonstration of enhanced PII detection that shows users exactly what sensitive
information was detected in their message instead of generic examples.
"""

import json
from datetime import datetime


def simulate_enhanced_pii_detection():
    """Simulate the enhanced PII detection system."""

    print("🔍 ENHANCED SENSITIVE INFORMATION DETECTION DEMO")
    print("=" * 60)
    print(f"Demo started at: {datetime.utcnow()}")
    print()

    # Simulate user input with various types of sensitive information
    user_message = """Hi, I'm Sarah Johnson from Boston. My therapist Dr. Martinez at Mass General Hospital prescribed Zoloft for my depression. I work at Google and my insurance is Blue Cross. My mom Lisa has been really supportive. You can reach me at sarah.j@email.com or 617-555-1234."""

    print("📝 USER MESSAGE:")
    print(f'"{user_message}"')
    print()

    # Simulate what the enhanced system would detect
    detected_info = [
        {"text": "Sarah Johnson", "type": "PERSON", "category": "personal_identity"},
        {
            "text": "Dr. Martinez",
            "type": "HEALTHCARE_PROVIDER",
            "category": "medical_information",
        },
        {
            "text": "Mass General Hospital",
            "type": "MEDICAL_FACILITY",
            "category": "location_information",
        },
        {"text": "Zoloft", "type": "MEDICATION", "category": "medical_information"},
        {
            "text": "depression",
            "type": "MENTAL_HEALTH_DIAGNOSIS",
            "category": "medical_information",
        },
        {
            "text": "Google",
            "type": "WORKPLACE_INFO",
            "category": "location_information",
        },
        {
            "text": "Blue Cross",
            "type": "INSURANCE_INFO",
            "category": "financial_information",
        },
        {"text": "mom Lisa", "type": "FAMILY_MEMBER", "category": "personal_identity"},
        {
            "text": "sarah.j@email.com",
            "type": "EMAIL_ADDRESS",
            "category": "contact_information",
        },
        {"text": "617-555-1234", "type": "PHONE", "category": "contact_information"},
        {"text": "Boston", "type": "LOCATION", "category": "location_information"},
    ]

    # Show what OLD system displayed
    print("❌ OLD SYSTEM (generic examples):")
    print("Categories detected with generic examples:")
    print("- Personal Identity: ['John Smith', 'my mom Sarah']")
    print("- Medical Information: ['medications', 'diagnoses', 'doctor names']")
    print("- Contact Information: ['email addresses', 'phone numbers']")
    print("❌ User has no idea what specific information was detected!")
    print()

    # Show what NEW system displays
    print("✅ NEW SYSTEM (actual detected information):")

    # Group by categories
    categories = {}
    for item in detected_info:
        category = item["category"]
        if category not in categories:
            categories[category] = []
        categories[category].append(item)

    # Create summary message
    sensitive_items = [f'"{item["text"]}"' for item in detected_info[:5]]
    if len(detected_info) > 5:
        sensitive_items.append(f"and {len(detected_info) - 5} more items")

    summary_message = f"I detected sensitive personal information in your message: {', '.join(sensitive_items)}. You can choose what to keep and what to make private:"

    print("🚨 DETECTION SUMMARY:")
    print(summary_message)
    print()

    print("📋 DETECTED SENSITIVE INFORMATION BY CATEGORY:")
    print()

    category_descriptions = {
        "personal_identity": "Names of people (yours and others)",
        "medical_information": "Medical and mental health information",
        "contact_information": "Contact details",
        "financial_information": "Financial and insurance details",
        "location_information": "Places and locations",
    }

    for category, items in categories.items():
        print(f"🏷️  {category.replace('_', ' ').title()}")
        print(
            f"   Description: {category_descriptions.get(category, 'Various information')}"
        )
        print("   Detected items:")
        for item in items:
            print(f'   • "{item["text"]}" ({item["type"]})')
        print(f"   Default choice: ❌ Make private (anonymize)")
        print()

    # Show the user choice interface
    print("🎛️  USER CONSENT INTERFACE:")
    print("For each category, you can choose:")
    print("[ ] Keep original text")
    print("[✓] Make private (replace with <PLACEHOLDER>)")
    print()

    # Show example of selective anonymization
    print("📋 EXAMPLE USER CHOICES:")
    print("✅ Personal Identity → Keep (user wants to keep their name)")
    print("❌ Medical Information → Make private")
    print("❌ Contact Information → Make private")
    print("✅ Location Information → Keep (general locations OK)")
    print("❌ Financial Information → Make private")
    print()

    # Show result after selective anonymization
    result_text = """Hi, I'm Sarah Johnson from Boston. My <HEALTHCARE_PROVIDER> at Mass General Hospital prescribed <MEDICATION> for my <MENTAL_HEALTH_DIAGNOSIS>. I work at Google and my insurance is <INSURANCE_INFO>. My <FAMILY_MEMBER> has been really supportive. You can reach me at <EMAIL_ADDRESS> or <PHONE>."""

    print("🎯 FINAL RESULT (after selective anonymization):")
    print(f'"{result_text}"')
    print()

    print("✅ BENEFITS OF NEW APPROACH:")
    print("- User sees exactly what sensitive data was detected")
    print("- Full transparency about what information was found")
    print("- Granular control over each category")
    print("- No surprises about what gets anonymized")
    print("- User can make informed privacy decisions")


def show_detection_report_example():
    """Show example of detailed detection report."""
    print("\n🔬 DETAILED DETECTION REPORT EXAMPLE")
    print("-" * 45)

    report = {
        "has_sensitive_info": True,
        "total_entities_detected": 11,
        "summary": {
            "total_items": 10,
            "categories_affected": 5,
            "most_sensitive": ["Sarah Johnson", "Dr. Martinez", "Zoloft"],
        },
        "significant_entities": [
            {"text": "Sarah Johnson", "type": "PERSON", "confidence": 0.95},
            {"text": "Dr. Martinez", "type": "HEALTHCARE_PROVIDER", "confidence": 0.89},
            {"text": "Zoloft", "type": "MEDICATION", "confidence": 0.92},
            {
                "text": "depression",
                "type": "MENTAL_HEALTH_DIAGNOSIS",
                "confidence": 0.87,
            },
            {"text": "sarah.j@email.com", "type": "EMAIL_ADDRESS", "confidence": 0.99},
        ],
        "non_significant_entities": [
            {"text": "therapy", "type": "THERAPY_TYPE", "confidence": 0.78}
        ],
    }

    print("Report Summary:")
    print(f"• Total entities detected: {report['total_entities_detected']}")
    print(f"• Significant (needs consent): {len(report['significant_entities'])}")
    print(f"• Non-significant (safe): {len(report['non_significant_entities'])}")
    print()

    print("Most sensitive items found:")
    for item in report["summary"]["most_sensitive"]:
        print(f"  ⚠️  '{item}'")


def main():
    """Main demonstration function."""
    simulate_enhanced_pii_detection()
    show_detection_report_example()

    print("\n🎉 CONCLUSION:")
    print("=" * 15)
    print("The enhanced system provides complete transparency about")
    print("what sensitive information was detected, giving users")
    print("full control over their privacy decisions.")
    print()
    print("Users now see EXACTLY what was found instead of generic examples!")


if __name__ == "__main__":
    main()
