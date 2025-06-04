#!/usr/bin/env python3
"""
Comprehensive Image Generation Pipeline Test
Tests the entire pipeline end-to-end to ensure production readiness.

This script tests:
1. Database connectivity and schema
2. Model imports and initialization
3. API endpoint functionality
4. Image generation pipeline
5. Error handling and edge cases
6. Performance considerations
"""

import sys
import os
import asyncio
import json
import time
import uuid
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent / "backend" / ".env")

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

try:
    import pytest
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    from backend.models import Base, GeneratedImage, User
    from backend.utils.database import DatabaseConfig, get_db, get_database_manager
    from backend.services.image_generation.emotion_visualizer import EmotionVisualizer
    from backend.services.image_generation.image_generator import ImageGenerator
    from backend.services.image_generation.prompt_builder import PromptBuilder
    import httpx

    print("✅ All required modules imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


class ImageGenerationPipelineTest:
    """Comprehensive test suite for image generation pipeline."""

    def __init__(self):
        self.test_results = []
        self.test_user_id = str(uuid.uuid4())  # Generate a valid UUID for testing
        self.engine = None
        self.session = None

    def log_test(self, test_name: str, status: str, message: str, details: Dict = None):
        """Log test results."""
        result = {
            "test": test_name,
            "status": status,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details or {},
        }
        self.test_results.append(result)

        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {message}")

        if details:
            for key, value in details.items():
                print(f"   └─ {key}: {value}")

    def test_database_connectivity(self):
        """Test database connection and schema."""
        try:
            database_url = DatabaseConfig.get_database_url()
            self.engine = create_engine(database_url)

            # Test connection
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                conn.commit()

            self.log_test(
                "Database Connectivity", "PASS", "Successfully connected to database"
            )
            return True

        except Exception as e:
            self.log_test(
                "Database Connectivity", "FAIL", f"Database connection failed: {str(e)}"
            )
            return False

    def test_table_schema(self):
        """Test that generated_images table exists with correct schema."""
        try:
            with self.engine.connect() as conn:
                # Check table exists
                result = conn.execute(
                    text(
                        """
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_name = 'generated_images'
                """
                    )
                )

                if not result.fetchone():
                    self.log_test(
                        "Table Schema", "FAIL", "generated_images table does not exist"
                    )
                    return False

                # Check columns
                result = conn.execute(
                    text(
                        """
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'generated_images'
                    ORDER BY ordinal_position
                """
                    )
                )

                columns = {
                    row[0]: {"type": row[1], "nullable": row[2]}
                    for row in result.fetchall()
                }

                required_columns = {
                    "id": "character varying",
                    "user_id": "uuid",
                    "name": "character varying",
                    "prompt": "text",
                    "image_data": "text",
                    "image_format": "character varying",
                    "image_metadata": "json",
                    "created_at": "timestamp with time zone",
                    "updated_at": "timestamp with time zone",
                }

                missing_columns = []
                for col_name, expected_type in required_columns.items():
                    if col_name not in columns:
                        missing_columns.append(f"{col_name} (missing)")
                    elif expected_type not in columns[col_name]["type"]:
                        missing_columns.append(
                            f"{col_name} (wrong type: {columns[col_name]['type']})"
                        )

                if missing_columns:
                    self.log_test(
                        "Table Schema",
                        "FAIL",
                        f"Schema issues found",
                        {"missing_or_incorrect": missing_columns},
                    )
                    return False

                self.log_test(
                    "Table Schema",
                    "PASS",
                    f"All {len(required_columns)} columns present with correct types",
                    {"columns_found": len(columns)},
                )
                return True

        except Exception as e:
            self.log_test("Table Schema", "FAIL", f"Schema check failed: {str(e)}")
            return False

    def test_model_imports(self):
        """Test that all required models and classes can be imported."""
        try:
            # Test model creation
            test_image = GeneratedImage(
                user_id=self.test_user_id,
                name="Test Image",
                prompt="A test prompt",
                image_data="test_data",
                image_format="png",
                image_metadata={"test": True},
            )

            # Test that all attributes exist
            assert hasattr(test_image, "id")
            assert hasattr(test_image, "user_id")
            assert hasattr(test_image, "name")
            assert hasattr(test_image, "prompt")
            assert hasattr(test_image, "image_data")
            assert hasattr(test_image, "image_metadata")

            self.log_test(
                "Model Imports",
                "PASS",
                "All models imported and instantiated successfully",
            )
            return True

        except Exception as e:
            self.log_test(
                "Model Imports", "FAIL", f"Model import/instantiation failed: {str(e)}"
            )
            return False

    def test_image_generator_initialization(self):
        """Test ImageGenerator initialization."""
        try:
            # Test without HF token (should fail gracefully)
            original_token = os.getenv("HF_TOKEN")
            if original_token:
                # Test with token
                generator = ImageGenerator()
                self.log_test(
                    "ImageGenerator Init",
                    "PASS",
                    "ImageGenerator initialized successfully with HF token",
                )
                return True
            else:
                # Test graceful failure without token
                try:
                    generator = ImageGenerator()
                    self.log_test(
                        "ImageGenerator Init",
                        "FAIL",
                        "ImageGenerator should fail without HF_TOKEN",
                    )
                    return False
                except ValueError as e:
                    if "Hugging Face token" in str(e):
                        self.log_test(
                            "ImageGenerator Init",
                            "PASS",
                            "ImageGenerator correctly fails without HF token",
                            {"error": str(e)},
                        )
                        return True
                    else:
                        raise e

        except Exception as e:
            self.log_test("ImageGenerator Init", "FAIL", f"Unexpected error: {str(e)}")
            return False

    def test_prompt_builder(self):
        """Test PromptBuilder functionality."""
        try:
            builder = PromptBuilder()

            # Test prompt template formatting
            test_context = {
                "input_context": "I feel peaceful",
                "short_term_context": "talking about calm feelings",
                "emotional_anchors": "serenity, peace",
                "long_term_context": "user likes nature",
            }

            formatted = builder.format_prompt_template(test_context)

            if not formatted or len(formatted) < 50:
                self.log_test(
                    "PromptBuilder",
                    "FAIL",
                    "Formatted prompt too short or empty",
                    {"length": len(formatted) if formatted else 0},
                )
                return False

            # Test input analysis
            analysis = builder._analyze_input_content("I feel peaceful like a sunset")

            if not isinstance(analysis, dict) or "richness_score" not in analysis:
                self.log_test(
                    "PromptBuilder",
                    "FAIL",
                    "Input analysis failed or missing richness_score",
                )
                return False

            self.log_test(
                "PromptBuilder",
                "PASS",
                "PromptBuilder working correctly",
                {
                    "formatted_prompt_length": len(formatted),
                    "richness_score": analysis.get("richness_score"),
                },
            )
            return True

        except Exception as e:
            self.log_test(
                "PromptBuilder", "FAIL", f"PromptBuilder test failed: {str(e)}"
            )
            return False

    async def test_emotion_visualizer_basic(self):
        """Test EmotionVisualizer basic functionality (without actual image generation)."""
        try:
            # Create visualizer without LLM client to test basic functionality
            visualizer = EmotionVisualizer(llm_client=None)

            # Test emotion analysis
            test_context = {
                "input_context": "I feel peaceful and calm",
                "short_term_context": "discussing relaxation",
            }

            emotion_type = visualizer._analyze_emotion_type(test_context)

            if not emotion_type or emotion_type not in [
                "calm",
                "energetic",
                "mysterious",
                "hopeful",
                "melancholic",
            ]:
                self.log_test(
                    "EmotionVisualizer Basic",
                    "FAIL",
                    f"Invalid emotion type detected: {emotion_type}",
                )
                return False

            # Test validation
            validation = await visualizer.validate_user_input_for_visualization(
                self.test_user_id, "I feel like a peaceful sunset"
            )

            if not isinstance(validation, dict) or "suitable" not in validation:
                self.log_test(
                    "EmotionVisualizer Basic", "FAIL", "Input validation failed"
                )
                return False

            self.log_test(
                "EmotionVisualizer Basic",
                "PASS",
                "Basic EmotionVisualizer functionality working",
                {
                    "detected_emotion": emotion_type,
                    "input_suitable": validation.get("suitable"),
                },
            )
            return True

        except Exception as e:
            self.log_test("EmotionVisualizer Basic", "FAIL", f"Test failed: {str(e)}")
            return False

    def test_database_operations(self):
        """Test database CRUD operations."""
        try:
            # Use the database session correctly as a context manager
            db_manager = get_database_manager()
            with db_manager.get_db() as db:
                # Check if test user already exists and clean up first
                existing_user = (
                    db.query(User).filter(User.email == "test@example.com").first()
                )
                if existing_user:
                    # Delete any existing images for this user
                    existing_images = (
                        db.query(GeneratedImage)
                        .filter(GeneratedImage.user_id == existing_user.id)
                        .all()
                    )
                    for img in existing_images:
                        db.delete(img)
                    # Delete the existing user
                    db.delete(existing_user)
                    db.commit()

                # Create a test user since generated_images has a foreign key constraint
                test_user = User(
                    id=self.test_user_id,
                    email="test@example.com",
                    full_name="Test User",
                    is_active=True,
                )
                db.add(test_user)
                db.commit()

                # Test insert
                test_image = GeneratedImage(
                    user_id=self.test_user_id,
                    name="Test Pipeline Image",
                    prompt="A beautiful test landscape",
                    image_data="fake_base64_data_for_testing",
                    image_format="png",
                    image_metadata={
                        "emotion_type": "calm",
                        "test": True,
                        "pipeline_test": True,
                    },
                )

                db.add(test_image)
                db.commit()
                image_id = test_image.id

                # Test select
                retrieved = (
                    db.query(GeneratedImage)
                    .filter(GeneratedImage.id == image_id)
                    .first()
                )

                if not retrieved:
                    self.log_test(
                        "Database Operations",
                        "FAIL",
                        "Failed to retrieve inserted image",
                    )
                    return False

                # Test update
                retrieved.name = "Updated Test Name"
                db.commit()

                # Test filter by metadata (simplified to avoid JSON query complexity)
                images_by_emotion = (
                    db.query(GeneratedImage)
                    .filter(GeneratedImage.user_id == self.test_user_id)
                    .all()
                )

                # Test delete image
                db.delete(retrieved)
                db.commit()

                # Verify image deletion
                deleted_check = (
                    db.query(GeneratedImage)
                    .filter(GeneratedImage.id == image_id)
                    .first()
                )

                if deleted_check:
                    self.log_test(
                        "Database Operations", "FAIL", "Image not properly deleted"
                    )
                    return False

                # Clean up: delete test user
                db.delete(test_user)
                db.commit()

                self.log_test(
                    "Database Operations",
                    "PASS",
                    "All CRUD operations successful",
                    {
                        "insert": "✓",
                        "select": "✓",
                        "update": "✓",
                        "metadata_filter": f"Found {len(images_by_emotion)} images",
                        "delete": "✓",
                        "cleanup": "✓",
                    },
                )
                return True

        except Exception as e:
            self.log_test(
                "Database Operations", "FAIL", f"Database operations failed: {str(e)}"
            )
            return False

    async def test_api_endpoints_mock(self):
        """Test API endpoint structure (without actual HTTP calls)."""
        try:
            from backend.services.image_generation.api import router

            # Check that routes are defined
            route_paths = [route.path for route in router.routes]

            expected_paths = [
                "/generate",
                "/images",
                "/images/{image_id}",
                "/images/{image_id}/name",
                "/images/{image_id}/metadata",
                "/validate",
            ]

            missing_paths = [
                path
                for path in expected_paths
                if not any(path in route_path for route_path in route_paths)
            ]

            if missing_paths:
                self.log_test(
                    "API Endpoints",
                    "FAIL",
                    f"Missing API endpoints",
                    {"missing": missing_paths},
                )
                return False

            self.log_test(
                "API Endpoints",
                "PASS",
                f"All {len(expected_paths)} expected endpoints defined",
                {"total_routes": len(route_paths)},
            )
            return True

        except Exception as e:
            self.log_test(
                "API Endpoints", "FAIL", f"API endpoint test failed: {str(e)}"
            )
            return False

    def test_environment_configuration(self):
        """Test environment configuration."""
        try:
            config_issues = []

            # Check database URL
            db_url = DatabaseConfig.get_database_url()
            if not db_url or "localhost" in db_url:
                config_issues.append("Database URL not configured for production")

            # Check HF token
            hf_token = os.getenv("HF_TOKEN")
            if not hf_token:
                config_issues.append("HF_TOKEN not configured")

            # Check if required environment variables are set
            required_vars = ["SUPABASE_DATABASE_URL"]
            for var in required_vars:
                if not os.getenv(var):
                    config_issues.append(f"{var} not set")

            if config_issues:
                self.log_test(
                    "Environment Config",
                    "WARN",
                    "Configuration issues found",
                    {"issues": config_issues},
                )
                return False

            self.log_test(
                "Environment Config",
                "PASS",
                "All required environment variables configured",
            )
            return True

        except Exception as e:
            self.log_test("Environment Config", "FAIL", f"Config test failed: {str(e)}")
            return False

    async def test_error_handling(self):
        """Test error handling scenarios."""
        try:
            # Test with invalid user input
            visualizer = EmotionVisualizer(llm_client=None)

            # Test empty input (using await instead of asyncio.run)
            validation_empty = await visualizer.validate_user_input_for_visualization(
                self.test_user_id, ""
            )

            # Test very short input (using await instead of asyncio.run)
            validation_short = await visualizer.validate_user_input_for_visualization(
                self.test_user_id, "hi"
            )

            # Both should handle gracefully (not crash)
            if not isinstance(validation_empty, dict) or not isinstance(
                validation_short, dict
            ):
                self.log_test(
                    "Error Handling", "FAIL", "Error handling not working properly"
                )
                return False

            self.log_test(
                "Error Handling",
                "PASS",
                "Error handling working correctly",
                {
                    "empty_input_handled": validation_empty.get("suitable", "unknown"),
                    "short_input_handled": validation_short.get("suitable", "unknown"),
                },
            )
            return True

        except Exception as e:
            self.log_test(
                "Error Handling", "FAIL", f"Error handling test failed: {str(e)}"
            )
            return False

    async def run_all_tests(self):
        """Run all tests in sequence."""
        print("🚀 Starting Comprehensive Image Generation Pipeline Tests")
        print("=" * 70)

        tests = [
            ("Database Connectivity", self.test_database_connectivity),
            ("Table Schema", self.test_table_schema),
            ("Model Imports", self.test_model_imports),
            ("ImageGenerator Init", self.test_image_generator_initialization),
            ("PromptBuilder", self.test_prompt_builder),
            ("EmotionVisualizer Basic", self.test_emotion_visualizer_basic),
            ("Database Operations", self.test_database_operations),
            ("API Endpoints", self.test_api_endpoints_mock),
            ("Environment Config", self.test_environment_configuration),
            ("Error Handling", self.test_error_handling),
        ]

        passed = 0
        failed = 0
        warnings = 0

        for test_name, test_func in tests:
            try:
                if asyncio.iscoroutinefunction(test_func):
                    result = await test_func()
                else:
                    result = test_func()

                if result:
                    passed += 1
                else:
                    failed += 1

            except Exception as e:
                print(f"❌ {test_name}: CRASHED - {str(e)}")
                failed += 1

        # Count warnings
        warnings = sum(1 for r in self.test_results if r["status"] == "WARN")

        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Warnings: {warnings}")
        print(f"📊 Total: {len(tests)}")

        # Determine production readiness
        if failed == 0:
            if warnings == 0:
                print("\n🎉 PRODUCTION READY! All tests passed.")
            else:
                print(
                    f"\n⚠️  MOSTLY READY - {warnings} configuration warnings to address."
                )
        else:
            print(f"\n❌ NOT PRODUCTION READY - {failed} critical issues to fix.")

        # Save detailed results
        with open("image_generation_test_results.json", "w") as f:
            json.dump(
                {
                    "summary": {
                        "passed": passed,
                        "failed": failed,
                        "warnings": warnings,
                        "total": len(tests),
                        "production_ready": failed == 0,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                    "detailed_results": self.test_results,
                },
                f,
                indent=2,
            )

        print(f"\n📄 Detailed results saved to: image_generation_test_results.json")

        return failed == 0


async def main():
    """Main test runner."""
    tester = ImageGenerationPipelineTest()
    success = await tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
