import os
import re
import logging
from typing import List, Dict, Any, Optional, Set
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine
from transformers import pipeline
from ..types import MemoryItem

# Set up logging
logger = logging.getLogger(__name__)


class PIIDetector:
    def __init__(self):
        # Initialize Presidio analyzer
        self.analyzer = AnalyzerEngine()

        # Initialize Presidio anonymizer
        self.anonymizer = AnonymizerEngine()

        # Initialize Hugging Face NER model for additional PII detection
        self.ner_pipeline = pipeline(
            "token-classification",
            model="dslim/bert-base-NER",
            aggregation_strategy="simple",
        )

        # Define PII with privacy risk levels for dual storage strategy
        self.pii_definitions = {
            # HIGH RISK - Always anonymize in long-term storage
            "PERSON": {
                "patterns": None,  # Handled by Presidio + Hugging Face
                "risk_level": "high",
                "category": "personal_identity",
                "description": "Person names",
            },
            "EMAIL_ADDRESS": {
                "patterns": None,
                "risk_level": "high",
                "category": "contact_information",
                "description": "Email addresses",
            },
            "PHONE_NUMBER": {
                "patterns": None,
                "risk_level": "high",
                "category": "contact_information",
                "description": "Phone numbers",
            },
            "HEALTHCARE_PROVIDER": {
                "patterns": [
                    r"\b(?i)(dr\.|doctor|therapist|psychiatrist|psychologist|counselor|social worker|msw|lcsw|lmft|phd|md|psy\.d\.)\s+[A-Z][a-z]+\b"
                ],
                "risk_level": "high",
                "category": "medical_information",
                "description": "Healthcare provider names",
            },
            "FAMILY_MEMBER": {
                "patterns": [
                    r"\b(?i)(my|his|her)\s+(mom|mother|dad|father|parent|son|daughter|child|kid|sister|brother|sibling|wife|husband|spouse|partner|boyfriend|girlfriend)\s+([A-Z][a-z]+)\b"
                ],
                "risk_level": "high",
                "category": "personal_identity",
                "description": "Family member names",
            },
            "WORKPLACE_INFO": {
                "patterns": [
                    r"\b(?i)(works? at|employed by|company|corporation|inc\.|llc)\s+[A-Z][a-zA-Z\s&]+\b"
                ],
                "risk_level": "high",
                "category": "location_information",
                "description": "Workplace information",
            },
            "CREDIT_CARD": {
                "patterns": [r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b"],
                "risk_level": "high",
                "category": "financial_information",
                "description": "Credit card numbers",
            },
            "INSURANCE_INFO": {
                "patterns": [
                    r"\b(?i)(medicaid|medicare|blue cross|aetna|cigna|humana|united healthcare|kaiser|insurance|policy number|member id)\b",
                    r"\b[A-Z]{2,4}\d{6,12}\b",
                ],
                "risk_level": "high",
                "category": "financial_information",
                "description": "Insurance information",
            },
            # MEDIUM RISK - User chooses for long-term storage
            "MEDICATION": {
                "patterns": [
                    r"\b(?i)(zoloft|prozac|lexapro|wellbutrin|xanax|ativan|klonopin|adderall|ritalin|abilify|seroquel|lithium|lamictal|depakote|risperdal|geodon|zyprexa|clozaril|haldol|thorazine|effexor|cymbalta|paxil|celexa|buspar|trazodone|mirtazapine|venlafaxine|sertraline|fluoxetine|escitalopram|bupropion|alprazolam|lorazepam|clonazepam)\b"
                ],
                "risk_level": "medium",
                "category": "medical_information",
                "description": "Medications",
            },
            "MENTAL_HEALTH_DIAGNOSIS": {
                "patterns": [
                    r"\b(?i)(depression|anxiety|ptsd|ocd|adhd|bipolar|schizophrenia|borderline personality|bpd|autism|asperger|anorexia|bulimia|eating disorder|panic disorder|social anxiety|generalized anxiety|major depressive|manic episode|psychosis|mania|hypomania)\b"
                ],
                "risk_level": "medium",
                "category": "medical_information",
                "description": "Mental health diagnoses",
            },
            "MEDICAL_FACILITY": {
                "patterns": [
                    r"\b(?i)(hospital|clinic|medical center|health center|psychiatric|mental health center|rehab|rehabilitation|treatment center|wellness center)\s+[A-Z][a-zA-Z\s]+\b"
                ],
                "risk_level": "medium",
                "category": "location_information",
                "description": "Medical facilities",
            },
            # LOW RISK - Generally safe to keep
            "THERAPY_TYPE": {
                "patterns": [
                    r"\b(?i)(cbt|cognitive behavioral therapy|dbt|dialectical behavior therapy|emdr|psychotherapy|group therapy|family therapy|couples therapy|exposure therapy|talk therapy|psychoanalysis|gestalt therapy|somatic therapy)\b"
                ],
                "risk_level": "low",
                "category": "therapy_information",
                "description": "Therapy types",
            },
            "CRISIS_HOTLINE": {
                "patterns": [
                    r"\b988\b",
                    r"\b1-800-273-8255\b",
                    r"\b(?i)(crisis|suicide|help)\s+(?:line|hotline)?\s*:?\s*[\d\-\(\)\s]{10,}\b",
                ],
                "risk_level": "low",
                "category": "therapy_information",
                "description": "Crisis hotlines",
            },
            "DATE_TIME": {
                "patterns": None,
                "risk_level": "low",
                "category": "dates_and_times",
                "description": "Dates and times",
            },
        }

        # Build pattern recognizers
        self._setup_pattern_recognizers()

    def _setup_pattern_recognizers(self):
        """Set up custom pattern recognizers for Presidio."""
        for entity_type, definition in self.pii_definitions.items():
            if definition["patterns"]:
                patterns = []
                for pattern_str in definition["patterns"]:
                    patterns.append(
                        Pattern(
                            name=f"{entity_type}_pattern", regex=pattern_str, score=0.8
                        )
                    )

                recognizer = PatternRecognizer(
                    supported_entity=entity_type, patterns=patterns
                )
                self.analyzer.registry.add_recognizer(recognizer)

    async def detect_pii(self, memory: MemoryItem) -> Dict[str, Any]:
        """Detect PII in memory content and return detailed results."""
        # Get Presidio results
        presidio_results = self.analyzer.analyze(text=memory.content, language="en")

        # Get Hugging Face NER results for additional name detection
        ner_results = self.ner_pipeline(memory.content)

        # Combine and deduplicate results
        detected_items = []

        # Add Presidio results
        for result in presidio_results:
            entity_type = result.entity_type
            detected_text = memory.content[result.start : result.end]

            # Get definition info
            definition = self.pii_definitions.get(
                entity_type,
                {
                    "risk_level": "medium",
                    "category": "other",
                    "description": entity_type.lower().replace("_", " "),
                },
            )

            detected_items.append(
                {
                    "id": f"{entity_type}_{result.start}_{result.end}",
                    "text": detected_text,
                    "type": entity_type,
                    "start": result.start,
                    "end": result.end,
                    "confidence": result.score,
                    "risk_level": definition["risk_level"],
                    "category": definition["category"],
                    "description": definition["description"],
                }
            )

        # Add Hugging Face results (mainly for person names)
        for result in ner_results:
            if result["entity_group"] == "PER":  # Person names
                detected_items.append(
                    {
                        "id": f"PERSON_{result['start']}_{result['end']}",
                        "text": result["word"],
                        "type": "PERSON",
                        "start": result["start"],
                        "end": result["end"],
                        "confidence": result["score"],
                        "risk_level": "high",
                        "category": "personal_identity",
                        "description": "Person names",
                    }
                )

        return {
            "has_pii": len(detected_items) > 0,
            "detected_items": detected_items,
            "needs_consent": any(
                item["risk_level"] in ["high", "medium"] for item in detected_items
            ),
        }

    def get_granular_consent_options(
        self, pii_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get granular consent options for each individual detected item."""
        if not pii_results.get("has_pii", False):
            return {"needs_consent": False}

        detected_items = pii_results["detected_items"]

        # Group items that need consent (high/medium risk)
        consent_items = [
            item for item in detected_items if item["risk_level"] in ["high", "medium"]
        ]

        if not consent_items:
            return {"needs_consent": False}

        # Create summary
        item_texts = [f'"{item["text"]}"' for item in consent_items[:3]]
        if len(consent_items) > 3:
            item_texts.append(f"and {len(consent_items) - 3} more items")

        consent_options = {
            "needs_consent": True,
            "storage_strategy": "dual",
            "message": f"I detected sensitive information: {', '.join(item_texts)}. I can handle each item differently for short-term chat vs long-term memory.",
            "consent_items": [],
        }

        # Add each item with individual consent options
        for item in consent_items:
            consent_item = {
                "id": item["id"],
                "text": item["text"],
                "type": item["type"],
                "description": item["description"],
                "risk_level": item["risk_level"],
                "category": item["category"],
                "confidence": item["confidence"],
                "recommendations": self._get_item_recommendations(item),
                "user_choice_required": item["risk_level"] == "medium",
            }
            consent_options["consent_items"].append(consent_item)

        return consent_options

    def _get_item_recommendations(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Get storage recommendations for a specific item."""
        risk_level = item["risk_level"]

        recommendations = {
            "short_term": {
                "action": "keep_original",
                "reason": "Enables personalized responses in this chat session",
            }
        }

        if risk_level == "high":
            recommendations["long_term"] = {
                "action": "anonymize",
                "reason": "High privacy risk - protects your identity in permanent storage",
            }
        elif risk_level == "medium":
            recommendations["long_term"] = {
                "action": "user_choice",
                "reason": "Medical context may help treatment continuity - your choice",
            }
        else:  # low risk
            recommendations["long_term"] = {
                "action": "keep_original",
                "reason": "Safe therapeutic context that helps ongoing care",
            }

        return recommendations

    async def apply_granular_consent(
        self,
        content: str,
        storage_type: str,  # "short_term" or "long_term"
        user_consent: Dict[str, Any],  # item_id -> "keep" or "anonymize"
        pii_results: Dict[str, Any],
    ) -> str:
        """Apply user consent decisions for each individual PII item."""

        if storage_type == "short_term":
            # For short-term, generally keep original unless user explicitly wants anonymization
            items_to_anonymize = [
                item
                for item in pii_results["detected_items"]
                if user_consent.get(item["id"], "keep") == "anonymize"
            ]
        else:  # long_term
            # For long-term, apply user choices with defaults based on risk level
            items_to_anonymize = []
            for item in pii_results["detected_items"]:
                user_choice = user_consent.get(item["id"])

                if user_choice == "anonymize":
                    items_to_anonymize.append(item)
                elif user_choice == "keep":
                    continue  # Keep original
                else:  # No explicit choice, use defaults
                    if item["risk_level"] == "high":
                        items_to_anonymize.append(item)
                    # Medium and low risk keep original if no choice specified

        # Apply anonymization
        if not items_to_anonymize:
            return content

        # Sort by position (reverse order to maintain positions during replacement)
        items_to_anonymize.sort(key=lambda x: x["start"], reverse=True)

        result_content = content
        for item in items_to_anonymize:
            # Create placeholder based on type
            placeholder = f"<{item['type']}>"
            # Replace the specific text
            result_content = (
                result_content[: item["start"]]
                + placeholder
                + result_content[item["end"] :]
            )

        return result_content
