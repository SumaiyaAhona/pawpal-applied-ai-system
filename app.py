import streamlit as st
from datetime import datetime, timedelta
from pawpal_system import Task, Pet, Owner, Scheduler

# --- Page setup ---
st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# --- Intro ---
st.markdown(
    """
Welcome to the PawPal+ app.

This demo shows your pet care tasks and schedule. Add pets, create tasks,
and see them sorted, with conflict detection and recurring tasks.
"""
)

# --- Session state setup ---
if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jordan", Scheduler())
if "tasks" not in st.session_state:
    st.session_state.tasks = []

# Default values for Owner Settings (stored so they survive reruns)
if "owner_first_name" not in st.session_state:
    st.session_state.owner_first_name = "Jordan"
if "owner_last_name" not in st.session_state:
    st.session_state.owner_last_name = ""
if "available_minutes" not in st.session_state:
    st.session_state.available_minutes = 60
if "daily_budget" not in st.session_state:
    st.session_state.daily_budget = 10.0

# --- Owner Settings Sidebar ---
with st.sidebar:
    st.header("Owner Settings")

    first_name = st.text_input("First name", value=st.session_state.owner_first_name)
    last_name  = st.text_input("Last name",  value=st.session_state.owner_last_name)
    available_minutes = st.number_input(
        "Available minutes per day",
        min_value=0, max_value=1440, step=5,
        value=st.session_state.available_minutes,
    )
    daily_budget = st.number_input(
        "Max daily pet-care budget ($)",
        min_value=0.0, step=0.50,
        value=st.session_state.daily_budget,
    )

    if st.button("Save owner"):
        # Write inputs back into session state so the whole app can read them
        st.session_state.owner_first_name = first_name
        st.session_state.owner_last_name  = last_name
        st.session_state.available_minutes = available_minutes
        st.session_state.daily_budget      = daily_budget

        # Keep the Owner object's name in sync with the sidebar
        full_name = f"{first_name} {last_name}".strip()
        st.session_state.owner.name = full_name

        st.success("Owner settings saved!")

    # Always show current saved values below the button
    st.divider()
    st.caption("Current settings")
    st.write(f"**Name:** {st.session_state.owner_first_name} {st.session_state.owner_last_name}".strip())
    st.write(f"**Time available:** {st.session_state.available_minutes} min/day")
    st.write(f"**Daily budget:** ${st.session_state.daily_budget:.2f}")

# --- Add Pet Section ---
st.subheader("Add a Pet")
owner_name = st.text_input("Owner name", value=st.session_state.owner.name)
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Add pet"):
    if pet_name:
        st.session_state.owner.add_pet(Pet(pet_name, species))
        st.success(f"Pet '{pet_name}' added!")
    else:
        st.warning("Enter a pet name!")

# --- Your Pets Section ---
st.subheader("Your Pets")

if not st.session_state.owner.pets:
    st.info("No pets added yet. Use the form above to add one.")
else:
    # Build a list of names for the dropdown
    pet_names = [p.name for p in st.session_state.owner.pets]
    selected_pet = st.selectbox("Select a pet to view its tasks", pet_names)

    # Collect tasks that belong to the selected pet, keeping the original index
    # so the Remove button can delete the right item from st.session_state.tasks
    pet_tasks = [
        (i, task)
        for i, task in enumerate(st.session_state.tasks)
        if task["pet"] == selected_pet
    ]

    if not pet_tasks:
        st.info(f"No tasks scheduled for {selected_pet} yet.")
    else:
        st.markdown(f"**Scheduled tasks for {selected_pet}:**")
        for original_index, task in pet_tasks:
            col_info, col_btn = st.columns([5, 1])
            with col_info:
                st.markdown(
                    f"**{task['title']}** &nbsp;|&nbsp; "
                    f"{task['duration_minutes']} min &nbsp;|&nbsp; "
                    f"Priority: **{task['priority']}** &nbsp;|&nbsp; "
                    f"Repeat: {task['repeat']} &nbsp;|&nbsp; "
                    f"Pet: {task['pet']}"
                )
            with col_btn:
                # Use original_index as the key so each button is unique
                if st.button("Remove", key=f"remove_{original_index}"):
                    st.session_state.tasks.pop(original_index)
                    st.rerun()

# --- Add Task Section ---
st.subheader("Add a Task")
col1, col2, col3, col4 = st.columns(4)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
with col4:
    frequency = st.selectbox("Repeat", ["none", "daily", "weekly"])

if st.button("Add task"):
    if not st.session_state.owner.pets:
        st.warning("Add a pet first!")
    else:
        pet = next((p for p in st.session_state.owner.pets if p.name == pet_name), None)
        if pet:
            task = Task(
                task_title,
                datetime.now(),
                priority,
                int(duration),
                frequency=frequency if frequency != "none" else None
            )
            st.session_state.owner.schedule_task(pet, task)
            st.session_state.tasks.append({
                "title": task_title,
                "duration_minutes": int(duration),
                "priority": priority,
                "repeat": frequency,
                "pet": pet.name
            })
            st.success(f"Task '{task_title}' added to {pet.name}!")
        else:
            st.warning(f"No pet named '{pet_name}' found!")

# --- Show Current Tasks ---
st.markdown("### Current Tasks")
if st.session_state.tasks:
    st.table(st.session_state.tasks)
else:
    st.info("No tasks yet. Add one above.")

# --- Generate Daily Schedule Section ---
st.divider()
st.subheader("Generate Daily Schedule")
st.caption("Tasks sorted by priority, checked against your available time, with conflict detection.")

if st.button("Generate daily schedule"):
    if not st.session_state.tasks:
        st.warning("No tasks added yet. Add some tasks above first.")
    else:
        # Priority order: high tasks go first, then medium, then low
        PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

        sorted_tasks = sorted(
            st.session_state.tasks,
            key=lambda t: PRIORITY_ORDER.get(t["priority"], 3)
        )

        # Total minutes needed for all tasks
        total_minutes = sum(t["duration_minutes"] for t in sorted_tasks)

        # Read the owner's available minutes (set in the sidebar; default 60)
        available = st.session_state.get("available_minutes", 60)

        # Warn the owner if the schedule is too packed
        if total_minutes > available:
            st.warning(
                f"Total task time is **{total_minutes} min** but you only have "
                f"**{available} min/day** available. Consider removing or shortening some tasks."
            )
        else:
            st.success(
                f"Schedule fits! Total: **{total_minutes} min** of your **{available} min** available."
            )

        # Show the ordered schedule as a table
        st.markdown("#### Today's Schedule (high priority first)")
        schedule_rows = []
        for task in sorted_tasks:
            schedule_rows.append({
                "Task": task["title"],
                "Pet": task["pet"],
                "Duration (min)": task["duration_minutes"],
                "Priority": task["priority"],
            })
        st.table(schedule_rows)

        # --- Conflict detection (merged from old Advanced Schedule Builder) ---
        # Use the Scheduler object to check for overlapping tasks per pet
        scheduler = st.session_state.owner.scheduler
        for pet in st.session_state.owner.pets:
            conflicts = scheduler.detect_conflicts(pet)
            if conflicts:
                conflict_names = ", ".join(t.title for t in conflicts)
                st.warning(f"⚠ Conflict detected for **{pet.name}**: {conflict_names}")

        # --- Recurring task queuing (merged from old Advanced Schedule Builder) ---
        # If a completed task repeats daily or weekly, queue its next occurrence
        for pet in st.session_state.owner.pets:
            for task in scheduler.sort_by_time(pet=pet):
                if task.status == "completed" and task.frequency in ("daily", "weekly"):
                    delta = timedelta(days=1 if task.frequency == "daily" else 7)
                    next_task = Task(
                        task.title,
                        task.time + delta,
                        task.priority,
                        task.duration,
                        frequency=task.frequency
                    )
                    pet.add_task(next_task)
                    st.info(
                        f"Recurring task '{task.title}' for {pet.name} queued for "
                        f"{next_task.time.strftime('%Y-%m-%d %H:%M')}."
                    )

# ---------------------------------------------------------------------------
# SMART PAWPAL+ ASSISTANT
# AI / reliability / guardrail feature for the final project.
# Uses rule-based classification so the logic is easy to follow and explain.
# ---------------------------------------------------------------------------
st.divider()
st.subheader("🤖 Smart PawPal+ Assistant")
st.caption("Ask a pet-care question or describe a task idea and get an instant suggestion.")

user_input = st.text_input("What's on your mind about your pet?", placeholder="e.g. my dog ate chocolate, how often should I groom my cat?")

if user_input:
    text = user_input.lower()

    # --- Guardrail: emergency keyword detection ---
    # These keywords signal situations that need a vet immediately.
    EMERGENCY_KEYWORDS = [
        "chocolate", "poison", "poisoned", "toxic", "seizure",
        "seizures", "bleeding", "blood", "trouble breathing",
        "not breathing", "unconscious", "collapsed", "swallowed",
        "ate something", "vomiting blood", "can't walk",
    ]

    # --- Category keyword sets ---
    FEEDING_KEYWORDS    = ["feed", "food", "eat", "hungry", "diet", "meal", "treats", "water", "drink", "nutrition"]
    GROOMING_KEYWORDS   = ["groom", "bath", "bathe", "brush", "nail", "nails", "fur", "hair", "shed", "shampoo"]
    EXERCISE_KEYWORDS   = ["walk", "exercise", "run", "play", "active", "energy", "tired", "outside", "fetch"]
    SCHEDULE_KEYWORDS   = ["schedule", "remind", "appointment", "vet visit", "checkup", "vaccine", "when", "how often", "routine"]

    def classify(text):
        """Return the category that best matches the input text."""
        if any(kw in text for kw in EMERGENCY_KEYWORDS):
            return "emergency"
        if any(kw in text for kw in FEEDING_KEYWORDS):
            return "feeding"
        if any(kw in text for kw in GROOMING_KEYWORDS):
            return "grooming"
        if any(kw in text for kw in EXERCISE_KEYWORDS):
            return "exercise"
        if any(kw in text for kw in SCHEDULE_KEYWORDS):
            return "scheduling"
        return "general"

    # --- Suggestions mapped to each category ---
    SUGGESTIONS = {
        "feeding": {
            "message": "**Feeding tip:** Most adult dogs and cats do well with 2 meals per day at consistent times. Make sure fresh water is always available.",
            "task":    "Add a 'Morning feeding' and 'Evening feeding' task with **medium** priority.",
            "priority": "medium",
        },
        "grooming": {
            "message": "**Grooming tip:** Short-haired pets typically need brushing once a week; long-haired breeds may need daily brushing. Nails should be trimmed every 3–4 weeks.",
            "task":    "Add a 'Weekly brushing' task with **low** priority.",
            "priority": "low",
        },
        "exercise": {
            "message": "**Exercise tip:** Most dogs need at least 30 minutes of activity per day. Puppies and high-energy breeds may need more. Cats benefit from interactive play sessions.",
            "task":    "Add a 'Daily walk or play session' task with **high** priority.",
            "priority": "high",
        },
        "scheduling": {
            "message": "**Scheduling tip:** Annual vet check-ups are recommended for healthy adult pets. Puppies and kittens need more frequent visits for vaccines.",
            "task":    "Add a 'Vet check-up' task with **high** priority and set it to repeat yearly.",
            "priority": "high",
        },
        "general": {
            "message": "**General care tip:** Keeping a consistent routine for feeding, exercise, and rest helps pets feel safe and healthy.",
            "task":    "Add a 'Daily care routine' task with **medium** priority.",
            "priority": "medium",
        },
    }

    category = classify(text)

    # Display the appropriate response
    if category == "emergency":
        # Guardrail: high-visibility warning for dangerous situations
        st.warning(
            "🚨 **Emergency detected!**\n\n"
            "Your message contains keywords that may indicate a medical emergency. "
            "**Contact your veterinarian or an emergency animal clinic immediately.**\n\n"
            "You can also call the ASPCA Animal Poison Control Center: **1-888-426-4435**"
        )
    else:
        info = SUGGESTIONS[category]
        st.info(
            f"**Category detected:** `{category.capitalize()}`\n\n"
            f"{info['message']}\n\n"
            f"💡 **Suggested task:** {info['task']}"
        )
        st.success(f"Recommended priority level: **{info['priority'].upper()}**")