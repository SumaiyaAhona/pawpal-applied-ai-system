# Model Card — PawPal+ Intelligent Pet Care Assistant

---

## 1. Project Title

**PawPal+ Intelligent Pet Care Assistant**
Rule-based natural language classification system for pet-care task management and emergency triage.

---

## 2. System Overview

PawPal+ is a Streamlit application that helps pet owners manage daily care tasks, generate priority-sorted schedules, and ask free-text pet-care questions through a built-in assistant. The assistant component uses a rule-based classifier — no external APIs, no machine learning models, no internet connection required — to interpret user input and return a targeted response.

The system is designed to be transparent and predictable: every decision the classifier makes can be traced directly to a keyword match and a response dictionary. This makes it easier to audit, explain, and improve than a black-box model.

---

## 3. Intended Use

**Primary users:** Pet owners who want a lightweight daily care planning tool with a conversational help layer.

**Intended contexts:**
- Planning and tracking recurring pet-care tasks (feeding, grooming, exercise, vet appointments)
- Generating a daily schedule constrained by available time
- Asking quick care questions in plain language
- Getting an immediate safety warning when describing a potential pet emergency

**Not intended for:**
- Replacing professional veterinary diagnosis or treatment
- Managing medical conditions or prescriptions
- Use with species other than dogs and cats (current suggestions are calibrated for these two)

---

## 4. AI Approach / How the Model Works

The assistant is a **rule-based keyword classifier** implemented in plain Python. It does not use a trained machine learning model, a neural network, or any external API.

**Classification pipeline:**

1. The user's input is converted to lowercase.
2. The classifier checks the input against six ordered keyword lists. The first list that produces a match determines the category.
3. A response dictionary maps each category to a care tip and a suggested task.
4. The UI renders the response using `st.warning` (emergency), `st.info` + `st.success` (all other categories).

**Category priority order (highest to lowest):**

| Priority | Category | Example trigger words |
|---|---|---|
| 1 | `emergency` | chocolate, poison, seizure, bleeding, trouble breathing, collapsed |
| 2 | `feeding` | feed, food, eat, diet, meal, treats, water |
| 3 | `grooming` | groom, bath, brush, nails, fur, shampoo |
| 4 | `exercise` | walk, run, play, active, energy, fetch |
| 5 | `scheduling` | schedule, appointment, checkup, vaccine, how often |
| 6 | `general` | *(catch-all for anything that does not match above)* |

Emergency is always checked first. This ordering guarantees that no care tip is shown instead of a safety warning, regardless of what else appears in the input.

**Response example for `feeding`:**
> Most adult dogs and cats do well with 2 meals per day at consistent times. Make sure fresh water is always available.
> Suggested task: Add a 'Morning feeding' and 'Evening feeding' task with medium priority.

---

## 5. Reliability and Evaluation

### Automated testing

The core scheduling logic (`pawpal_system.py`) is covered by a `pytest` suite in `tests/`. Tests verify:

- Tasks are returned in correct time order by `sort_by_time()`
- Conflict detection flags overlapping tasks and returns correct `(task_a, task_b)` pairs
- Recurring tasks generate correct next-occurrence dates for both daily and weekly frequencies
- Edge cases — empty pet lists, unregistered pets — return `[]` without raising exceptions

The classifier itself is not covered by automated tests; it was evaluated manually (see below).

### Manual testing

The assistant was tested by running 20+ varied inputs across all six categories, including:

- Exact keyword matches ("my dog won't eat")
- Partial matches ("he hasn't touched his food bowl")
- Multi-keyword inputs ("should I walk my dog before feeding him?")
- Emergency inputs with additional context ("my cat had a seizure but seems okay now")
- Inputs with no obvious category ("what should I do today?")

### Example results

| Input | Expected category | Actual category | Correct? |
|---|---|---|---|
| "my dog ate chocolate" | emergency | emergency | Yes |
| "how often should I brush my cat?" | grooming | grooming | Yes |
| "she seems tired and low energy" | exercise | exercise | Yes |
| "is it time for a vet visit?" | scheduling | scheduling | Yes |
| "my cat had a seizure but seems fine now" | emergency | emergency | Yes |
| "she doesn't seem like herself" | general | general | Yes |
| "should I give her water before a walk?" | feeding | feeding | Partial — exercise intent missed |

### What improved reliability

- Placing the emergency check **first** in the classifier prevented any scenario where a dangerous input was rerouted to a general care tip.
- Expanding the emergency keyword list beyond obvious terms (e.g., adding "collapsed", "swallowed", "vomiting blood") reduced the chance of a missed critical input.
- Using `str.lower()` before matching eliminated case sensitivity as a failure mode.

---

## 6. Limitations and Biases

**Keyword brittleness**
The classifier only recognizes inputs that contain one of its predefined keywords. A user who writes "he refuses to eat anything" will not match the feeding category because "refuses" and "anything" are not in the keyword list. The fallback to `general` means they still get a response, but not the most relevant one.

**Single-category output**
The classifier returns the first matching category and stops. An input like "should I feed my dog before our walk?" contains both feeding and exercise keywords, but only feeding is returned. Nuanced multi-topic questions are flattened.

**Species and breed assumptions**
Care tips reference dogs and cats generically. Advice about brushing frequency or exercise needs does not account for breed differences (a Husky has very different exercise requirements than a Chihuahua). Users with exotic pets or specific breeds may receive inaccurate recommendations.

**No memory between inputs**
Each question is classified independently. The assistant has no session memory, so follow-up questions like "what about for kittens?" receive a general response with no awareness of the prior exchange.

**English only**
All keyword matching is done against English terms. Non-English input will fall through to the `general` category.

---

## 7. Misuse Risks and Prevention

**Risk: User treats the assistant as a substitute for veterinary care**
A user who receives a care tip for a feeding question might delay contacting a vet for what is actually a medical problem. The emergency guardrail addresses the most obvious cases, but subtle symptoms (lethargy, weight loss, behavioral changes) are not in the keyword list.

**Mitigation:** The assistant's responses are framed as tips and suggestions, not diagnoses. The emergency warning explicitly directs the user to a professional and provides the ASPCA Poison Control number.

**Risk: False sense of safety from a passed emergency check**
If a user describes a genuine emergency using words not in the keyword list, the classifier returns a routine care tip. This is the most serious failure mode of a rule-based system.

**Mitigation:** The emergency keyword list was designed conservatively — it errs toward triggering the warning on ambiguous inputs (e.g., "blood") rather than requiring a precise phrase. Future versions should expand this list and consider adding a disclaimer to all responses.

**Risk: Unhelpful general responses discouraging continued use**
If too many inputs fall to the `general` catch-all, users may lose confidence in the assistant.

**Mitigation:** The general response was written to still be actionable ("Keeping a consistent routine for feeding, exercise, and rest helps pets feel safe and healthy") rather than a generic error message.

---

## 8. What Surprised Me During Testing

Two things were surprising during manual testing.

First, the emergency classifier was more robust than expected for compound inputs. "My dog ate chocolate and is now shaking" triggered `emergency` correctly because "chocolate" appears early in the string and is checked first — even though "shaking" is not in any keyword list. The priority ordering did its job without any extra logic.

Second, the `general` catch-all fired more often than anticipated for reasonable questions. Inputs like "my dog seems bored" or "is my cat sleeping too much?" produced general responses when a more specific category (exercise or scheduling) might have been more helpful. This revealed that the keyword lists need to be broader, not just longer — covering symptoms and observations in addition to direct activity names.

---

## 9. Collaboration with AI During Development

AI assistance (Claude) was used during development for code structure, UI copy, and debugging.

**One helpful suggestion**

When building the emergency classifier, the AI suggested placing the emergency keyword check as the *first branch* of the classifier rather than adding it as a special case at the end. This structural advice — check the most critical category first, always — made the safety logic simpler and more reliable. It also made the code easier to explain: "we always check for emergencies before anything else."

**One flawed or incorrect suggestion**

Early in development, the AI suggested using `st.experimental_rerun()` to refresh the page after removing a task. This function was deprecated in newer versions of Streamlit. Using it caused a warning in the console and would have broken the app in future Streamlit upgrades. The correct replacement, `st.rerun()`, was found by checking the Streamlit documentation directly. This was a good reminder that AI-generated code should always be verified against current library documentation — especially for rapidly evolving frameworks.

---

## 10. Ethical Reflection

The most significant ethical responsibility in this project is the emergency guardrail. A pet care app that fails to flag a poisoning or seizure — and instead returns a grooming tip — could contribute to a pet's death. That is not a hypothetical risk; it is a realistic failure mode of a keyword classifier.

Designing the emergency check to be conservative (flagging "blood" even without additional context) reflects a deliberate choice: the cost of a false positive (a user sees an unnecessary warning) is far lower than the cost of a false negative (a user misses a real emergency). When the stakes of a wrong answer are asymmetric, the system should be asymmetrically cautious.

More broadly, this project demonstrates that rule-based systems are not inherently less ethical than machine learning models. A well-designed rule-based classifier can be more transparent, more auditable, and more predictable than a model whose decision boundaries cannot be directly inspected. Choosing the simpler approach was a deliberate engineering decision, not a limitation to apologize for.

---

## 11. Future Improvements

- **Expand the emergency keyword list** using published lists of common household pet toxins (ASPCA, AVMA) to reduce the risk of missed emergencies.
- **Add multi-category detection** so an input can match more than one category and return a combined response.
- **Integrate an LLM** (e.g., Claude API) as an optional backend for users who want richer, more context-aware responses while keeping the rule-based system as a reliable fallback.
- **Add a disclaimer to all responses** reminding users that the assistant provides general guidance only and is not a substitute for veterinary advice.
- **Automated tests for the classifier** covering edge cases, multi-keyword inputs, and regression checks after any keyword list change.
- **Breed and species awareness** so care tips account for known differences in exercise, grooming, and dietary needs.

---

## 12. Final Statement

PawPal+ demonstrates that a rule-based AI system, when designed carefully and tested honestly, can be both useful and responsible. The classifier does not learn, generalize, or surprise — and for this application, that predictability is a feature, not a weakness.

The most important design decision in this project was not a technical one: it was the choice to treat the emergency guardrail as a safety requirement rather than a stretch goal. Every other feature in the app is optional. The guardrail is not.

This project is a realistic starting point for a production pet care assistant. Its limitations are documented, its failure modes are understood, and the path to improving it is clear.

---

*PawPal+ — CodePath Final Project | Rule-based AI System*
