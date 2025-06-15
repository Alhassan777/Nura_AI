"""
Action Plans Service - Core business logic for AI-generated action plans.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from models import ActionPlan, ActionStep, ActionSubtask
from ..assistant.extractors.action_plan_extractor import ActionPlanExtractor
from ..assistant.mental_health_assistant import MentalHealthAssistant

logger = logging.getLogger(__name__)


class ActionPlanService:
    """Service for managing AI-generated action plans."""

    def __init__(self):
        """Initialize the action plan service with AI capabilities."""
        self.mental_health_assistant = MentalHealthAssistant()

        # Initialize the action plan extractor with the assistant's model and config
        self.action_plan_extractor = ActionPlanExtractor(
            model=self.mental_health_assistant.model,
            generation_config=self.mental_health_assistant.conversational_config,
        )

    async def generate_action_plan_from_conversation(
        self, user_id: str, conversation_context: str, user_message: str, db: Session
    ) -> Optional[Dict[str, Any]]:
        """
        Generate an action plan using AI based on conversation context.

        Args:
            user_id: User identifier
            conversation_context: Previous conversation context
            user_message: Current user message
            db: Database session

        Returns:
            Generated action plan data or None if not applicable
        """
        try:
            # Use the action plan extractor to analyze the conversation
            extraction_result = await self.action_plan_extractor.extract_information(
                conversation_context=conversation_context,
                user_message=user_message,
                assistant_response="",  # We'll generate this after
                user_id=user_id,
            )

            if not extraction_result.get("should_suggest_action_plan"):
                return None

            extracted_plan = extraction_result.get("extracted_action_plan", {})
            if not extracted_plan:
                return None

            # Create the action plan in database
            action_plan = await self._create_action_plan_from_extraction(
                user_id=user_id, extraction_result=extraction_result, db=db
            )

            return {
                "action_plan": action_plan,
                "extraction_result": extraction_result,
                "should_suggest": True,
            }

        except Exception as e:
            logger.error(f"Error generating action plan for user {user_id}: {e}")
            return None

    async def _create_action_plan_from_extraction(
        self, user_id: str, extraction_result: Dict[str, Any], db: Session
    ) -> ActionPlan:
        """Create action plan in database from AI extraction result."""

        extracted_plan = extraction_result.get("extracted_action_plan", {})
        metadata = extraction_result.get("action_plan_metadata", {})

        # Create the main action plan
        action_plan = ActionPlan(
            user_id=user_id,
            title=metadata.get("name")
            or extracted_plan.get("plan_title", "AI Generated Plan"),
            description=metadata.get("description")
            or extracted_plan.get("plan_summary", ""),
            plan_type=metadata.get("action_plan_type", "hybrid"),
            priority="medium",
            status="active",
            generated_by_ai=True,
            generation_prompt=str(extraction_result),
            ai_metadata={
                "user_emotional_state": metadata.get("user_emotional_state"),
                "primary_goal": metadata.get("primary_goal"),
                "user_capacity": metadata.get("user_capacity"),
                "motivation_level": metadata.get("motivation_level"),
                "gentle_prompt": extraction_result.get("gentle_prompt"),
                "extraction_confidence": extraction_result.get("confidence", "medium"),
            },
        )

        db.add(action_plan)
        db.flush()  # Get the ID

        # Create steps from AI extraction
        await self._create_steps_from_extraction(action_plan.id, extracted_plan, db)

        # Calculate initial progress
        action_plan.progress_percentage = self._calculate_progress(action_plan)

        db.commit()
        db.refresh(action_plan)

        logger.info(
            f"Created AI-generated action plan {action_plan.id} for user {user_id}"
        )
        return action_plan

    async def _create_steps_from_extraction(
        self, action_plan_id: str, extracted_plan: Dict[str, Any], db: Session
    ):
        """Create action steps and subtasks from AI extraction."""

        # Handle immediate actions
        immediate_actions = extracted_plan.get("immediate_actions", [])
        step_order = 0

        for action in immediate_actions:
            if isinstance(action, dict):
                step = ActionStep(
                    action_plan_id=action_plan_id,
                    title=action.get("action", "Immediate Action"),
                    description=action.get("purpose", ""),
                    order_index=step_order,
                    time_needed=action.get("time_needed"),
                    difficulty=action.get("difficulty"),
                    purpose=action.get("purpose"),
                    success_criteria=action.get("success_looks_like"),
                    ai_metadata=action,
                )
                db.add(step)
                step_order += 1

        # Handle milestone goals
        milestone_goals = extracted_plan.get("milestone_goals", [])
        for milestone in milestone_goals:
            if isinstance(milestone, dict):
                step = ActionStep(
                    action_plan_id=action_plan_id,
                    title=milestone.get("goal", "Milestone Goal"),
                    description=f"Timeframe: {milestone.get('timeframe', 'TBD')}",
                    order_index=step_order,
                    purpose=milestone.get("goal"),
                    ai_metadata=milestone,
                )
                db.add(step)
                db.flush()  # Get step ID for subtasks

                # Create subtasks from action_steps
                action_steps = milestone.get("action_steps", [])
                subtask_order = 0
                for action_step in action_steps:
                    if isinstance(action_step, str):
                        subtask = ActionSubtask(
                            action_step_id=step.id,
                            title=action_step,
                            order_index=subtask_order,
                        )
                        db.add(subtask)
                        subtask_order += 1

                step_order += 1

        # Handle long-term vision as final step
        long_term_vision = extracted_plan.get("long_term_vision", {})
        if long_term_vision:
            step = ActionStep(
                action_plan_id=action_plan_id,
                title="Long-term Vision",
                description=long_term_vision.get("desired_outcome", ""),
                order_index=step_order,
                time_needed=long_term_vision.get("timeframe"),
                purpose="Achieve long-term transformation",
                success_criteria=long_term_vision.get("desired_outcome"),
                ai_metadata=long_term_vision,
            )
            db.add(step)

            # Add major milestones as subtasks
            major_milestones = long_term_vision.get("major_milestones", [])
            subtask_order = 0
            for milestone in major_milestones:
                if isinstance(milestone, str):
                    subtask = ActionSubtask(
                        action_step_id=step.id,
                        title=milestone,
                        order_index=subtask_order,
                    )
                    db.add(subtask)
                    subtask_order += 1

    def get_action_plans(self, user_id: str, db: Session) -> List[ActionPlan]:
        """Get all action plans for a user."""
        return (
            db.query(ActionPlan)
            .filter(and_(ActionPlan.user_id == user_id, ActionPlan.status != "deleted"))
            .order_by(ActionPlan.created_at.desc())
            .all()
        )

    def get_action_plan(
        self, plan_id: str, user_id: str, db: Session
    ) -> Optional[ActionPlan]:
        """Get a specific action plan by ID."""
        plan = (
            db.query(ActionPlan)
            .filter(
                and_(
                    ActionPlan.id == plan_id,
                    ActionPlan.user_id == user_id,
                    ActionPlan.status != "deleted",
                )
            )
            .first()
        )

        if plan:
            # Update progress before returning
            plan.progress_percentage = self._calculate_progress(plan)
            db.commit()

        return plan

    def create_action_plan(
        self,
        user_id: str,
        title: str,
        description: str,
        plan_type: str,
        priority: str = "medium",
        tags: List[str] = None,
        db: Session = None,
    ) -> ActionPlan:
        """Create a new manual action plan."""
        action_plan = ActionPlan(
            user_id=user_id,
            title=title,
            description=description,
            plan_type=plan_type,
            priority=priority,
            status="active",
            generated_by_ai=False,
            tags=tags or [],
            progress_percentage=0,
        )

        db.add(action_plan)
        db.commit()
        db.refresh(action_plan)

        logger.info(f"Created manual action plan {action_plan.id} for user {user_id}")
        return action_plan

    def update_action_plan(
        self, plan_id: str, user_id: str, updates: Dict[str, Any], db: Session
    ) -> Optional[ActionPlan]:
        """Update an existing action plan."""
        plan = self.get_action_plan(plan_id, user_id, db)
        if not plan:
            return None

        # Update allowed fields
        allowed_fields = [
            "title",
            "description",
            "priority",
            "status",
            "tags",
            "due_date",
        ]
        for field, value in updates.items():
            if field in allowed_fields and hasattr(plan, field):
                setattr(plan, field, value)

        plan.updated_at = datetime.utcnow()

        # Recalculate progress
        plan.progress_percentage = self._calculate_progress(plan)

        db.commit()
        db.refresh(plan)

        logger.info(f"Updated action plan {plan_id} for user {user_id}")
        return plan

    def delete_action_plan(self, plan_id: str, user_id: str, db: Session) -> bool:
        """Soft delete an action plan."""
        plan = self.get_action_plan(plan_id, user_id, db)
        if not plan:
            return False

        plan.status = "deleted"
        plan.updated_at = datetime.utcnow()

        db.commit()

        logger.info(f"Deleted action plan {plan_id} for user {user_id}")
        return True

    def update_step_status(
        self,
        plan_id: str,
        step_id: str,
        user_id: str,
        completed: bool,
        notes: str = None,
        db: Session = None,
    ) -> Optional[ActionPlan]:
        """Update the completion status of an action step."""
        plan = self.get_action_plan(plan_id, user_id, db)
        if not plan:
            return None

        step = (
            db.query(ActionStep)
            .filter(
                and_(ActionStep.id == step_id, ActionStep.action_plan_id == plan_id)
            )
            .first()
        )

        if not step:
            return None

        step.completed = completed
        step.completed_at = datetime.utcnow() if completed else None
        if notes:
            step.notes = notes
        step.updated_at = datetime.utcnow()

        # Update plan progress
        plan.progress_percentage = self._calculate_progress(plan)
        plan.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(plan)

        logger.info(f"Updated step {step_id} status to {completed} for plan {plan_id}")
        return plan

    def update_subtask_status(
        self,
        plan_id: str,
        step_id: str,
        subtask_id: str,
        user_id: str,
        completed: bool,
        db: Session = None,
    ) -> Optional[ActionPlan]:
        """Update the completion status of a subtask."""
        plan = self.get_action_plan(plan_id, user_id, db)
        if not plan:
            return None

        subtask = (
            db.query(ActionSubtask)
            .join(ActionStep)
            .filter(
                and_(
                    ActionSubtask.id == subtask_id,
                    ActionStep.id == step_id,
                    ActionStep.action_plan_id == plan_id,
                )
            )
            .first()
        )

        if not subtask:
            return None

        subtask.completed = completed
        subtask.completed_at = datetime.utcnow() if completed else None
        subtask.updated_at = datetime.utcnow()

        # Update plan progress
        plan.progress_percentage = self._calculate_progress(plan)
        plan.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(plan)

        logger.info(
            f"Updated subtask {subtask_id} status to {completed} for plan {plan_id}"
        )
        return plan

    def add_step(
        self,
        plan_id: str,
        user_id: str,
        title: str,
        description: str = None,
        db: Session = None,
    ) -> Optional[ActionPlan]:
        """Add a new step to an action plan."""
        plan = self.get_action_plan(plan_id, user_id, db)
        if not plan:
            return None

        # Get the next order index
        max_order = (
            db.query(ActionStep.order_index)
            .filter(ActionStep.action_plan_id == plan_id)
            .order_by(ActionStep.order_index.desc())
            .first()
        )

        next_order = (max_order[0] + 1) if max_order else 0

        step = ActionStep(
            action_plan_id=plan_id,
            title=title,
            description=description,
            order_index=next_order,
        )

        db.add(step)
        db.commit()
        db.refresh(plan)

        logger.info(f"Added step to plan {plan_id} for user {user_id}")
        return plan

    def add_subtask(
        self,
        plan_id: str,
        step_id: str,
        user_id: str,
        title: str,
        description: str = None,
        db: Session = None,
    ) -> Optional[ActionPlan]:
        """Add a new subtask to an action step."""
        plan = self.get_action_plan(plan_id, user_id, db)
        if not plan:
            return None

        step = (
            db.query(ActionStep)
            .filter(
                and_(ActionStep.id == step_id, ActionStep.action_plan_id == plan_id)
            )
            .first()
        )

        if not step:
            return None

        # Get the next order index
        max_order = (
            db.query(ActionSubtask.order_index)
            .filter(ActionSubtask.action_step_id == step_id)
            .order_by(ActionSubtask.order_index.desc())
            .first()
        )

        next_order = (max_order[0] + 1) if max_order else 0

        subtask = ActionSubtask(
            action_step_id=step_id,
            title=title,
            description=description,
            order_index=next_order,
        )

        db.add(subtask)
        db.commit()
        db.refresh(plan)

        logger.info(f"Added subtask to step {step_id} for plan {plan_id}")
        return plan

    def _calculate_progress(self, action_plan: ActionPlan) -> int:
        """Calculate progress percentage for an action plan."""
        if not action_plan.steps:
            return 0

        total_items = 0
        completed_items = 0

        for step in action_plan.steps:
            if step.subtasks:
                # If step has subtasks, count subtasks
                total_items += len(step.subtasks)
                completed_items += sum(
                    1 for subtask in step.subtasks if subtask.completed
                )
            else:
                # If no subtasks, count the step itself
                total_items += 1
                if step.completed:
                    completed_items += 1

        if total_items == 0:
            return 0

        return int((completed_items / total_items) * 100)
