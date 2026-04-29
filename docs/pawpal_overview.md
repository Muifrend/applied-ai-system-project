# PawPal+ App Overview

## 🐾 Introduction
**PawPal+** is a Streamlit-based web application designed to help pet owners seamlessly manage and track care tasks for their pets. From daily walks and feeding times to recurring medication and vet reminders, PawPal+ serves as an intelligent scheduling assistant for single and multi-pet households.

## 🏗️ Core Architecture & Entities
The application is built on a clean object-oriented Python backend (`pawpal_system.py`) connected to a reactive Streamlit frontend (`app.py`).

The core data models include:
1. **Owner**: Represents the user(s) managing the pets. An owner can manage multiple pets.
2. **Pet**: Represents the animal being cared for (e.g., dog, cat, bird). Contains basic details (name, species, age) and holds a list of tasks.
3. **Task**: Represents a single pet care activity. Contains:
   - `description` (e.g., "Morning Walk")
   - `time` (HH:MM format)
   - `due_date` (Date)
   - `frequency` (Daily, Weekly, Monthly, As Needed)
   - `is_completed` (Boolean status)
4. **Scheduler**: The core logic engine that manages retrieving, sorting, filtering, completing, and conflict-checking tasks across an owner's pets.

## ✨ Key Features & Functionality

### 1. Unified Dashboard
- **Owner Filtering**: Users can view the schedule for the entire household ("All" view) or filter tasks down to a specific owner.
- **Top-Level Metrics**: Quick statistics showing the number of Owners Managed, Pets Managed, and total Pending Tasks.

### 2. Intelligent Scheduling & Sorting
- **Chronological Ordering**: The scheduler automatically sorts tasks deterministically based on:
  1. Completion Status (Pending tasks first)
  2. Due Date
  3. Frequency Rank (Daily > Weekly > Monthly > As Needed)
  4. Time of Day (HH:MM)
- **Safe Fallbacks**: Invalid time strings won't crash the app; they are safely pushed to the end of the schedule.

### 3. Smart Recurrence Engine
- **Auto-Generation**: When a user marks a recurring task as complete, the app automatically calculates the next due date and schedules the next occurrence.
  - `Daily` -> +1 Day
  - `Weekly` -> +7 Days
  - `Monthly` -> +30 Days

### 4. Conflict Detection
- **Time Slot Warnings**: If an owner accidentally schedules two tasks for the exact same date and time (e.g., feeding the dog and the cat at exactly 08:00 on the same day), the system detects this slot conflict and displays a prominent warning on the dashboard.

### 5. Quick Actions (Sidebar)
Users can rapidly manage their household via sidebar forms:
- **Add Owner**: Register a new person.
- **Add Pet**: Assign a new pet to an existing owner.
- **Schedule Task**: Assign a new task to a specific pet, including selecting the exact time, frequency, and date.

## 🛠️ Technical Stack
- **Frontend / UI**: [Streamlit](https://streamlit.io/) (Provides reactive UI, session state management, and layout).
- **Backend / Logic**: Pure Python 3 using `dataclasses`.
- **Testing**: `pytest` for validating core scheduler behaviors (sorting, recurrence, conflicts).

## 🚀 How It Works (User Flow)
1. The app initializes with some dummy data (Jordan, Alex, and their pets) stored in Streamlit's `session_state`.
2. The user views the main dashboard to see upcoming tasks ordered sequentially.
3. The user can click "Done" on a task. The `Scheduler` engine marks that specific instance complete and immediately provisions the next instance if it is a recurring task.
4. The screen reruns, immediately updating metrics and removing the completed task (unless "Show completed tasks" is toggled on).
