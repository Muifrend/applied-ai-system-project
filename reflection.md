# PawPal+ Project Reflection

## 1. System Design

The user should be able to:
- Enter basic owner and pet information.
- Add and edit pet care tasks, including at least duration and priority.
- Generate and view a daily care plan based on constraints and priorities.

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

I started off with Task Pet and Schedule class.
Task
- name
- description
- date
Pet 
- name
- animal
- age
- method is_sick
I wasn't sure about Schedules feauters. The responsibilities where divided into what is the pet in Pet and what the task is and the date in Task. I was thinking whether Schedule was supposed to aggregate the tasks. I hadn't thought about the Owner class.


**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

I consulted with Copilot on my initial design and gave it the readme, it updated the classes and added a Owner class, however, I had to cut two redundant ones (ScheduleItem, Scheduler) and simplify the rest because it added fields like a method explain to a task which didn't make sense to me, since there was already a description.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
