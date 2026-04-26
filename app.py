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
# Stores age and gender per pet (Pet class only holds name and type)
if "pet_details" not in st.session_state:
    st.session_state.pet_details = {}

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

# --- Add a Pet Section ---
with st.expander("Add a Pet", expanded=not st.session_state.owner.pets):
    new_pet_name = st.text_input("Pet name", placeholder="e.g. Mochi")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        new_species = st.selectbox("Species", ["dog", "cat", "other"])
    with col_b:
        new_age = st.number_input("Age (years)", min_value=0, max_value=30, value=1)
    with col_c:
        new_gender = st.selectbox("Gender", ["female", "male", "unknown"])

    if st.button("Add pet"):
        name = new_pet_name.strip()
        if not name:
            st.warning("Enter a pet name!")
        elif any(p.name == name for p in st.session_state.owner.pets):
            st.warning(f"A pet named '{name}' is already added!")
        else:
            st.session_state.owner.add_pet(Pet(name, new_species))
            st.session_state.pet_details[name] = {"age": new_age, "gender": new_gender}
            st.success(f"Pet '{name}' added!")

# --- Your Pets Section ---
st.subheader("Your Pets")

if not st.session_state.owner.pets:
    st.info("No pets added yet. Open 'Add a Pet' above to get started.")
    selected_pet = None
else:
    pet_names = [p.name for p in st.session_state.owner.pets]
    selected_pet = st.selectbox("Select a pet", pet_names, key="selected_pet")

    # Show a one-line summary of the selected pet's details
    pet_obj = next(p for p in st.session_state.owner.pets if p.name == selected_pet)
    details = st.session_state.pet_details.get(selected_pet, {})
    st.caption(
        f"Species: {pet_obj.type} | "
        f"Age: {details.get('age', '?')} yr | "
        f"Gender: {details.get('gender', 'unknown')}"
    )

    # Show tasks belonging to the selected pet
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
                time_str = f"{task.get('hour', 12)}:{task.get('minute', 0):02d} {task.get('am_pm', 'AM')}"
                cost_str = f"${task.get('cost', 0.0):.2f}"
                st.markdown(
                    f"**{task['title']}** &nbsp;|&nbsp; "
                    f"Category: {task.get('category', 'general')} &nbsp;|&nbsp; "
                    f"Time: {time_str} &nbsp;|&nbsp; "
                    f"{task['duration_minutes']} min &nbsp;|&nbsp; "
                    f"Priority: **{task['priority']}** &nbsp;|&nbsp; "
                    f"Repeat: {task['repeat']} &nbsp;|&nbsp; "
                    f"Cost: {cost_str}"
                )
            with col_btn:
                if st.button("Remove", key=f"remove_{original_index}"):
                    st.session_state.tasks.pop(original_index)
                    st.rerun()

# --- Add a Task for Selected Pet Section ---
st.subheader("Add a Task for Selected Pet")

if not st.session_state.owner.pets:
    st.info("Add a pet above before creating tasks.")
elif selected_pet is None:
    st.info("Select a pet in 'Your Pets' above to add tasks.")
else:
    st.caption(f"Adding task to: **{selected_pet}**")

    col1, col2 = st.columns(2)
    with col1:
        task_title = st.text_input("Task name", placeholder="e.g. Morning walk")
    with col2:
        category = st.selectbox(
            "Category",
            ["feeding", "exercise", "grooming", "medication", "vet", "enrichment", "other"]
        )

    col3, col4, col5, col6 = st.columns(4)
    with col3:
        task_hour = st.number_input("Hour", min_value=1, max_value=12, value=8)
    with col4:
        task_minute = st.number_input("Minute", min_value=0, max_value=59, value=0, step=5)
    with col5:
        am_pm = st.selectbox("AM / PM", ["AM", "PM"])
    with col6:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

    col7, col8, col9 = st.columns(3)
    with col7:
        duration = st.number_input("Duration (min)", min_value=1, max_value=480, value=20)
    with col8:
        cost = st.number_input("Cost ($)", min_value=0.0, step=0.50, value=0.0)
    with col9:
        frequency = st.selectbox("Repeat", ["none", "daily", "weekly"])

    if st.button("Add task"):
        if not task_title.strip():
            st.warning("Enter a task name!")
        else:
            pet = next((p for p in st.session_state.owner.pets if p.name == selected_pet), None)
            if pet:
                # Convert 12-hour time to 24-hour for the Task datetime
                hour_24 = task_hour % 12 + (12 if am_pm == "PM" else 0)
                task_time = datetime.now().replace(
                    hour=hour_24, minute=task_minute, second=0, microsecond=0
                )
                task_obj = Task(
                    task_title.strip(),
                    task_time,
                    priority,
                    int(duration),
                    frequency=frequency if frequency != "none" else None,
                )
                st.session_state.owner.schedule_task(pet, task_obj)
                st.session_state.tasks.append({
                    "title":            task_title.strip(),
                    "category":         category,
                    "hour":             task_hour,
                    "minute":           task_minute,
                    "am_pm":            am_pm,
                    "duration_minutes": int(duration),
                    "priority":         priority,
                    "repeat":           frequency,
                    "cost":             float(cost),
                    "pet":              pet.name,
                })
                st.success(f"Task '{task_title.strip()}' added to {pet.name}!")

# --- Generate Daily Schedule Section ---
st.divider()
st.subheader("Generate Daily Schedule")
st.caption("Tasks sorted by priority, checked against available time and daily budget, with conflict detection.")

if st.button("Generate daily schedule"):
    if not st.session_state.tasks:
        st.warning("No tasks added yet. Add some tasks above first.")
    else:
        PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

        sorted_tasks = sorted(
            st.session_state.tasks,
            key=lambda t: PRIORITY_ORDER.get(t["priority"], 3)
        )

        # --- Time check ---
        total_minutes = sum(t["duration_minutes"] for t in sorted_tasks)
        available = st.session_state.get("available_minutes", 60)

        if total_minutes > available:
            st.warning(
                f"⏱ Total task time is **{total_minutes} min** but you only have "
                f"**{available} min/day** available. Consider removing or shortening some tasks."
            )
        else:
            st.success(
                f"⏱ Schedule fits! Total: **{total_minutes} min** of your **{available} min** available."
            )

        # --- Cost check ---
        total_cost = sum(t.get("cost", 0.0) for t in sorted_tasks)
        budget = st.session_state.get("daily_budget", 10.0)

        st.markdown(f"**Total estimated daily cost: ${total_cost:.2f}**")
        if total_cost > budget:
            st.warning(
                f"💰 Total cost **${total_cost:.2f}** exceeds your daily budget of **${budget:.2f}**."
            )
        else:
            st.success(
                f"💰 Total cost **${total_cost:.2f}** is within your daily budget of **${budget:.2f}**."
            )

        # --- Schedule table ---
        st.markdown("#### Today's Schedule (high priority first)")
        schedule_rows = []
        for task in sorted_tasks:
            time_str = f"{task.get('hour', 12)}:{task.get('minute', 0):02d} {task.get('am_pm', 'AM')}"
            schedule_rows.append({
                "Pet":            task["pet"],
                "Task":           task["title"],
                "Category":       task.get("category", "general"),
                "Time":           time_str,
                "Duration (min)": task["duration_minutes"],
                "Priority":       task["priority"],
                "Repeat":         task["repeat"],
                "Cost":           f"${task.get('cost', 0.0):.2f}",
            })
        st.table(schedule_rows)

        # --- Conflict detection ---
        scheduler = st.session_state.owner.scheduler
        any_conflict = False
        for pet in st.session_state.owner.pets:
            conflicts = scheduler.detect_conflicts(pet)
            if conflicts:
                any_conflict = True
                conflict_names = ", ".join(t.title for t in conflicts)
                st.warning(f"⚠ Conflict detected for **{pet.name}**: {conflict_names}")
        if not any_conflict and st.session_state.owner.pets:
            st.success("No scheduling conflicts detected.")

        # --- Recurring task queuing ---
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
                        frequency=task.frequency,
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