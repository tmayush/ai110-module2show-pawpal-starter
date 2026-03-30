"""
PawPal+ Streamlit Application

This is the interactive UI for the PawPal+ pet care scheduling system.
"""

import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler, TaskType

st.set_page_config(page_title="PawPal+", page_icon="\U0001f43e", layout="centered")

# Initialize session state
if "owner" not in st.session_state:
    st.session_state.owner = None
if "scheduler" not in st.session_state:
    st.session_state.scheduler = None
if "pets" not in st.session_state:
    st.session_state.pets = []
if "tasks" not in st.session_state:
    st.session_state.tasks = []
if "schedule_generated" not in st.session_state:
    st.session_state.schedule_generated = False


def reset_schedule():
    """Reset the schedule when tasks or settings change."""
    st.session_state.schedule_generated = False


st.title("\U0001f43e PawPal+")
st.markdown("**Your AI-powered pet care planning assistant**")

# Sidebar for scenario info
with st.sidebar:
    st.header("About PawPal+")
    st.markdown(
        """
        PawPal+ helps busy pet owners plan their daily pet care tasks.

        **Features:**
        - Track multiple pets and care tasks
        - Consider time constraints
        - Prioritize based on importance
        - Generate optimized schedules
        - Explain scheduling decisions
        """
    )

    st.divider()

    st.header("How to Use")
    st.markdown(
        """
        1. Enter your information
        2. Add your pet(s)
        3. Create care tasks
        4. Generate your daily plan
        5. Review and follow the schedule
        """
    )

# Main content
st.header("1. Owner Information")

col1, col2 = st.columns(2)
with col1:
    owner_name = st.text_input(
        "Your name",
        value="Jordan",
        key="owner_name",
        on_change=reset_schedule
    )
with col2:
    available_time = st.number_input(
        "Available time (minutes/day)",
        min_value=0,
        max_value=1440,
        value=180,
        step=15,
        key="available_time",
        on_change=reset_schedule
    )

# Create or update owner
if owner_name:
    if st.session_state.owner is None or st.session_state.owner.name != owner_name:
        st.session_state.owner = Owner(
            name=owner_name,
            available_time_minutes=available_time
        )
        st.session_state.scheduler = Scheduler(st.session_state.owner)
    else:
        st.session_state.owner.available_time_minutes = available_time

st.divider()

# Pet Management
st.header("2. Your Pets")

col1, col2, col3 = st.columns(3)
with col1:
    pet_name = st.text_input("Pet name", value="", key="pet_name_input")
with col2:
    pet_species = st.selectbox(
        "Species",
        ["Dog", "Cat", "Bird", "Rabbit", "Other"],
        key="species_input"
    )
with col3:
    pet_age = st.number_input(
        "Age (years)",
        min_value=0,
        max_value=30,
        value=3,
        key="age_input"
    )

special_needs = st.text_input(
    "Special needs (optional)",
    placeholder="e.g., medication, joint issues, anxiety",
    key="special_needs_input"
)

if st.button("Add Pet", type="secondary"):
    if pet_name and st.session_state.owner:
        new_pet = Pet(
            name=pet_name,
            species=pet_species.lower(),
            age=pet_age
        )
        if special_needs:
            new_pet.add_special_need(special_needs)

        st.session_state.owner.add_pet(new_pet)
        st.session_state.pets.append(new_pet)

        # Update scheduler
        if st.session_state.scheduler:
            st.session_state.scheduler.pets = st.session_state.owner.pets

        reset_schedule()
        st.success(f"Added {pet_name}!")
        st.rerun()
    else:
        st.error("Please enter your name and pet name first.")

# Display current pets
if st.session_state.pets:
    st.subheader("Your Pets")
    for i, pet in enumerate(st.session_state.pets):
        with st.expander(f"{pet.name} ({pet.species.capitalize()})"):
            st.write(f"**Age:** {pet.age} years")
            if pet.special_needs:
                st.write(f"**Special needs:** {', '.join(pet.special_needs)}")
else:
    st.info("Add your first pet above")

st.divider()

# Task Management
st.header("3. Care Tasks")

if not st.session_state.pets:
    st.warning("Please add at least one pet before creating tasks.")
else:
    col1, col2 = st.columns(2)
    with col1:
        task_name = st.text_input(
            "Task name",
            placeholder="e.g., Morning walk",
            key="task_name_input"
        )
        task_pet = st.selectbox(
            "Pet",
            options=st.session_state.pets,
            format_func=lambda p: f"{p.name} ({p.species})",
            key="task_pet_input"
        )
        task_type = st.selectbox(
            "Task type",
            options=[t for t in TaskType],
            format_func=lambda t: t.value.capitalize(),
            key="task_type_input"
        )

    with col2:
        task_duration = st.number_input(
            "Duration (minutes)",
            min_value=1,
            max_value=240,
            value=20,
            key="task_duration_input"
        )
        task_priority = st.select_slider(
            "Priority",
            options=[1, 2, 3, 4, 5],
            value=3,
            format_func=lambda x: f"{x} {'*' * x}",
            key="task_priority_input"
        )

    if st.button("Add Task", type="secondary"):
        if task_name and st.session_state.scheduler:
            new_task = Task(
                name=task_name,
                duration_minutes=task_duration,
                priority=task_priority,
                task_type=task_type,
                pet=task_pet
            )
            st.session_state.scheduler.add_task(new_task)
            st.session_state.tasks.append(new_task)
            reset_schedule()
            st.success(f"Added task: {task_name}")
            st.rerun()
        else:
            st.error("Please enter a task name.")

# Display current tasks
if st.session_state.tasks:
    st.subheader("All Tasks")

    # Task statistics
    incomplete_tasks = [t for t in st.session_state.tasks if not t.completed]
    completed_tasks = [t for t in st.session_state.tasks if t.completed]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Tasks", len(st.session_state.tasks))
    with col2:
        st.metric("Incomplete", len(incomplete_tasks))
    with col3:
        st.metric("Completed", len(completed_tasks))

    # Display tasks
    for i, task in enumerate(st.session_state.tasks):
        status_icon = "Done" if task.completed else "Pending"
        with st.expander(
            f"[{status_icon}] {task.name} - {task.pet.name} ({task.duration_minutes} min, Priority {task.priority})"
        ):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**Type:** {task.task_type.value.capitalize()}")
                st.write(f"**Duration:** {task.duration_minutes} minutes")
                st.write(f"**Priority:** {task.priority}/5")
                st.write(f"**Pet:** {task.pet.name} ({task.pet.species})")
            with col2:
                if not task.completed:
                    if st.button("Mark Complete", key=f"complete_{i}"):
                        task.mark_complete()
                        reset_schedule()
                        st.rerun()
                else:
                    st.success("Completed!")
else:
    st.info("Add your first task above")

st.divider()

# Schedule Generation
st.header("4. Generate Schedule")

if not st.session_state.tasks:
    st.warning("Please add at least one task before generating a schedule.")
else:
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Generate Daily Plan", type="primary", use_container_width=True):
            if st.session_state.scheduler:
                with st.spinner("Creating your optimized schedule..."):
                    st.session_state.scheduler.generate_daily_plan()
                    st.session_state.schedule_generated = True
                st.success("Schedule generated!")
                st.rerun()

    with col2:
        if st.button("Reset All Tasks", type="secondary", use_container_width=True):
            for task in st.session_state.tasks:
                task.completed = False
            reset_schedule()
            st.success("All tasks reset!")
            st.rerun()

    with col3:
        if st.button("Clear All", type="secondary", use_container_width=True):
            st.session_state.tasks = []
            st.session_state.pets = []
            if st.session_state.scheduler:
                st.session_state.scheduler.tasks = []
                st.session_state.scheduler.pets = []
                st.session_state.scheduler.daily_plan = []
            if st.session_state.owner:
                st.session_state.owner.pets = []
            reset_schedule()
            st.success("Everything cleared!")
            st.rerun()

st.divider()

# Display Schedule
if st.session_state.schedule_generated and st.session_state.scheduler:
    st.header("Your Daily Schedule")

    plan = st.session_state.scheduler.get_schedule()

    if plan:
        # Summary metrics
        total_time = st.session_state.scheduler.get_total_scheduled_time()
        available = st.session_state.owner.available_time_minutes
        remaining = available - total_time

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Scheduled Tasks", len(plan))
        with col2:
            st.metric("Total Time", f"{total_time} min")
        with col3:
            st.metric("Available Time", f"{available} min")
        with col4:
            st.metric("Time Remaining", f"{remaining} min")

        # Visual schedule
        st.subheader("Task List")
        for i, task in enumerate(plan, 1):
            priority_color = {
                5: "red",
                4: "orange",
                3: "yellow",
                2: "green",
                1: "blue"
            }.get(task.priority, "gray")

            st.markdown(
                f"""
                **{i}. {task.name}** (Priority: {task.priority}/5)
                - Pet: {task.pet.name} ({task.pet.species})
                - Type: {task.task_type.value.capitalize()}
                - Duration: {task.duration_minutes} minutes
                """
            )

        st.divider()

        # Explanation
        st.subheader("Scheduling Explanation")
        explanation = st.session_state.scheduler.explain_reasoning()
        st.markdown(explanation)

    else:
        st.info("No tasks could be scheduled. Check your available time or task priorities.")
else:
    if st.session_state.tasks:
        st.info("Click 'Generate Daily Plan' to see your optimized schedule")

# Footer
st.divider()
st.caption("Built with Streamlit and Python | PawPal+")
