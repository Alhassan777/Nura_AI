"""
VAPI Tools Registry - Centralized Tool Definitions for Mental Health Assistant

This module provides a comprehensive registry of all VAPI tools across six categories:
1. Crisis Intervention (Direct database access)
2. General Voice (Native VAPI tools + system management)
3. Scheduling (HTTP API calls to scheduling service)
4. Safety Checkup (Hybrid - bridges safety network with scheduling)
5. Image Generation (HTTP API calls to image service)
6. Memory Management (HTTP API calls to memory service)

Architecture:
- Single endpoint from VAPI dashboard: /api/voice/webhooks
- Main webhook handler routes to appropriate service based on tool name
- Avoids duplication by consolidating all tool definitions in one place
"""

from typing import Dict, Any, List, Optional
import os


class VAPIToolsRegistry:
    """Centralized registry for all VAPI tool definitions."""

    def __init__(self):
        """Initialize the tools registry."""
        self.webhook_url = os.getenv(
            "VAPI_WEBHOOK_URL", "https://your-domain.com/api/voice/webhooks"
        )

    def get_all_tools(self) -> List[Dict[str, Any]]:
        """
        Get all tool definitions for VAPI registration.

        Returns:
            List of all tool definitions across all categories
        """
        return [
            *self.get_crisis_tools(),
            *self.get_general_tools(),
            *self.get_scheduling_tools(),
            *self.get_safety_checkup_tools(),
            *self.get_image_generation_tools(),
            *self.get_memory_tools(),
        ]

    def get_tools_by_category(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get tools organized by category.

        Returns:
            Dictionary with tools grouped by category
        """
        return {
            "crisis": self.get_crisis_tools(),
            "general": self.get_general_tools(),
            "scheduling": self.get_scheduling_tools(),
            "safety_checkup": self.get_safety_checkup_tools(),
            "image_generation": self.get_image_generation_tools(),
            "memory": self.get_memory_tools(),
        }

    def get_tool_routing_map(self) -> Dict[str, str]:
        """
        Get mapping of tool names to their handler types.

        Returns:
            Dictionary mapping tool names to handler types
        """
        return {
            # Crisis tools (direct database access via voice service)
            "query_safety_network_contacts": "crisis_handler",
            "initiate_emergency_contact_outreach": "crisis_handler",
            "log_crisis_intervention": "crisis_handler",
            "send_crisis_sms": "vapi_native",
            "transfer_to_emergency_contact": "vapi_native",
            # General tools (voice service + native VAPI)
            "end_call": "vapi_native",
            "pause_conversation": "general_handler",
            "transfer_call": "vapi_native",
            "check_system_status": "general_handler",
            # Scheduling tools (API calls to scheduling service)
            "create_schedule_appointment": "scheduling_handler",
            "list_user_schedules": "scheduling_handler",
            "update_schedule_appointment": "scheduling_handler",
            "delete_schedule_appointment": "scheduling_handler",
            "check_user_availability": "scheduling_handler",
            # Safety checkup tools (hybrid - uses both safety and scheduling services)
            "schedule_safety_checkup": "safety_checkup_handler",
            "get_safety_checkup_schedules": "safety_checkup_handler",
            "cancel_safety_checkup": "safety_checkup_handler",
            # Image generation tools (API calls to image service)
            "process_drawing_reflection": "image_handler",
            "validate_visualization_input": "image_handler",
            "generate_visual_prompt": "image_handler",
            "create_emotional_image": "image_handler",
            "get_image_generation_status": "image_handler",
            # Memory tools (API calls to memory service)
            "search_user_memories": "memory_handler",
            "store_conversation_memory": "memory_handler",
            "get_memory_insights": "memory_handler",
        }

    # === CRISIS INTERVENTION TOOLS ===
    def get_crisis_tools(self) -> List[Dict[str, Any]]:
        """Crisis intervention tools for emergency mental health support."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "query_safety_network_contacts",
                    "description": "Query the user's safety network emergency contacts when crisis intervention is needed. Use this when the user is in distress and human support is required.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "The unique identifier for the user whose safety network should be queried",
                            },
                            "crisis_level": {
                                "type": "string",
                                "enum": ["moderate", "high", "critical"],
                                "description": "The assessed level of crisis - moderate (needs support), high (urgent intervention), critical (immediate danger)",
                            },
                            "crisis_description": {
                                "type": "string",
                                "description": "Brief description of the crisis situation and why human intervention is needed",
                            },
                            "user_current_state": {
                                "type": "string",
                                "description": "Description of the user's current emotional/mental state",
                            },
                        },
                        "required": [
                            "user_id",
                            "crisis_level",
                            "crisis_description",
                            "user_current_state",
                        ],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "initiate_emergency_contact_outreach",
                    "description": "Initiate contact outreach to an emergency contact during crisis intervention. Use this after querying safety network contacts to reach out to a specific contact.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "contact_id": {
                                "type": "string",
                                "description": "The ID of the emergency contact to reach out to (from query_safety_network_contacts result)",
                            },
                            "crisis_level": {
                                "type": "string",
                                "enum": ["moderate", "high", "critical"],
                                "description": "The assessed level of crisis - moderate (needs support), high (urgent intervention), critical (immediate danger)",
                            },
                            "message_context": {
                                "type": "string",
                                "description": "Context about the crisis situation to provide to the emergency contact",
                            },
                            "preferred_method": {
                                "type": "string",
                                "enum": ["phone", "sms", "email"],
                                "description": "Preferred method to contact the emergency contact",
                            },
                        },
                        "required": [
                            "contact_id",
                            "crisis_level",
                            "message_context",
                        ],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "log_crisis_intervention",
                    "description": "Log the crisis intervention attempt for record keeping and follow-up",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "The unique identifier for the user",
                            },
                            "contact_id": {
                                "type": "string",
                                "description": "The ID of the safety contact that was contacted",
                            },
                            "contact_method": {
                                "type": "string",
                                "enum": ["phone", "sms", "email"],
                                "description": "The method used to contact the emergency contact",
                            },
                            "contact_success": {
                                "type": "boolean",
                                "description": "Whether the contact attempt was successful",
                            },
                            "crisis_summary": {
                                "type": "string",
                                "description": "Summary of the crisis situation and intervention taken",
                            },
                            "next_steps": {
                                "type": "string",
                                "description": "Recommended next steps or follow-up actions",
                            },
                        },
                        "required": [
                            "user_id",
                            "contact_id",
                            "contact_method",
                            "contact_success",
                            "crisis_summary",
                        ],
                    },
                },
            },
            {
                "type": "sms",
                "function": {
                    "name": "send_crisis_sms",
                    "description": "Send an urgent SMS message to emergency contact using Vapi's native SMS functionality. Use this after querying safety contacts to get their phone number.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "to": {
                                "type": "string",
                                "description": "Emergency contact phone number to send SMS to (get from query_safety_network_contacts)",
                            },
                            "message": {
                                "type": "string",
                                "description": "Crisis intervention message to send via SMS. Include user name, crisis level, and request for immediate contact.",
                            },
                        },
                        "required": ["to", "message"],
                    },
                },
            },
            {
                "type": "transferCall",
                "function": {
                    "name": "transfer_to_emergency_contact",
                    "description": "Transfer the current call to an emergency contact using Vapi's native call transfer. Use this for immediate voice connection in crisis situations.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "destination": {
                                "type": "object",
                                "properties": {
                                    "type": {
                                        "type": "string",
                                        "enum": ["number"],
                                        "description": "Type of transfer destination - always 'number' for phone transfer",
                                    },
                                    "number": {
                                        "type": "string",
                                        "description": "Emergency contact phone number to transfer to (get from query_safety_network_contacts)",
                                    },
                                    "message": {
                                        "type": "string",
                                        "description": "Message to play before transfer, explaining the crisis situation briefly",
                                    },
                                },
                                "required": ["type", "number"],
                            }
                        },
                        "required": ["destination"],
                    },
                },
            },
        ]

    # === GENERAL VOICE TOOLS ===
    def get_general_tools(self) -> List[Dict[str, Any]]:
        """General voice conversation management tools."""
        return [
            {
                "type": "endCall",
                "function": {
                    "name": "end_call",
                    "description": "End the conversation naturally or for emergency referrals. Use with appropriate reason codes.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "reason": {
                                "type": "string",
                                "enum": [
                                    "natural_completion",
                                    "emergency_referral",
                                    "user_request",
                                    "technical_issue",
                                ],
                                "description": "Reason for ending the call",
                            },
                            "message": {
                                "type": "string",
                                "description": "Final message to user before ending call",
                            },
                        },
                        "required": ["reason"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "pause_conversation",
                    "description": "Temporarily pause the conversation to give the user time to process information or emotions",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "duration_seconds": {
                                "type": "integer",
                                "description": "Number of seconds to pause (5-30 seconds recommended)",
                                "minimum": 5,
                                "maximum": 30,
                            },
                            "pause_message": {
                                "type": "string",
                                "description": "Message to user about the pause (e.g., 'Take a moment to breathe')",
                            },
                        },
                        "required": ["duration_seconds"],
                    },
                },
            },
            {
                "type": "transferCall",
                "function": {
                    "name": "transfer_call",
                    "description": "Transfer call to professional support (therapist, peer support, technical support)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "destination": {
                                "type": "object",
                                "properties": {
                                    "type": {
                                        "type": "string",
                                        "enum": ["number"],
                                        "description": "Type of transfer destination",
                                    },
                                    "number": {
                                        "type": "string",
                                        "description": "Phone number to transfer to",
                                    },
                                    "message": {
                                        "type": "string",
                                        "description": "Message explaining the transfer to the user",
                                    },
                                },
                                "required": ["type", "number"],
                            },
                            "transfer_type": {
                                "type": "string",
                                "enum": [
                                    "professional_therapy",
                                    "peer_support",
                                    "technical_support",
                                ],
                                "description": "Type of support being transferred to",
                            },
                        },
                        "required": ["destination", "transfer_type"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "check_system_status",
                    "description": "Verify if recent operations (memory storage, scheduling, etc.) completed successfully to provide appropriate user feedback",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "operation_type": {
                                "type": "string",
                                "enum": [
                                    "memory_storage",
                                    "scheduling",
                                    "image_generation",
                                    "safety_contact",
                                ],
                                "description": "Type of operation to check status for",
                            },
                            "operation_id": {
                                "type": "string",
                                "description": "Optional ID of the specific operation to check",
                            },
                        },
                        "required": ["operation_type"],
                    },
                },
            },
        ]

    # === SCHEDULING TOOLS ===
    def get_scheduling_tools(self) -> List[Dict[str, Any]]:
        """Appointment and schedule management tools."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "create_schedule_appointment",
                    "description": "Create a new scheduled appointment or recurring checkup for the user",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "User-friendly name for the schedule (e.g., 'Weekly Anxiety Check-in')",
                            },
                            "schedule_type": {
                                "type": "string",
                                "enum": ["voice_checkup", "chat_checkup", "reminder"],
                                "description": "Type of scheduled interaction",
                            },
                            "cron_expression": {
                                "type": "string",
                                "description": "Cron expression for scheduling (e.g., '0 14 * * 1' for Monday 2 PM)",
                            },
                            "timezone": {
                                "type": "string",
                                "description": "User's timezone (default: UTC)",
                            },
                            "reminder_method": {
                                "type": "string",
                                "enum": ["call", "sms", "email"],
                                "description": "How to remind the user",
                            },
                            "context_summary": {
                                "type": "string",
                                "description": "Brief context about why this schedule was created",
                            },
                        },
                        "required": [
                            "name",
                            "schedule_type",
                            "cron_expression",
                            "reminder_method",
                        ],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "list_user_schedules",
                    "description": "List the user's existing scheduled appointments and checkups",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "active_only": {
                                "type": "boolean",
                                "description": "Whether to show only active schedules (default: true)",
                            },
                            "schedule_type": {
                                "type": "string",
                                "enum": [
                                    "voice_checkup",
                                    "chat_checkup",
                                    "reminder",
                                    "all",
                                ],
                                "description": "Filter by schedule type (default: all)",
                            },
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "update_schedule_appointment",
                    "description": "Update an existing scheduled appointment",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "schedule_id": {
                                "type": "string",
                                "description": "ID of the schedule to update",
                            },
                            "name": {
                                "type": "string",
                                "description": "Updated name for the schedule",
                            },
                            "cron_expression": {
                                "type": "string",
                                "description": "Updated cron expression",
                            },
                            "reminder_method": {
                                "type": "string",
                                "enum": ["call", "sms", "email"],
                                "description": "Updated reminder method",
                            },
                            "is_active": {
                                "type": "boolean",
                                "description": "Whether the schedule should remain active",
                            },
                        },
                        "required": ["schedule_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_schedule_appointment",
                    "description": "Cancel/delete a scheduled appointment",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "schedule_id": {
                                "type": "string",
                                "description": "ID of the schedule to delete",
                            },
                            "reason": {
                                "type": "string",
                                "description": "Optional reason for cancellation",
                            },
                        },
                        "required": ["schedule_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "check_user_availability",
                    "description": "Check user's availability and suggest optimal times for scheduling",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "preferred_time_of_day": {
                                "type": "string",
                                "enum": ["morning", "afternoon", "evening", "flexible"],
                                "description": "User's preferred time of day",
                            },
                            "preferred_days": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": [
                                        "monday",
                                        "tuesday",
                                        "wednesday",
                                        "thursday",
                                        "friday",
                                        "saturday",
                                        "sunday",
                                    ],
                                },
                                "description": "User's preferred days of the week",
                            },
                            "frequency": {
                                "type": "string",
                                "enum": ["daily", "weekly", "biweekly", "monthly"],
                                "description": "Desired frequency of checkups",
                            },
                        },
                        "required": ["preferred_time_of_day", "frequency"],
                    },
                },
            },
        ]

    # === SAFETY CHECKUP TOOLS ===
    def get_safety_checkup_tools(self) -> List[Dict[str, Any]]:
        """Safety network and checkup coordination tools."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "schedule_safety_checkup",
                    "description": "Schedule recurring safety checkups with safety network contacts",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "User ID for the checkup schedule",
                            },
                            "contact_id": {
                                "type": "string",
                                "description": "ID of the safety network contact to involve",
                            },
                            "checkup_type": {
                                "type": "string",
                                "enum": [
                                    "wellness_check",
                                    "medication_reminder",
                                    "therapy_support",
                                    "crisis_prevention",
                                ],
                                "description": "Type of safety checkup",
                            },
                            "frequency": {
                                "type": "string",
                                "enum": ["daily", "weekly", "biweekly", "monthly"],
                                "description": "How often to conduct checkups",
                            },
                            "preferred_time": {
                                "type": "string",
                                "description": "Preferred time for checkups (e.g., '14:00')",
                            },
                            "method": {
                                "type": "string",
                                "enum": ["voice_call", "sms", "email"],
                                "description": "Method for conducting checkups",
                            },
                        },
                        "required": ["user_id", "checkup_type", "frequency", "method"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_safety_checkup_schedules",
                    "description": "List existing safety checkup schedules for the user",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "User ID to get schedules for",
                            },
                            "active_only": {
                                "type": "boolean",
                                "description": "Whether to show only active schedules (default: true)",
                            },
                        },
                        "required": ["user_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "cancel_safety_checkup",
                    "description": "Cancel a safety checkup schedule",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "schedule_id": {
                                "type": "string",
                                "description": "ID of the safety checkup schedule to cancel",
                            },
                            "reason": {
                                "type": "string",
                                "description": "Reason for cancellation",
                            },
                        },
                        "required": ["schedule_id"],
                    },
                },
            },
        ]

    # === IMAGE GENERATION TOOLS ===
    def get_image_generation_tools(self) -> List[Dict[str, Any]]:
        """Therapeutic image generation and visual processing tools."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "process_drawing_reflection",
                    "description": "Process user's emotional or visual input for therapeutic drawing reflection",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "User ID for the reflection session",
                            },
                            "user_input": {
                                "type": "string",
                                "description": "User's description of their feelings or visual imagery",
                            },
                            "emotional_context": {
                                "type": "string",
                                "description": "Current emotional state or context",
                            },
                            "visual_elements": {
                                "type": "string",
                                "description": "Any specific visual elements mentioned by the user",
                            },
                        },
                        "required": ["user_id", "user_input", "emotional_context"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "validate_visualization_input",
                    "description": "Validate if user input is suitable for creating meaningful visual representation",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "User ID for validation",
                            },
                            "user_input": {
                                "type": "string",
                                "description": "User's input to validate for visualization",
                            },
                        },
                        "required": ["user_id", "user_input"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_visual_prompt",
                    "description": "Transform processed user input into a detailed visual prompt for image generation",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "User ID for the prompt generation",
                            },
                            "processed_input": {
                                "type": "string",
                                "description": "Processed and analyzed user input",
                            },
                            "emotion_type": {
                                "type": "string",
                                "description": "Primary emotion identified in the input",
                            },
                            "style_preference": {
                                "type": "string",
                                "enum": [
                                    "impressionistic",
                                    "abstract",
                                    "realistic",
                                    "minimalist",
                                    "watercolor",
                                ],
                                "description": "Visual style preference for the image",
                            },
                        },
                        "required": ["user_id", "processed_input", "emotion_type"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "create_emotional_image",
                    "description": "Generate therapeutic image using the created visual prompt",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "User ID for the image generation",
                            },
                            "visual_prompt": {
                                "type": "string",
                                "description": "Detailed visual prompt for image generation",
                            },
                            "emotion_type": {
                                "type": "string",
                                "description": "Primary emotion being represented",
                            },
                            "save_locally": {
                                "type": "boolean",
                                "description": "Whether to save the generated image locally",
                            },
                        },
                        "required": ["user_id", "visual_prompt", "emotion_type"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_image_generation_status",
                    "description": "Check the status and availability of the image generation service",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "User ID for status check",
                            },
                        },
                        "required": ["user_id"],
                    },
                },
            },
        ]

    # === MEMORY TOOLS ===
    def get_memory_tools(self) -> List[Dict[str, Any]]:
        """Conversation memory and context management tools."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_user_memories",
                    "description": "Search through user's conversation history for relevant context and insights",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "User ID to search memories for",
                            },
                            "query": {
                                "type": "string",
                                "description": "Search query or topic to find relevant memories",
                            },
                            "memory_type": {
                                "type": "string",
                                "enum": [
                                    "conversations",
                                    "insights",
                                    "goals",
                                    "progress",
                                    "all",
                                ],
                                "description": "Type of memories to search",
                            },
                            "time_range": {
                                "type": "string",
                                "enum": [
                                    "recent",
                                    "this_week",
                                    "this_month",
                                    "all_time",
                                ],
                                "description": "Time range for memory search",
                            },
                        },
                        "required": ["user_id", "query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "store_conversation_memory",
                    "description": "Store important elements from the current conversation for future reference",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "User ID for memory storage",
                            },
                            "memory_content": {
                                "type": "string",
                                "description": "Key conversation content to remember",
                            },
                            "memory_type": {
                                "type": "string",
                                "enum": [
                                    "insight",
                                    "goal",
                                    "progress",
                                    "concern",
                                    "achievement",
                                ],
                                "description": "Type of memory being stored",
                            },
                            "importance_level": {
                                "type": "string",
                                "enum": ["low", "medium", "high", "critical"],
                                "description": "Importance level of this memory",
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Tags for categorizing the memory",
                            },
                        },
                        "required": ["user_id", "memory_content", "memory_type"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_memory_insights",
                    "description": "Analyze conversation patterns and provide insights about user's progress and trends",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "User ID to analyze insights for",
                            },
                            "analysis_type": {
                                "type": "string",
                                "enum": [
                                    "emotional_trends",
                                    "progress_tracking",
                                    "conversation_patterns",
                                    "goal_achievement",
                                ],
                                "description": "Type of insight analysis to perform",
                            },
                            "time_period": {
                                "type": "string",
                                "enum": ["week", "month", "quarter", "all_time"],
                                "description": "Time period for analysis",
                            },
                        },
                        "required": ["user_id", "analysis_type"],
                    },
                },
            },
        ]

    def get_tool_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all tools for documentation purposes.

        Returns:
            Summary dictionary with tool counts and descriptions
        """
        tools_by_category = self.get_tools_by_category()

        return {
            "total_tools": len(self.get_all_tools()),
            "categories": {
                category: {
                    "count": len(tools),
                    "tools": [tool["function"]["name"] for tool in tools],
                    "description": self._get_category_description(category),
                }
                for category, tools in tools_by_category.items()
            },
            "webhook_endpoint": self.webhook_url,
            "routing_strategy": "Single endpoint with function name routing",
        }

    def _get_category_description(self, category: str) -> str:
        """Get description for a tool category."""
        descriptions = {
            "crisis": "Emergency mental health support with safety network integration",
            "general": "Voice conversation management and system control",
            "scheduling": "Appointment and recurring checkup management",
            "safety_checkup": "Proactive wellness monitoring with safety contacts",
            "image_generation": "Therapeutic visual content creation for emotional processing",
            "memory": "Conversation context and progress tracking",
        }
        return descriptions.get(category, "Unknown category")


# Global registry instance
vapi_tools_registry = VAPIToolsRegistry()
