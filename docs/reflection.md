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

It considers time and orders the view based on which is the upcoming one and has a recurring feature. And also you can view the pets based on the owner. And it identifies collisions in schedule.
I just put myself in the position of the person and imagined what matters most and decided through this process that they should just see the most urgent tasks. Additionally, this was further entrenched by the class structure for which you had to determine the time and date of the task before so that it wasn't in the schedulers role.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

So some calendar events will overlap and not be flagged since they will only be flagged when they are happening at exactly the same time. This helps with simplifying the logic and also is not that big of a drawback when the purpose is to help with scheduling and not optimize on this facet.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

Copilot helped me with brainstorming the classes and implementing the tests and working with the ai, however, I found it bad in refractoring and debugging which is when I switched to Codex for it to quickly pass over the codebase and fix.
For copilot the best prompts where usually the ones that summarized information and did the small refractors like adding the docstrings. When working with more files it degraded drastically. 

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

As I stated earlied, I cut two redundant classes (ScheduleItem, Scheduler switched for Schedule) and simplified the rest because it added fields like a method explain to a task which didn't make sense to me, since there was already a description.
The way that I determined if the classes were redundant is I thought about the functions of each class and evaluated whether this could be adopted without implementing them and so I cut.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

First the pytest to see if the backend logic worked, but when I went to debugging the frontend I also that the UI that the copilot version made drifted far from the original base code so I inputted that and made it go back to that design and then I went to debugging through using the app which was tedious with copilot so I switched to Codex.
The frontend debugging was important so that the app was actually usable. The draft that copilot came up with was far from a product that a person would want to use so I had to intervene.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

I'm confident that majority of the core functionality works and that there are some small bugs here and there. 
I would test more from a product design perspective and see whether the features make sense, but for that I would need more knowledge on the consumer.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

The progression from the copilot draft into the one that reverted back to the original layout. I made sure that the app didn't drift from the original idea.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

I would think about a different user flow, therefore, redesigning classes and possibly focusing on priority instead of urgency.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

The way you scaffold the backend has product implications and will guide the future design of the project so thinking through the first steps thoroughly is extremely important.
