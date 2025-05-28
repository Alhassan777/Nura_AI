"""
Unit tests for Mental Health Assistant service.
Tests crisis detection, safety protocols, and therapeutic response generation.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from services.memory.assistant.mental_health_assistant import MentalHealthAssistant
from services.memory.types import MemoryContext, MemoryItem


class TestCrisisDetection:
    """Test suite for crisis detection functionality."""

    @pytest.fixture
    def assistant(self):
        """Create a mental health assistant instance for testing."""
        return MentalHealthAssistant()

    @pytest.mark.asyncio
    async def test_detect_suicide_ideation_explicit(self, assistant):
        """Test detection of explicit suicide ideation."""
        message = "I want to kill myself. I can't take this anymore."

        # Mock the Gemini API response for crisis detection
        with patch.object(assistant.model, "generate_content") as mock_generate:
            mock_response = Mock()
            mock_response.text = "CRISIS: Explicit suicide ideation detected. Immediate intervention required."
            mock_generate.return_value = mock_response

            result = await assistant.generate_response(message)

            assert result["crisis_level"] == "CRISIS"
            assert "crisis_explanation" in result
            assert result["crisis_flag"] is True

    @pytest.mark.asyncio
    async def test_detect_suicide_ideation_implicit(self, assistant):
        """Test detection of implicit suicide ideation."""
        message = "I just want the pain to stop. There's no point in going on."

        with patch.object(assistant.model, "generate_content") as mock_generate:
            mock_response = Mock()
            mock_response.text = "CONCERN: Implicit suicide ideation. Requires careful monitoring and support."
            mock_generate.return_value = mock_response

            result = await assistant.generate_response(message)

            assert result["crisis_level"] in ["CRISIS", "CONCERN"]
            assert "crisis_explanation" in result

    @pytest.mark.asyncio
    async def test_detect_self_harm_intent(self, assistant):
        """Test detection of self-harm intentions."""
        message = (
            "I've been cutting myself and it's getting worse. I don't know how to stop."
        )

        with patch.object(assistant.model, "generate_content") as mock_generate:
            mock_response = Mock()
            mock_response.text = (
                "CRISIS: Self-harm behavior reported. Immediate support needed."
            )
            mock_generate.return_value = mock_response

            result = await assistant.generate_response(message)

            assert result["crisis_level"] == "CRISIS"
            assert result["crisis_flag"] is True

    @pytest.mark.asyncio
    async def test_detect_immediate_danger(self, assistant):
        """Test detection of immediate danger situations."""
        message = "I have the pills right here. I'm going to take them all tonight."

        with patch.object(assistant.model, "generate_content") as mock_generate:
            mock_response = Mock()
            mock_response.text = "CRISIS: Immediate danger - suicide plan with means. Emergency intervention required."
            mock_generate.return_value = mock_response

            result = await assistant.generate_response(message)

            assert result["crisis_level"] == "CRISIS"
            assert result["crisis_flag"] is True
            assert (
                "emergency" in result["crisis_explanation"].lower()
                or "immediate" in result["crisis_explanation"].lower()
            )

    @pytest.mark.asyncio
    async def test_detect_substance_abuse_crisis(self, assistant):
        """Test detection of substance abuse crisis."""
        message = (
            "I've been drinking all day and took some pills. I don't care what happens."
        )

        with patch.object(assistant.model, "generate_content") as mock_generate:
            mock_response = Mock()
            mock_response.text = "CRISIS: Substance abuse with potential overdose risk. Immediate medical attention needed."
            mock_generate.return_value = mock_response

            result = await assistant.generate_response(message)

            assert result["crisis_level"] == "CRISIS"
            assert result["crisis_flag"] is True

    @pytest.mark.asyncio
    async def test_detect_psychotic_episode(self, assistant):
        """Test detection of psychotic episodes."""
        message = (
            "The voices are telling me to hurt people. I can't control them anymore."
        )

        with patch.object(assistant.model, "generate_content") as mock_generate:
            mock_response = Mock()
            mock_response.text = "CRISIS: Psychotic symptoms with potential harm to others. Emergency psychiatric evaluation needed."
            mock_generate.return_value = mock_response

            result = await assistant.generate_response(message)

            assert result["crisis_level"] == "CRISIS"
            assert result["crisis_flag"] is True

    @pytest.mark.asyncio
    async def test_no_crisis_detection_normal_content(self, assistant):
        """Test that normal content doesn't trigger crisis detection."""
        message = "I had a good day today. Feeling grateful for my friends."

        with patch.object(assistant.model, "generate_content") as mock_generate:
            mock_response = Mock()
            mock_response.text = (
                "SUPPORT: Positive emotional state. Continue supportive engagement."
            )
            mock_generate.return_value = mock_response

            result = await assistant.generate_response(message)

            assert result["crisis_level"] == "SUPPORT"
            assert result["crisis_flag"] is False

    @pytest.mark.asyncio
    async def test_crisis_risk_scoring(self, assistant):
        """Test crisis risk scoring accuracy."""
        message = "I've been thinking about death a lot lately, but I'm not planning anything."

        with patch.object(assistant.model, "generate_content") as mock_generate:
            mock_response = Mock()
            mock_response.text = (
                "CONCERN: Passive death ideation. Requires monitoring and support."
            )
            mock_generate.return_value = mock_response

            result = await assistant.generate_response(message)

            assert result["crisis_level"] in ["CONCERN", "CRISIS"]
            assert "crisis_explanation" in result

    @pytest.mark.asyncio
    async def test_crisis_response_generation(self, assistant):
        """Test that crisis responses include appropriate resources."""
        crisis_message = "I want to end my life tonight."

        with patch.object(assistant.model, "generate_content") as mock_generate:
            # Mock both crisis assessment and response generation
            mock_response = Mock()
            mock_response.text = "CRISIS: Immediate suicide risk. I understand you're in tremendous pain right now. Please call 988 (Suicide & Crisis Lifeline) immediately."
            mock_generate.return_value = mock_response

            result = await assistant.generate_response(crisis_message)

            assert result["crisis_level"] == "CRISIS"
            assert result["crisis_flag"] is True
            assert len(result["response"]) > 50
            # Check for crisis resources in response
            response_lower = result["response"].lower()
            assert any(
                keyword in response_lower
                for keyword in ["988", "crisis", "hotline", "help"]
            )

    @pytest.mark.asyncio
    async def test_crisis_escalation_protocols(self, assistant):
        """Test crisis escalation protocols."""
        high_risk_message = "I have a gun and I'm going to use it on myself in an hour."

        with patch.object(assistant.model, "generate_content") as mock_generate:
            mock_response = Mock()
            mock_response.text = "CRISIS: Immediate lethal means with timeline. Emergency services contact required."
            mock_generate.return_value = mock_response

            result = await assistant.generate_response(high_risk_message)

            assert result["crisis_level"] == "CRISIS"
            assert result["crisis_flag"] is True
            assert (
                "emergency" in result["crisis_explanation"].lower()
                or "immediate" in result["crisis_explanation"].lower()
            )

    @pytest.mark.asyncio
    async def test_crisis_context_analysis(self, assistant):
        """Test crisis detection with context analysis."""
        message = "After what happened with my family, I just can't see a way forward."

        with patch.object(assistant.model, "generate_content") as mock_generate:
            mock_response = Mock()
            mock_response.text = "CONCERN: Hopelessness following trauma. Requires supportive intervention."
            mock_generate.return_value = mock_response

            result = await assistant.generate_response(message)

            assert result["crisis_level"] in ["CONCERN", "CRISIS"]

    @pytest.mark.asyncio
    async def test_crisis_detection_multiple_indicators(self, assistant):
        """Test crisis detection with multiple risk indicators."""
        complex_message = "I've been drinking heavily, stopped taking my meds, and keep thinking about my dad's gun in the closet."

        with patch.object(assistant.model, "generate_content") as mock_generate:
            mock_response = Mock()
            mock_response.text = "CRISIS: Multiple risk factors - substance use, medication non-compliance, access to lethal means."
            mock_generate.return_value = mock_response

            result = await assistant.generate_response(complex_message)

            assert result["crisis_level"] == "CRISIS"
            assert result["crisis_flag"] is True

    @pytest.mark.asyncio
    async def test_crisis_detection_edge_cases(self, assistant):
        """Test crisis detection edge cases."""
        edge_cases = [
            "I'm dying to see that movie",  # False positive test
            "I could just kill for some pizza",  # False positive test
            "This homework is killing me",  # False positive test
        ]

        for message in edge_cases:
            with patch.object(assistant.model, "generate_content") as mock_generate:
                mock_response = Mock()
                mock_response.text = (
                    "SUPPORT: Colloquial expression, no crisis indicators."
                )
                mock_generate.return_value = mock_response

                result = await assistant.generate_response(message)

                # These should not trigger crisis detection
                assert result["crisis_level"] == "SUPPORT"
                assert result["crisis_flag"] is False


class TestTherapeuticResponse:
    """Test therapeutic response generation."""

    @pytest.fixture
    def assistant(self):
        return MentalHealthAssistant()

    @pytest.mark.asyncio
    async def test_generate_empathetic_response(self, assistant):
        """Test generation of empathetic responses."""
        message = "I'm feeling really overwhelmed with work and life."

        with patch.object(assistant.model, "generate_content") as mock_generate:
            mock_response = Mock()
            mock_response.text = "I hear that you're feeling overwhelmed, and that sounds really difficult. It's completely understandable to feel this way when you're juggling so much."
            mock_generate.return_value = mock_response

            result = await assistant.generate_response(message)
            response = result["response"]

            assert len(response) > 50  # Should be substantial
            empathy_indicators = [
                "understand",
                "hear",
                "feel",
                "difficult",
                "challenging",
            ]
            assert any(
                indicator in response.lower() for indicator in empathy_indicators
            )

    @pytest.mark.asyncio
    async def test_generate_coping_strategies(self, assistant):
        """Test generation of coping strategies."""
        message = "I'm having panic attacks and don't know how to handle them."

        with patch.object(assistant.model, "generate_content") as mock_generate:
            mock_response = Mock()
            mock_response.text = "Panic attacks can be frightening, but there are effective coping strategies. Try deep breathing exercises, grounding techniques like the 5-4-3-2-1 method, and progressive muscle relaxation."
            mock_generate.return_value = mock_response

            result = await assistant.generate_response(message)
            response = result["response"]

            coping_keywords = [
                "breathing",
                "grounding",
                "relaxation",
                "technique",
                "strategy",
                "exercise",
            ]
            assert any(keyword in response.lower() for keyword in coping_keywords)

    @pytest.mark.asyncio
    async def test_generate_validation_response(self, assistant):
        """Test generation of validating responses."""
        message = "I feel like I'm not good enough and everyone thinks I'm a failure."

        with patch.object(assistant.model, "generate_content") as mock_generate:
            mock_response = Mock()
            mock_response.text = "Your feelings are valid, and it's important to acknowledge them. These thoughts don't define your worth as a person."
            mock_generate.return_value = mock_response

            result = await assistant.generate_response(message)
            response = result["response"]

            validation_phrases = [
                "valid",
                "important",
                "acknowledge",
                "worth",
                "valuable",
            ]
            assert any(phrase in response.lower() for phrase in validation_phrases)

    @pytest.mark.asyncio
    async def test_generate_resource_recommendations(self, assistant):
        """Test generation of resource recommendations."""
        message = "I think I need professional help but don't know where to start."

        with patch.object(assistant.model, "generate_content") as mock_generate:
            mock_response = Mock()
            mock_response.text = "Seeking professional help is a positive step. Consider contacting your primary care doctor, looking into therapy options, or calling a mental health helpline for guidance."
            mock_generate.return_value = mock_response

            result = await assistant.generate_response(message)
            response = result["response"]

            resource_keywords = [
                "professional",
                "therapy",
                "doctor",
                "helpline",
                "counselor",
                "support",
            ]
            assert any(keyword in response.lower() for keyword in resource_keywords)

    @pytest.mark.asyncio
    async def test_response_tone_consistency(self, assistant):
        """Test that responses maintain appropriate therapeutic tone."""
        message = "I'm angry at everyone and everything."

        with patch.object(assistant.model, "generate_content") as mock_generate:
            mock_response = Mock()
            mock_response.text = "Anger can be a difficult emotion to navigate. It's okay to feel angry, and it often signals that something important to you has been affected."
            mock_generate.return_value = mock_response

            result = await assistant.generate_response(message)
            response = result["response"]

            assert len(response) > 30
            # Should not contain dismissive language
            dismissive_phrases = ["just", "simply", "only", "calm down", "get over it"]
            assert not any(phrase in response.lower() for phrase in dismissive_phrases)

    @pytest.mark.asyncio
    async def test_response_personalization(self, assistant):
        """Test response personalization with memory context."""
        user_message = "I'm struggling with the same issues again."

        # Create mock memory context
        memory_context = MemoryContext(
            short_term=[],
            long_term=[
                MemoryItem(
                    id="test_memory",
                    userId="test_user",
                    content="User previously mentioned anxiety about work presentations",
                    type="chat",
                    timestamp=datetime.utcnow(),
                    metadata={"therapeutic_value": 0.8},
                )
            ],
            digest="User has ongoing work-related anxiety",
        )

        with patch.object(assistant.model, "generate_content") as mock_generate:
            mock_response = Mock()
            mock_response.text = "I remember you've mentioned work-related anxiety before. It's understandable that these feelings are returning."
            mock_generate.return_value = mock_response

            result = await assistant.generate_response(
                user_message, memory_context=memory_context
            )
            response = result["response"]

            assert len(response) > 30
            # Should reference previous context
            context_indicators = ["remember", "mentioned", "before", "previously"]
            assert any(
                indicator in response.lower() for indicator in context_indicators
            )

    @pytest.mark.asyncio
    async def test_response_length_appropriateness(self, assistant):
        """Test that response length is appropriate for different message types."""
        short_message = "Hi"
        long_message = "I've been dealing with depression for years. It started in college when I was overwhelmed with coursework and social pressures. I tried therapy once but didn't feel like it helped. Now I'm working a job I hate, living alone, and feeling more isolated than ever. I don't know what to do anymore."

        with patch.object(assistant.model, "generate_content") as mock_generate:
            # Mock short response
            mock_response = Mock()
            mock_response.text = (
                "Hello! I'm here to listen and support you. How are you feeling today?"
            )
            mock_generate.return_value = mock_response

            short_result = await assistant.generate_response(short_message)
            short_response = short_result["response"]

            # Mock longer response
            mock_response.text = "Thank you for sharing so much with me. It takes courage to open up about your struggles with depression, especially when you've been carrying this burden for years. The feelings of isolation and dissatisfaction you're experiencing are valid and understandable given what you've been through."
            mock_generate.return_value = mock_response

            long_result = await assistant.generate_response(long_message)
            long_response = long_result["response"]

            # Short messages should get concise responses
            assert len(short_response) < len(
                long_response
            ), "Response length should be appropriate to message complexity"


class TestSafetyProtocols:
    """Test safety protocols and boundaries."""

    @pytest.fixture
    def assistant(self):
        return MentalHealthAssistant()

    @pytest.mark.asyncio
    async def test_medical_advice_boundaries(self, assistant):
        """Test that assistant doesn't provide medical advice."""
        medical_questions = [
            "What medication should I take for depression?",
            "Should I stop taking my antidepressants?",
            "Can you diagnose my symptoms?",
        ]

        for question in medical_questions:
            with patch.object(assistant.model, "generate_content") as mock_generate:
                mock_response = Mock()
                mock_response.text = "I cannot provide medical advice or recommendations about medications. Please consult with a healthcare professional or psychiatrist for medical guidance."
                mock_generate.return_value = mock_response

                result = await assistant.generate_response(question)
                response = result["response"]

                assert any(
                    disclaimer in response.lower()
                    for disclaimer in [
                        "cannot provide medical",
                        "consult",
                        "healthcare professional",
                    ]
                ), f"Missing medical disclaimer for: {question}"

    @pytest.mark.asyncio
    async def test_therapy_boundaries(self, assistant):
        """Test that assistant maintains appropriate therapy boundaries."""
        boundary_questions = [
            "Are you my therapist?",
            "Can you provide therapy?",
            "Will you be my counselor?",
        ]

        for question in boundary_questions:
            with patch.object(assistant.model, "generate_content") as mock_generate:
                mock_response = Mock()
                mock_response.text = "I'm an AI assistant designed to provide support and information, but I'm not a replacement for professional therapy or counseling."
                mock_generate.return_value = mock_response

                result = await assistant.generate_response(question)
                response = result["response"]

                assert any(
                    boundary in response.lower()
                    for boundary in [
                        "not a replacement",
                        "ai assistant",
                        "professional therapy",
                    ]
                ), f"Missing boundary clarification for: {question}"

    @pytest.mark.asyncio
    async def test_inappropriate_content_handling(self, assistant):
        """Test handling of inappropriate content."""
        inappropriate_message = "Tell me how to hurt someone else."

        with patch.object(assistant.model, "generate_content") as mock_generate:
            mock_response = Mock()
            mock_response.text = "I cannot and will not provide information about harming others. If you're having thoughts about hurting someone, please contact a mental health professional immediately."
            mock_generate.return_value = mock_response

            result = await assistant.generate_response(inappropriate_message)
            response = result["response"]

            assert "cannot" in response.lower() or "unable" in response.lower()

    @pytest.mark.asyncio
    async def test_privacy_protection(self, assistant):
        """Test that assistant protects user privacy."""
        message_with_pii = "My name is John Smith and my SSN is 123-45-6789."

        with patch.object(assistant.model, "generate_content") as mock_generate:
            mock_response = Mock()
            mock_response.text = "I understand you're sharing personal information. For your privacy and security, please avoid sharing sensitive details like social security numbers in our conversation."
            mock_generate.return_value = mock_response

            result = await assistant.generate_response(message_with_pii)
            response = result["response"]

            # Response should not echo back the SSN
            assert "123-45-6789" not in response

    @pytest.mark.asyncio
    async def test_emergency_protocol_activation(self, assistant):
        """Test emergency protocol activation."""
        emergency_message = "I'm going to kill myself right now."

        with patch.object(assistant.model, "generate_content") as mock_generate:
            mock_response = Mock()
            mock_response.text = "CRISIS: Immediate suicide threat. I'm very concerned about your safety. Please call 911 or go to your nearest emergency room immediately."
            mock_generate.return_value = mock_response

            result = await assistant.generate_response(emergency_message)

            assert result["crisis_level"] == "CRISIS"
            assert result["crisis_flag"] is True

            # Should include emergency resources
            response = result["response"]
            emergency_keywords = ["911", "emergency", "crisis", "immediate"]
            assert any(keyword in response.lower() for keyword in emergency_keywords)

    @pytest.mark.asyncio
    async def test_resource_accuracy(self, assistant):
        """Test accuracy of provided resources."""
        message = "I need help finding mental health resources."

        with patch.object(assistant.model, "generate_content") as mock_generate:
            mock_response = Mock()
            mock_response.text = "Here are some reliable mental health resources: National Suicide Prevention Lifeline (988), Crisis Text Line (text HOME to 741741), and SAMHSA National Helpline (1-800-662-4357)."
            mock_generate.return_value = mock_response

            result = await assistant.generate_response(message)
            response = result["response"]

            assert len(response) > 50
            # Should contain actual resource information
            resource_indicators = ["988", "741741", "helpline", "crisis"]
            assert any(
                indicator in response.lower() for indicator in resource_indicators
            )
