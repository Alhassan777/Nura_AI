#!/usr/bin/env python3

import os
import re


def fix_pii_detector_tests():
    """Fix all PII detector tests to use the correct method and field names."""

    test_files = [
        "tests/unit/services/test_pii_detector.py",
        "tests/unit/services/test_pii_detector_phase2.py",
        "tests/unit/services/test_pii_detector_corrected.py",
        "tests/unit/services/test_pii_detector_final.py",
    ]

    for file_path in test_files:
        if not os.path.exists(file_path):
            print(f"Skipping {file_path} - file not found")
            continue

        print(f"Fixing {file_path}...")

        with open(file_path, "r") as f:
            content = f.read()

        # Add imports at the top if not present
        if "from backend.services.memory.types import MemoryItem" not in content:
            # Find the imports section and add our import
            import_pattern = r"(from backend\.services\.memory\.security\.pii_detector import PIIDetector)"
            replacement = r"\1\nfrom backend.services.memory.types import MemoryItem\nfrom datetime import datetime\nimport uuid"
            content = re.sub(import_pattern, replacement, content)

        # Replace all calls to detect_pii_in_text with proper MemoryItem creation
        pattern = r"result = await pii_detector\.detect_pii_in_text\(([^)]+)\)"

        def replace_call(match):
            content_var = match.group(1)
            return f"""# Create a MemoryItem for testing
        memory_item = MemoryItem(
            id=str(uuid.uuid4()),
            userId="test_user", 
            content={content_var},
            type="test",
            metadata={{}},
            timestamp=datetime.utcnow()
        )
        
        result = await pii_detector.detect_pii(memory_item)"""

        content = re.sub(pattern, replace_call, content)

        # Replace field names
        content = content.replace('result["pii_items"]', 'result["detected_items"]')
        content = content.replace('item["entity_type"]', 'item["type"]')

        # Fix risk_level access - it's not directly in result, need to calculate it
        risk_level_pattern = r'assert result\["risk_level"\] == "([^"]+)"'

        def replace_risk_level(match):
            expected_risk = match.group(1)
            return f"""# Calculate overall risk level
        risk_levels = [item["risk_level"] for item in result["detected_items"]]
        overall_risk = "high" if "high" in risk_levels else ("medium" if "medium" in risk_levels else "low")
        assert overall_risk == "{expected_risk}" """

        content = re.sub(risk_level_pattern, replace_risk_level, content)

        # Fix other risk_level references
        content = re.sub(
            r'assert result\["risk_level"\] in \[([^\]]+)\]',
            r'# Calculate overall risk level\n        risk_levels = [item["risk_level"] for item in result["detected_items"]]\n        overall_risk = "high" if "high" in risk_levels else ("medium" if "medium" in risk_levels else "low")\n        assert overall_risk in [\1]',
            content,
        )

        # Fix simple risk_level checks
        content = re.sub(
            r'if result\["has_pii"\]:\s+assert result\["risk_level"\]',
            r'if result["has_pii"]:\n                risk_levels = [item["risk_level"] for item in result["detected_items"]]\n                overall_risk = "high" if "high" in risk_levels else ("medium" if "medium" in risk_levels else "low")\n                assert overall_risk',
            content,
        )

        with open(file_path, "w") as f:
            f.write(content)

        print(f"✅ Fixed {file_path}")


if __name__ == "__main__":
    fix_pii_detector_tests()
    print("All PII detector tests have been fixed!")
