"""
PawPal+ System - Core Logic Layer

This module contains the main classes for the PawPal+ pet care scheduling system.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum
from datetime import datetime, timedelta


class TaskType(Enum):
    """Enum for different types of pet care tasks."""
    WALK = "walk"
    FEED = "feed"
    MEDICATION = "medication"
    GROOMING = "grooming"
    ENRICHMENT = "enrichment"
    PLAYTIME = "playtime"
    TRAINING = "training"


class Frequency(Enum):
    """Enum for task recurrence frequency."""
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


@dataclass
class Owner:
    """
    Represents a pet owner with time constraints and preferences.

    Attributes:
        name: Owner's name
        available_time_minutes: Total daily time available for pet care
        preferences: Dictionary of owner preferences (e.g., preferred task times)
        pets: List of pets owned by this owner
    """
    name: str
    available_time_minutes: int
    preferences: Dict[str, any] = field(default_factory=dict)
    pets: List['Pet'] = field(default_factory=list, compare=False, repr=False)

    def get_available_time(self) -> int:
        """Returns the available time in minutes."""
        return self.available_time_minutes

    def set_preferences(self, preferences: Dict[str, any]) -> None:
        """Updates owner preferences."""
        self.preferences.update(preferences)

    def add_pet(self, pet: 'Pet') -> None:
        """Adds a pet to this owner's pet list."""
        if pet not in self.pets:
            self.pets.append(pet)
            pet.owner = self


@dataclass
class Pet:
    """
    Represents a pet with basic information and care needs.

    Attributes:
        name: Pet's name
        species: Type of pet (dog, cat, etc.)
        age: Pet's age in years
        special_needs: List of special care requirements
        owner: Reference to the pet's owner
    """
    name: str
    species: str
    age: int
    special_needs: List[str] = field(default_factory=list)
    owner: Optional[Owner] = field(default=None, compare=False, repr=False)

    def get_info(self) -> Dict[str, any]:
        """Returns a dictionary of pet information."""
        return {
            "name": self.name,
            "species": self.species,
            "age": self.age,
            "special_needs": self.special_needs,
            "owner": self.owner.name if self.owner else None
        }

    def add_special_need(self, need: str) -> None:
        """Adds a special care need for the pet."""
        if need and need not in self.special_needs:
            self.special_needs.append(need)


@dataclass
class Task:
    """
    Represents a pet care task with duration and priority.

    Attributes:
        name: Task name/description
        duration_minutes: How long the task takes
        priority: Priority level (1=lowest, 5=highest)
        task_type: Type of task (from TaskType enum)
        pet: Pet
        completed: Whether the task has been completed
        scheduled_time: Optional specific time for the task (HH:MM format)
        frequency: How often the task recurs (default: once)
        due_date: Optional date for the task
    """
    name: str
    duration_minutes: int
    priority: int
    task_type: TaskType
    pet: Pet
    completed: bool = False
    scheduled_time: Optional[str] = None
    frequency: Frequency = Frequency.ONCE
    due_date: Optional[datetime] = None

    def __post_init__(self):
        """Validates task attributes after initialization."""
        if not 1 <= self.priority <= 5:
            raise ValueError("Priority must be between 1 and 5")
        if self.duration_minutes <= 0:
            raise ValueError("Duration must be positive")
        if self.scheduled_time:
            # Validate time format (HH:MM)
            try:
                hours, minutes = map(int, self.scheduled_time.split(':'))
                if not (0 <= hours <= 23 and 0 <= minutes <= 59):
                    raise ValueError
            except (ValueError, AttributeError):
                raise ValueError("Scheduled time must be in HH:MM format (e.g., '09:30')")

    def mark_complete(self) -> None:
        """Marks the task as completed."""
        self.completed = True

    def get_priority(self) -> int:
        """Returns the task priority."""
        return self.priority

    def get_duration(self) -> int:
        """Returns the task duration in minutes."""
        return self.duration_minutes

    def get_end_time(self) -> Optional[str]:
        """
        Calculates and returns the end time of the task if scheduled_time is set.

        Returns:
            End time in HH:MM format, or None if no scheduled_time
        """
        if not self.scheduled_time:
            return None

        start = datetime.strptime(self.scheduled_time, '%H:%M')
        end = start + timedelta(minutes=self.duration_minutes)
        return end.strftime('%H:%M')

    def create_recurring_instance(self) -> 'Task':
        """
        Creates a new instance of this task for the next occurrence.

        Returns:
            A new Task object with updated due_date based on frequency
        """
        if self.frequency == Frequency.ONCE:
            raise ValueError("Cannot create recurring instance of a one-time task")

        # Calculate next due date
        if self.due_date:
            if self.frequency == Frequency.DAILY:
                next_date = self.due_date + timedelta(days=1)
            elif self.frequency == Frequency.WEEKLY:
                next_date = self.due_date + timedelta(weeks=1)
            elif self.frequency == Frequency.MONTHLY:
                next_date = self.due_date + timedelta(days=30)
            else:
                next_date = self.due_date
        else:
            # If no due date set, use tomorrow for daily tasks
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            if self.frequency == Frequency.DAILY:
                next_date = today + timedelta(days=1)
            elif self.frequency == Frequency.WEEKLY:
                next_date = today + timedelta(weeks=1)
            elif self.frequency == Frequency.MONTHLY:
                next_date = today + timedelta(days=30)
            else:
                next_date = today

        # Create new task with same properties but updated date
        return Task(
            name=self.name,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            task_type=self.task_type,
            pet=self.pet,
            completed=False,
            scheduled_time=self.scheduled_time,
            frequency=self.frequency,
            due_date=next_date
        )


class Scheduler:
    """
    Main scheduling engine that generates daily care plans.

    The Scheduler takes owner constraints, pet needs, and task priorities
    to create an optimized daily schedule.

    Attributes:
        owner: The pet owner
        pets: List of pets to schedule care for
        tasks: List of all care tasks
        daily_plan: The generated schedule
    """

    def __init__(self, owner: Owner):
        """Initialize the scheduler with an owner."""
        self.owner = owner
        self.pets: List[Pet] = owner.pets
        self.tasks: List[Task] = []
        self.daily_plan: List[Task] = []

    def add_pet(self, pet: Pet) -> None:
        """Adds a pet to the scheduler."""
        if pet not in self.pets:
            self.pets.append(pet)
            self.owner.add_pet(pet)

    def add_task(self, task: Task) -> None:
        """Adds a task to the scheduler."""
        if task not in self.tasks:
            self.tasks.append(task)

    def mark_task_complete(self, task: Task) -> Optional[Task]:
        """
        Marks a task as complete and creates a new instance if it's recurring.

        Args:
            task: The task to mark complete

        Returns:
            The new recurring task instance if applicable, None otherwise
        """
        task.mark_complete()

        # If this is a recurring task, create the next instance
        if task.frequency != Frequency.ONCE:
            new_task = task.create_recurring_instance()
            self.add_task(new_task)
            return new_task

        return None

    def remove_task(self, task: Task) -> None:
        """Removes a task from the scheduler."""
        if task in self.tasks:
            self.tasks.remove(task)

    def get_tasks_by_pet(self, pet: Pet) -> List[Task]:
        """Returns all tasks for a specific pet."""
        return [task for task in self.tasks if task.pet == pet]

    def get_tasks_by_type(self, task_type: TaskType) -> List[Task]:
        """Returns all tasks of a specific type."""
        return [task for task in self.tasks if task.task_type == task_type]

    def get_incomplete_tasks(self) -> List[Task]:
        """Returns all incomplete tasks."""
        return [task for task in self.tasks if not task.completed]

    def get_total_scheduled_time(self) -> int:
        """Returns total time of all scheduled tasks in minutes."""
        return sum(task.duration_minutes for task in self.daily_plan)

    def generate_daily_plan(self) -> List[Task]:
        """
        Generates an optimized daily schedule based on constraints.

        Returns:
            List of tasks in scheduled order
        """
        # Reset the daily plan
        self.daily_plan = []

        # Get incomplete tasks and prioritize them
        prioritized_tasks = self.prioritize_tasks()

        # Track available time
        available_time = self.owner.get_available_time()
        total_scheduled = 0

        # Greedily add tasks until we run out of time
        for task in prioritized_tasks:
            if total_scheduled + task.duration_minutes <= available_time:
                self.daily_plan.append(task)
                total_scheduled += task.duration_minutes

        return self.daily_plan

    def prioritize_tasks(self) -> List[Task]:
        """
        Sorts tasks by priority and other criteria.

        Returns:
            List of tasks in priority order
        """
        # Get only incomplete tasks
        incomplete_tasks = self.get_incomplete_tasks()

        # Sort by priority (highest first), then by duration (shorter first for ties)
        # This maximizes high-priority tasks while fitting more tasks when priorities are equal
        sorted_tasks = sorted(
            incomplete_tasks,
            key=lambda task: (-task.priority, task.duration_minutes)
        )

        return sorted_tasks

    def explain_reasoning(self) -> str:
        """
        Provides explanation for scheduling decisions.

        Returns:
            String explaining why tasks were scheduled in this order
        """
        if not self.daily_plan:
            return "No tasks have been scheduled yet. Generate a daily plan first."

        explanation_parts = []

        # Overall summary
        total_time = self.get_total_scheduled_time()
        available_time = self.owner.get_available_time()
        num_tasks = len(self.daily_plan)
        num_incomplete = len(self.get_incomplete_tasks())

        explanation_parts.append(
            f"\U0001f4cb **Schedule Summary for {self.owner.name}**\n"
            f"- Scheduled {num_tasks} out of {num_incomplete} incomplete tasks\n"
            f"- Total time: {total_time} minutes out of {available_time} minutes available\n"
            f"- Time remaining: {available_time - total_time} minutes\n"
        )

        # Explain prioritization strategy
        explanation_parts.append(
            "\n\U0001f3af **Prioritization Strategy:**\n"
            "Tasks are sorted by priority (highest first), then by duration (shorter first for equal priorities). "
            "This ensures critical tasks are completed while maximizing the number of tasks that fit in available time.\n"
        )

        # List scheduled tasks with reasoning
        explanation_parts.append("\n\U0001f4dd **Scheduled Tasks:**")
        for i, task in enumerate(self.daily_plan, 1):
            explanation_parts.append(
                f"{i}. **{task.name}** ({task.pet.name}) - "
                f"{task.duration_minutes} min, Priority {task.priority}/5, {task.task_type.value}"
            )

        # List skipped tasks if any
        scheduled_task_ids = {id(task) for task in self.daily_plan}
        skipped_tasks = [
            task for task in self.get_incomplete_tasks()
            if id(task) not in scheduled_task_ids
        ]

        if skipped_tasks:
            explanation_parts.append(
                f"\n\u26a0\ufe0f **Tasks Not Scheduled ({len(skipped_tasks)}):**\n"
                "These tasks could not fit in the available time:"
            )
            for task in skipped_tasks:
                explanation_parts.append(
                    f"- {task.name} ({task.pet.name}) - "
                    f"{task.duration_minutes} min, Priority {task.priority}/5"
                )

        return "\n".join(explanation_parts)

    def get_schedule(self) -> List[Task]:
        """Returns the current daily plan."""
        return self.daily_plan

    def sort_by_time(self) -> List[Task]:
        """
        Sorts tasks by their scheduled time.

        Returns:
            List of tasks sorted by scheduled_time (tasks without time come last)
        """
        # Separate tasks with and without scheduled times
        scheduled = [t for t in self.tasks if t.scheduled_time]
        unscheduled = [t for t in self.tasks if not t.scheduled_time]

        # Sort scheduled tasks by time
        scheduled.sort(key=lambda t: t.scheduled_time)

        # Return scheduled first, then unscheduled
        return scheduled + unscheduled

    def detect_conflicts(self) -> List[Dict[str, any]]:
        """
        Detects time conflicts between tasks.

        A conflict occurs when two tasks have overlapping time slots.

        Returns:
            List of conflict dictionaries with 'task1', 'task2', and 'reason' keys
        """
        conflicts = []

        # Only check tasks with scheduled times
        scheduled_tasks = [t for t in self.tasks if t.scheduled_time and not t.completed]

        # Check each pair of tasks for time overlap
        for i, task1 in enumerate(scheduled_tasks):
            for task2 in scheduled_tasks[i + 1:]:
                # Check if tasks overlap
                if self._tasks_overlap(task1, task2):
                    conflicts.append({
                        'task1': task1,
                        'task2': task2,
                        'reason': f"Both scheduled at {task1.scheduled_time} with overlapping times"
                    })

        return conflicts

    def _tasks_overlap(self, task1: Task, task2: Task) -> bool:
        """
        Check if two tasks have overlapping time slots.

        Args:
            task1: First task
            task2: Second task

        Returns:
            True if tasks overlap, False otherwise
        """
        if not task1.scheduled_time or not task2.scheduled_time:
            return False

        # Parse times
        start1 = datetime.strptime(task1.scheduled_time, '%H:%M')
        end1 = start1 + timedelta(minutes=task1.duration_minutes)

        start2 = datetime.strptime(task2.scheduled_time, '%H:%M')
        end2 = start2 + timedelta(minutes=task2.duration_minutes)

        # Check for overlap: task1 starts before task2 ends AND task2 starts before task1 ends
        return start1 < end2 and start2 < end1

    def get_conflict_warnings(self) -> str:
        """
        Generates a human-readable warning message about task conflicts.

        Returns:
            Warning message string, or empty string if no conflicts
        """
        conflicts = self.detect_conflicts()

        if not conflicts:
            return ""

        warnings = [f"\u26a0\ufe0f Found {len(conflicts)} scheduling conflict(s):\n"]

        for i, conflict in enumerate(conflicts, 1):
            task1 = conflict['task1']
            task2 = conflict['task2']
            warnings.append(
                f"{i}. {task1.name} ({task1.scheduled_time}-{task1.get_end_time()}) "
                f"overlaps with {task2.name} ({task2.scheduled_time}-{task2.get_end_time()})"
            )

        return "\n".join(warnings)
