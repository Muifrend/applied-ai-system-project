# Applied AI System Project: Final Submission Checklist

## 1. Functionality: What Your System Should Do
- [x] **Project does something useful with AI**: PawPal+ uses AI to act as a conversational pet-care scheduling assistant.
- [x] **Advanced AI Features**:
  - **Retrieval-Augmented Generation (RAG)**: The system searches through local markdown files containing pet-care guidelines before answering.
  - **Agentic Workflow**: The GPT-4o agent uses function calling to act autonomously (reading schedules, adding tasks, and flagging conflicts).
- [x] **Runs correctly and reproducibly**: Can be launched via `streamlit run app.py`.
- [x] **Includes logging or guardrails**: All agent tool invocations are logged with timestamps to `pawpal.log`.
- [x] **Clear setup steps**: Full setup and installation commands are detailed in `README.md`.

## 2. Design and Architecture
- [x] **System diagram**: Created and saved as `docs/class_diagram.md` (with UML architecture), showing the flow between the UI, Agent, Tools, and RAG Knowledge Base.

## 3. Documentation
- [x] **README Updates**:
  - The README explicitly names the original project and summarizes its goals.
  - Includes Title and summary of the new AI capabilities.
  - Architecture overview is documented.
  - Setup instructions (API keys, requirements) are provided.
  - Sample interactions are included.
  - Design decisions and testing summary.
  - Reflection section is present.

## 4. Reliability and Evaluation
- [x] **Automated tests**: 29 passing Pytest tests covering the agent tools, RAG logic, and legacy scheduler.
- [x] **Confidence scoring**: The AI evaluates its own "Actionability" (1-5 scale) to determine if a request is safe to automate or requires a human professional.
- [x] **Logging and error handling**: `pawpal.log` catches and tracks tool executions during agent interactions.
- [x] **Human evaluation & Testing Summary**: 29 out of 29 tests passed cleanly. During human evaluation, the AI performed well at routing routine scheduling tasks but initially struggled to show "low confidence" for medical emergencies until we updated the system prompt to explicitly define an actionability scale based strictly on the provided knowledge base.

## 5. Reflection and Ethics

**What are the limitations or biases in your system?**
The AI is limited by the strict boundaries of the markdown files provided in the `knowledge/` directory. If a pet breed has a very specific physiological anomaly not listed in the standard guidelines, the AI might give generic advice that doesn't perfectly fit. Additionally, it has an inherent bias toward "agreeableness" from its pre-training, which originally caused it to confidently attempt to answer medical questions rather than escalating them.

**Could your AI be misused, and how would you prevent that?**
Users might misuse the AI by relying on it as a substitute for a real veterinarian when their pet is severely ill. To prevent this, we implemented the `flag_conflict_or_gap` tool and the "Actionability Score" system, which forces the AI to output a score of "1" when dealing with medical symptoms, immediately signaling that the system is unauthorized to handle the request safely on its own.

**What surprised you while testing your AI's reliability?**
I was surprised by how difficult it was to force the AI to lower its "confidence" score for emergencies. Because GPT-4o is heavily pre-trained, it inherently "knew" that chocolate was toxic to dogs, so it gave itself a 5/5 confidence rating for that advice. I had to explicitly redesign the system prompt to score "System Actionability" instead, forcing it to grade its *authorization* rather than its *knowledge certainty*.

**Describe your collaboration with AI during this project. Identify one instance when the AI gave a helpful suggestion and one instance where its suggestion was flawed or incorrect.**
- **Helpful Suggestion**: The AI was extremely helpful in identifying the Streamlit + ChromaDB hot-reload bug. It quickly analyzed the `AttributeError: 'RustBindingsAPI'` error and correctly suggested wrapping the `KnowledgeBase` and `PawPalAgent` initializations in `@st.cache_resource` to prevent the database from crashing on multiple thread calls.
- **Flawed Suggestion**: When trying to input the correct API key into the Streamlit secret manager, I initially opted for .env not knowing that the AI pre-built the system for Streamlit secrets. And then I was trying to debug this using the AI but at some point I realized that the secrets was already built in so it's just easier to switch to that. And then the AI on first refractor got it working.
