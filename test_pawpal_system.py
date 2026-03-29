"""
Tests for PawPal+ System

This module contains comprehensive tests for the scheduling logic.
"""

import pytest
from datetime import datetime, timedelta
from pawpal_system import Owner, Pet, Task, Scheduler, TaskType, Frequency


class TestOwner:
    """Tests for Owner class."""

    def test_owner_creation(self):
        """Test creating an owner with basic attributes."""
        owner = Owner(name="Alice", available_time_minutes=180)
        assert owner.name == "Alice"
        assert owner.available_time_minutes == 180
        assert len(owner.pets) == 0

    def test_owner_add_pet(self):
        """Test adding pets to an owner."""
        owner = Owner(name="Bob", available_time_minutes=240)
        pet = Pet(name="Max", species="dog", age=3)
        owner.add_pet(pet)

        assert len(owner.pets) == 1
        assert pet in owner.pets
        assert pet.owner == owner

    def test_owner_preferences(self):
        """Test setting and updating owner preferences."""
        owner = Owner(name="Carol", available_time_minutes=120)
        owner.set_preferences({"morning_person": True, "prefers_walks": True})

        assert owner.preferences["morning_person"] is True
        assert owner.preferences["prefers_walks"] is True


class TestPet:
    """Tests for Pet class."""

    def test_pet_creation(self):
        """Test creating a pet with basic attributes."""
        pet = Pet(name="Luna", species="cat", age=2)
        assert pet.name == "Luna"
        assert pet.species == "cat"
        assert pet.age == 2
        assert len(pet.special_needs) == 0

    def test_pet_special_needs(self):
        """Test adding special needs to a pet."""
        pet = Pet(name="Charlie", species="dog", age=5)
        pet.add_special_need("medication")
        pet.add_special_need("gentle exercise")

        assert len(pet.special_needs) == 2
        assert "medication" in pet.special_needs

        # Test no duplicates
        pet.add_special_need("medication")
        assert len(pet.special_needs) == 2

    def test_pet_get_info(self):
        """Test getting pet information."""
        owner = Owner(name="Dave", available_time_minutes=200)
        pet = Pet(name="Buddy", species="dog", age=4, owner=owner)

        info = pet.get_info()
        assert info["name"] == "Buddy"
        assert info["species"] == "dog"
        assert info["age"] == 4
        assert info["owner"] == "Dave"


class TestTask:
    """Tests for Task class."""

    def test_task_creation(self):
        """Test creating a task with valid attributes."""
        pet = Pet(name="Mochi", species="cat", age=1)
        task = Task(
            name="Morning feed",
            duration_minutes=10,
            priority=5,
            task_type=TaskType.FEED,
            pet=pet
        )

        assert task.name == "Morning feed"
        assert task.duration_minutes == 10
        assert task.priority == 5
        assert task.completed is False

    def test_task_validation_priority(self):
        """Test that invalid priority raises an error."""
        pet = Pet(name="Rex", species="dog", age=3)

        with pytest.raises(ValueError, match="Priority must be between 1 and 5"):
            Task(
                name="Walk",
                duration_minutes=30,
                priority=6,
                task_type=TaskType.WALK,
                pet=pet
            )

    def test_task_validation_duration(self):
        """Test that invalid duration raises an error."""
        pet = Pet(name="Whiskers", species="cat", age=2)

        with pytest.raises(ValueError, match="Duration must be positive"):
            Task(
                name="Play",
                duration_minutes=0,
                priority=3,
                task_type=TaskType.PLAYTIME,
                pet=pet
            )

    def test_task_mark_complete(self):
        """Test marking a task as complete."""
        pet = Pet(name="Bella", species="dog", age=5)
        task = Task(
            name="Medication",
            duration_minutes=5,
            priority=5,
            task_type=TaskType.MEDICATION,
            pet=pet
        )

        assert task.completed is False
        task.mark_complete()
        assert task.completed is True


class TestScheduler:
    """Tests for Scheduler class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.owner = Owner(name="Jordan", available_time_minutes=120)
        self.pet1 = Pet(name="Max", species="dog", age=3)
        self.pet2 = Pet(name="Luna", species="cat", age=2)
        self.owner.add_pet(self.pet1)
        self.owner.add_pet(self.pet2)
        self.scheduler = Scheduler(self.owner)

    def test_scheduler_creation(self):
        """Test creating a scheduler."""
        assert self.scheduler.owner == self.owner
        assert len(self.scheduler.pets) == 2
        assert len(self.scheduler.tasks) == 0

    def test_add_task(self):
        """Test adding tasks to the scheduler."""
        task = Task(
            name="Morning walk",
            duration_minutes=30,
            priority=4,
            task_type=TaskType.WALK,
            pet=self.pet1
        )
        self.scheduler.add_task(task)

        assert len(self.scheduler.tasks) == 1
        assert task in self.scheduler.tasks

    def test_prioritize_tasks(self):
        """Test that tasks are prioritized correctly."""
        # Create tasks with different priorities
        task1 = Task("Low priority", 20, 1, TaskType.PLAYTIME, self.pet1)
        task2 = Task("High priority", 15, 5, TaskType.MEDICATION, self.pet1)
        task3 = Task("Medium priority", 25, 3, TaskType.WALK, self.pet1)
        task4 = Task("High priority short", 10, 5, TaskType.FEED, self.pet1)

        self.scheduler.add_task(task1)
        self.scheduler.add_task(task2)
        self.scheduler.add_task(task3)
        self.scheduler.add_task(task4)

        prioritized = self.scheduler.prioritize_tasks()

        # Check order: highest priority first, shorter duration for equal priorities
        assert prioritized[0].priority == 5
        assert prioritized[1].priority == 5
        assert prioritized[0].duration_minutes < prioritized[1].duration_minutes
        assert prioritized[2].priority == 3
        assert prioritized[3].priority == 1

    def test_generate_daily_plan_within_time(self):
        """Test schedule generation with sufficient time."""
        task1 = Task("Walk", 30, 5, TaskType.WALK, self.pet1)
        task2 = Task("Feed", 10, 5, TaskType.FEED, self.pet1)
        task3 = Task("Play", 20, 3, TaskType.PLAYTIME, self.pet1)

        self.scheduler.add_task(task1)
        self.scheduler.add_task(task2)
        self.scheduler.add_task(task3)

        plan = self.scheduler.generate_daily_plan()

        # All tasks should fit (total 60 minutes, available 120)
        assert len(plan) == 3
        assert self.scheduler.get_total_scheduled_time() == 60

    def test_generate_daily_plan_exceeds_time(self):
        """Test schedule generation when tasks exceed available time."""
        # Total tasks: 150 minutes, available: 120 minutes
        task1 = Task("Long walk", 60, 5, TaskType.WALK, self.pet1)
        task2 = Task("Feed", 10, 4, TaskType.FEED, self.pet1)
        task3 = Task("Play", 40, 3, TaskType.PLAYTIME, self.pet1)
        task4 = Task("Grooming", 40, 2, TaskType.GROOMING, self.pet1)

        self.scheduler.add_task(task1)
        self.scheduler.add_task(task2)
        self.scheduler.add_task(task3)
        self.scheduler.add_task(task4)

        plan = self.scheduler.generate_daily_plan()

        # Should prioritize and fit within time
        assert self.scheduler.get_total_scheduled_time() <= 120
        assert len(plan) < 4  # Not all tasks will fit

        # Highest priority tasks should be included
        assert task1 in plan  # priority 5
        assert task2 in plan  # priority 4

    def test_generate_daily_plan_completed_tasks_excluded(self):
        """Test that completed tasks are excluded from scheduling."""
        task1 = Task("Walk", 30, 5, TaskType.WALK, self.pet1)
        task2 = Task("Feed", 10, 5, TaskType.FEED, self.pet1)
        task1.mark_complete()

        self.scheduler.add_task(task1)
        self.scheduler.add_task(task2)

        plan = self.scheduler.generate_daily_plan()

        # Only incomplete task should be scheduled
        assert len(plan) == 1
        assert task2 in plan
        assert task1 not in plan

    def test_get_tasks_by_pet(self):
        """Test filtering tasks by pet."""
        task1 = Task("Walk dog", 30, 4, TaskType.WALK, self.pet1)
        task2 = Task("Feed cat", 10, 5, TaskType.FEED, self.pet2)
        task3 = Task("Play with dog", 20, 3, TaskType.PLAYTIME, self.pet1)

        self.scheduler.add_task(task1)
        self.scheduler.add_task(task2)
        self.scheduler.add_task(task3)

        dog_tasks = self.scheduler.get_tasks_by_pet(self.pet1)
        cat_tasks = self.scheduler.get_tasks_by_pet(self.pet2)

        assert len(dog_tasks) == 2
        assert len(cat_tasks) == 1
        assert task1 in dog_tasks
        assert task3 in dog_tasks
        assert task2 in cat_tasks

    def test_get_tasks_by_type(self):
        """Test filtering tasks by type."""
        task1 = Task("Walk", 30, 4, TaskType.WALK, self.pet1)
        task2 = Task("Feed cat", 10, 5, TaskType.FEED, self.pet2)
        task3 = Task("Feed dog", 10, 5, TaskType.FEED, self.pet1)

        self.scheduler.add_task(task1)
        self.scheduler.add_task(task2)
        self.scheduler.add_task(task3)

        feed_tasks = self.scheduler.get_tasks_by_type(TaskType.FEED)
        walk_tasks = self.scheduler.get_tasks_by_type(TaskType.WALK)

        assert len(feed_tasks) == 2
        assert len(walk_tasks) == 1

    def test_explain_reasoning_no_plan(self):
        """Test explanation when no plan exists."""
        explanation = self.scheduler.explain_reasoning()
        assert "No tasks have been scheduled" in explanation

    def test_explain_reasoning_with_plan(self):
        """Test explanation after generating a plan."""
        task1 = Task("Walk", 30, 5, TaskType.WALK, self.pet1)
        task2 = Task("Feed", 10, 4, TaskType.FEED, self.pet1)

        self.scheduler.add_task(task1)
        self.scheduler.add_task(task2)
        self.scheduler.generate_daily_plan()

        explanation = self.scheduler.explain_reasoning()

        assert "Jordan" in explanation
        assert "Scheduled 2" in explanation
        assert "Walk" in explanation
        assert "Feed" in explanation
        assert "Priority" in explanation

    def test_empty_schedule(self):
        """Test behavior with no tasks."""
        plan = self.scheduler.generate_daily_plan()
        assert len(plan) == 0
        assert self.scheduler.get_total_scheduled_time() == 0

    def test_zero_available_time(self):
        """Test schedule generation with zero available time."""
        owner = Owner(name="Busy Person", available_time_minutes=0)
        scheduler = Scheduler(owner)
        pet = Pet(name="Spot", species="dog", age=2)
        owner.add_pet(pet)

        task = Task("Walk", 30, 5, TaskType.WALK, pet)
        scheduler.add_task(task)

        plan = scheduler.generate_daily_plan()
        assert len(plan) == 0


class TestIntegration:
    """Integration tests for complete workflows."""

    def test_complete_workflow(self):
        """Test a complete workflow from owner creation to scheduling."""
        # Create owner
        owner = Owner(name="Sarah", available_time_minutes=180)
        owner.set_preferences({"morning_person": True})

        # Create pets
        dog = Pet(name="Rex", species="dog", age=4)
        cat = Pet(name="Mittens", species="cat", age=2)
        dog.add_special_need("joint medication")

        owner.add_pet(dog)
        owner.add_pet(cat)

        # Create scheduler
        scheduler = Scheduler(owner)

        # Add tasks
        tasks = [
            Task("Morning walk", 45, 5, TaskType.WALK, dog),
            Task("Dog medication", 5, 5, TaskType.MEDICATION, dog),
            Task("Feed dog", 10, 5, TaskType.FEED, dog),
            Task("Feed cat", 10, 5, TaskType.FEED, cat),
            Task("Play with dog", 30, 3, TaskType.PLAYTIME, dog),
            Task("Cat enrichment", 20, 3, TaskType.ENRICHMENT, cat),
            Task("Evening walk", 45, 4, TaskType.WALK, dog),
            Task("Grooming", 60, 2, TaskType.GROOMING, dog),
        ]

        for task in tasks:
            scheduler.add_task(task)

        # Generate plan
        plan = scheduler.generate_daily_plan()

        # Verify results
        assert len(plan) > 0
        assert scheduler.get_total_scheduled_time() <= 180

        # High priority tasks should be in plan
        task_names = [task.name for task in plan]
        assert "Dog medication" in task_names  # Critical priority 5

        # Get explanation
        explanation = scheduler.explain_reasoning()
        assert len(explanation) > 0
        assert "Sarah" in explanation

        # Complete a task
        plan[0].mark_complete()
        assert plan[0].completed is True

        # Generate new plan should exclude completed task
        new_plan = scheduler.generate_daily_plan()
        assert plan[0] not in new_plan


class TestTimeBasedFeatures:
    """Tests for time-based scheduling features."""

    def setup_method(self):
        """Set up test fixtures."""
        self.owner = Owner(name="Alex", available_time_minutes=240)
        self.pet = Pet(name="Buddy", species="dog", age=4)
        self.owner.add_pet(self.pet)
        self.scheduler = Scheduler(self.owner)

    def test_task_with_scheduled_time(self):
        """Test creating a task with a scheduled time."""
        task = Task(
            "Morning walk",
            30,
            5,
            TaskType.WALK,
            self.pet,
            scheduled_time="08:00"
        )
        assert task.scheduled_time == "08:00"
        assert task.get_end_time() == "08:30"

    def test_task_invalid_time_format(self):
        """Test that invalid time format raises an error."""
        with pytest.raises(ValueError, match="Scheduled time must be in HH:MM format"):
            Task(
                "Walk",
                30,
                5,
                TaskType.WALK,
                self.pet,
                scheduled_time="8:00am"
            )

    def test_task_time_out_of_range(self):
        """Test that out-of-range time raises an error."""
        with pytest.raises(ValueError, match="Scheduled time must be in HH:MM format"):
            Task(
                "Walk",
                30,
                5,
                TaskType.WALK,
                self.pet,
                scheduled_time="25:00"
            )

    def test_get_end_time_calculation(self):
        """Test end time calculation for various durations."""
        task1 = Task("Short task", 15, 3, TaskType.FEED, self.pet, scheduled_time="09:45")
        assert task1.get_end_time() == "10:00"

        task2 = Task("Long task", 90, 3, TaskType.GROOMING, self.pet, scheduled_time="14:30")
        assert task2.get_end_time() == "16:00"

    def test_get_end_time_without_scheduled_time(self):
        """Test that get_end_time returns None when no scheduled_time is set."""
        task = Task("Unscheduled", 30, 3, TaskType.WALK, self.pet)
        assert task.get_end_time() is None

    def test_sort_by_time(self):
        """Test sorting tasks by scheduled time."""
        task1 = Task("Afternoon", 30, 3, TaskType.WALK, self.pet, scheduled_time="14:00")
        task2 = Task("Morning", 30, 3, TaskType.FEED, self.pet, scheduled_time="08:00")
        task3 = Task("Evening", 30, 3, TaskType.PLAYTIME, self.pet, scheduled_time="18:00")
        task4 = Task("Unscheduled", 30, 3, TaskType.GROOMING, self.pet)

        self.scheduler.add_task(task1)
        self.scheduler.add_task(task2)
        self.scheduler.add_task(task3)
        self.scheduler.add_task(task4)

        sorted_tasks = self.scheduler.sort_by_time()

        # Check that scheduled tasks come first in time order
        assert sorted_tasks[0] == task2  # 08:00
        assert sorted_tasks[1] == task1  # 14:00
        assert sorted_tasks[2] == task3  # 18:00
        assert sorted_tasks[3] == task4  # Unscheduled comes last

    def test_detect_conflicts_no_conflicts(self):
        """Test conflict detection when tasks don't overlap."""
        task1 = Task("Morning", 30, 5, TaskType.WALK, self.pet, scheduled_time="08:00")
        task2 = Task("Afternoon", 30, 5, TaskType.FEED, self.pet, scheduled_time="14:00")

        self.scheduler.add_task(task1)
        self.scheduler.add_task(task2)

        conflicts = self.scheduler.detect_conflicts()
        assert len(conflicts) == 0

    def test_detect_conflicts_exact_overlap(self):
        """Test conflict detection when tasks start at the same time."""
        task1 = Task("Walk dog", 30, 5, TaskType.WALK, self.pet, scheduled_time="09:00")
        task2 = Task("Feed dog", 15, 5, TaskType.FEED, self.pet, scheduled_time="09:00")

        self.scheduler.add_task(task1)
        self.scheduler.add_task(task2)

        conflicts = self.scheduler.detect_conflicts()
        assert len(conflicts) == 1
        assert conflicts[0]['task1'] == task1
        assert conflicts[0]['task2'] == task2

    def test_detect_conflicts_partial_overlap(self):
        """Test conflict detection when tasks partially overlap."""
        task1 = Task("Walk", 60, 5, TaskType.WALK, self.pet, scheduled_time="09:00")
        task2 = Task("Grooming", 45, 4, TaskType.GROOMING, self.pet, scheduled_time="09:30")

        self.scheduler.add_task(task1)
        self.scheduler.add_task(task2)

        conflicts = self.scheduler.detect_conflicts()
        assert len(conflicts) == 1

    def test_detect_conflicts_adjacent_tasks(self):
        """Test that adjacent tasks (no overlap) don't conflict."""
        task1 = Task("Morning walk", 30, 5, TaskType.WALK, self.pet, scheduled_time="08:00")
        task2 = Task("Feed", 15, 5, TaskType.FEED, self.pet, scheduled_time="08:30")

        self.scheduler.add_task(task1)
        self.scheduler.add_task(task2)

        conflicts = self.scheduler.detect_conflicts()
        assert len(conflicts) == 0

    def test_get_conflict_warnings(self):
        """Test generating human-readable conflict warnings."""
        task1 = Task("Walk", 60, 5, TaskType.WALK, self.pet, scheduled_time="09:00")
        task2 = Task("Grooming", 30, 4, TaskType.GROOMING, self.pet, scheduled_time="09:30")

        self.scheduler.add_task(task1)
        self.scheduler.add_task(task2)

        warning = self.scheduler.get_conflict_warnings()
        assert "conflict" in warning.lower()
        assert "Walk" in warning
        assert "Grooming" in warning

    def test_no_conflict_warnings_when_no_conflicts(self):
        """Test that no warning is generated when there are no conflicts."""
        task1 = Task("Morning", 30, 5, TaskType.WALK, self.pet, scheduled_time="08:00")
        task2 = Task("Afternoon", 30, 5, TaskType.FEED, self.pet, scheduled_time="14:00")

        self.scheduler.add_task(task1)
        self.scheduler.add_task(task2)

        warning = self.scheduler.get_conflict_warnings()
        assert warning == ""


class TestRecurringTasks:
    """Tests for recurring task functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.owner = Owner(name="Sam", available_time_minutes=180)
        self.pet = Pet(name="Fluffy", species="cat", age=3)
        self.owner.add_pet(self.pet)
        self.scheduler = Scheduler(self.owner)

    def test_task_with_frequency(self):
        """Test creating a task with a frequency."""
        task = Task(
            "Daily walk",
            30,
            5,
            TaskType.WALK,
            self.pet,
            frequency=Frequency.DAILY
        )
        assert task.frequency == Frequency.DAILY

    def test_create_recurring_instance_daily(self):
        """Test creating a recurring instance for a daily task."""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        task = Task(
            "Daily medication",
            5,
            5,
            TaskType.MEDICATION,
            self.pet,
            frequency=Frequency.DAILY,
            due_date=today
        )

        new_task = task.create_recurring_instance()

        assert new_task.name == task.name
        assert new_task.frequency == Frequency.DAILY
        assert new_task.completed is False
        assert new_task.due_date == today + timedelta(days=1)

    def test_create_recurring_instance_weekly(self):
        """Test creating a recurring instance for a weekly task."""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        task = Task(
            "Weekly grooming",
            60,
            3,
            TaskType.GROOMING,
            self.pet,
            frequency=Frequency.WEEKLY,
            due_date=today
        )

        new_task = task.create_recurring_instance()
        assert new_task.due_date == today + timedelta(weeks=1)

    def test_cannot_create_recurring_instance_for_once(self):
        """Test that one-time tasks cannot create recurring instances."""
        task = Task(
            "One-time task",
            30,
            3,
            TaskType.WALK,
            self.pet,
            frequency=Frequency.ONCE
        )

        with pytest.raises(ValueError, match="Cannot create recurring instance"):
            task.create_recurring_instance()

    def test_mark_task_complete_creates_recurring_instance(self):
        """Test that marking a recurring task complete creates a new instance."""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        task = Task(
            "Daily walk",
            30,
            5,
            TaskType.WALK,
            self.pet,
            frequency=Frequency.DAILY,
            due_date=today
        )

        self.scheduler.add_task(task)
        initial_count = len(self.scheduler.tasks)

        # Mark complete - should create a new instance
        new_task = self.scheduler.mark_task_complete(task)

        assert task.completed is True
        assert new_task is not None
        assert new_task.completed is False
        assert len(self.scheduler.tasks) == initial_count + 1

    def test_mark_task_complete_once_no_new_instance(self):
        """Test that marking a one-time task complete doesn't create new instance."""
        task = Task(
            "One-time task",
            30,
            3,
            TaskType.WALK,
            self.pet,
            frequency=Frequency.ONCE
        )

        self.scheduler.add_task(task)
        initial_count = len(self.scheduler.tasks)

        new_task = self.scheduler.mark_task_complete(task)

        assert task.completed is True
        assert new_task is None
        assert len(self.scheduler.tasks) == initial_count
