# Socratica

> AI-powered teaching assistant built with **Langflow** and **Retrieval-Augmented Generation (RAG)** to help students learn from course materials.
> 
> 

## Overview

**Socratica** is an AI-powered learning assistant designed to support students outside regular class hours.

The system uses course materials such as **syllabi, lecture slides, PDF modules, and assessment rubrics** as its knowledge base. Students can ask questions and receive context-aware answers grounded in the provided course materials rather than relying solely on general knowledge.

The goal is to provide a **24/7 digital teaching assistant** that helps students understand course concepts, review learning materials, and practice their knowledge.

---

## Problem

Lecturers and Teaching Assistants often receive repetitive questions from students about:

* Course materials


* Syllabus information


* Assignment instructions


* Difficult concepts
* Learning exercises



Handling these questions manually can consume significant time, especially outside lecture hours, and can result in delayed responses.

**Socratica** addresses this problem by providing an AI assistant that can retrieve relevant information from official course materials and respond to students in real time.

---

## Core Features

### 📚 Course Knowledge Base

Upload course materials such as:

* PDF


* DOCX


* PPTX


* Syllabus


* Lecture slides


* Course modules


* Assessment rubrics



The documents are processed and stored as searchable knowledge for the AI agent.

### 💬 Context-Aware Q&A

Students can ask questions about the course and receive answers based on the available knowledge base.

The system is designed to:

* Retrieve relevant course information


* Generate context-aware answers


* Provide source citations


* Reject questions outside the course scope



Example:

> **Question:** What is inheritance in Object-Oriented Programming?
> **Answer:** Inheritance is a mechanism that allows a class to derive properties and behavior from another class.
> **Source:** Object-Oriented Programming — Lecture 3, Page 12
> 
> 

The original PRD requires answers to include references to their source material.

### 🧠 Socratic Learning Mode

For problem-solving and assignment-related questions, **Socratica** can guide students through the reasoning process instead of immediately providing the final answer.

The goal is to encourage students to understand the problem and develop their own solution.

### 📝 Assignment Feedback

Students can submit a draft assignment or code for preliminary feedback.

The AI can provide feedback based on criteria such as:

* Structure


* Topic relevance


* Code syntax


* General quality

The system does **not** provide an official numerical grade.

### 👨‍🏫 Human Escalation

When the AI has low confidence or a student is not satisfied with the response, the question can be escalated to a Lecturer or Teaching Assistant for review.

---

## MVP Scope

For the initial version, the project focuses on the core learning workflow:

```text
Student
   │
   ▼
Chat Interface
   │
   ▼
Langflow
   │
   ▼
RAG Pipeline
   │
   ▼
Course Knowledge Base
   │
   ▼
LLM
   │
   ▼
Answer + Source

```

### MVP Features

* [x] Course document ingestion


* [x] RAG-based question answering


* [x] Context-aware responses


* [x] Source citation


* [x] Out-of-scope handling


* [ ] Socratic Mode


* [ ] Assignment feedback


* [ ] Lecturer escalation dashboard



---

## Architecture

The system uses **Langflow** as the visual orchestration layer for the AI workflow.

```text
┌──────────────────────────┐
│      Student / User      │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│      Web Interface       │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│         Langflow         │
│    AI Workflow Layer     │
└────────────┬─────────────┘
             │
       ┌─────┴─────┐
       ▼           ▼
┌────────────┐ ┌──────────────┐
│ RAG        │ │ Guardrails   │
│ Pipeline   │ │ & Router     │
└─────┬──────┘ └──────┬───────┘
      │               │
      ▼               ▼
┌────────────┐   ┌────────────┐
│ Vector DB  │   │    LLM     │
└────────────┘   └─────┬──────┘
                       │
                       ▼
                ┌────────────┐
                │ Answer +   │
                │ Citation   │
                └────────────┘

```

The broader PRD architecture also defines a guardrail/router layer, vector database, LLM engine, and escalation log/database.

---

## RAG Workflow

The knowledge retrieval process follows this general pipeline:

```text
Course Documents
      │
      ▼
Document Extraction
      │
      ▼
Text Chunking
      │
      ▼
Metadata
(Bab / Page / Meeting)
      │
      ▼
Embeddings
      │
      ▼
Vector Database
      │
      ▼
Semantic Search
      │
      ▼
Relevant Context
      │
      ▼
LLM
      │
      ▼
Grounded Answer

```

Document chunks can contain metadata such as chapter, page number, and lecture/meeting number to improve retrieval and source attribution.

---

## Technology Stack

| Layer | Technology |
| --- | --- |
| AI Orchestration | Langflow |
| AI Architecture | RAG

 |
| LLM | IBM Granite / compatible LLM

 |
| Vector Database | PostgreSQL + pgvector / Qdrant

 |
| Backend | FastAPI

 |
| Frontend | Web-based UI

 |
| Documents | PDF / DOCX / PPTX

 |

The original PRD specifies a stack involving an API/orchestration layer, guardrails, vector database, LLM engine, and escalation database.

---

## Example Use Case

### Student asks:

> "Apa perbedaan inheritance dan composition?"

### Socratica workflow:

```text
Question
   ↓
Langflow
   ↓
Retrieve relevant course materials
   ↓
Check scope
   ↓
Generate grounded response
   ↓
Attach source

```

### Expected response:

> **Inheritance** memungkinkan sebuah class mewarisi atribut dan behavior dari class lain, sedangkan **composition** membangun sebuah object menggunakan object lain sebagai bagian dari komponennya.
> **Source:** Lecture 04 — Object-Oriented Programming, Page 15

---

## Guardrails

**Socratica** is designed to prioritize grounded answers from the course knowledge base.

The system should:

* Avoid unsupported answers


* Reject out-of-scope questions


* Protect against prompt injection


* Keep responses grounded in retrieved course materials


* Provide source references



Prompt injection is explicitly identified as a security concern in the project requirements.

---

## Performance & Quality Targets

The PRD defines the following target metrics:

| Metric | Target |
| --- | --- |
| RAG Faithfulness | > 90%

 |
| First Token Latency | < 2 seconds

 |
| Total Response | < 5 seconds

 |
| Prompt Injection Protection | Required

 |
| Data Encryption | Required

 |

These targets are part of the project's non-functional requirements.

---

## Project Goals

**Socratica** aims to:

1. Reduce repetitive questions handled manually by lecturers and TAs.


2. Provide students with 24/7 access to course assistance.


3. Help students understand concepts rather than simply provide answers.


4. Keep AI responses grounded in official course materials.


5. Create a safe workflow for escalating uncertain questions to human educators.



---

## Future Development

Potential future improvements include:

* Lecturer / TA dashboard


* Question analytics


* More advanced Socratic Mode


* Assignment feedback automation


* Multi-course support
* Improved document management
* More detailed evaluation and monitoring

These features can be developed progressively without changing the core RAG architecture.

---

## Current Scope

### In Scope

* Course material ingestion


* RAG-based Q&A


* Context-aware responses


* Source citation


* Basic guardrails


* Langflow-based AI workflow



### Out of Scope — V1

* Automatic final grading connected directly to an LMS


* Voice interaction



These limitations follow the project's original V1 scope.

---

## License

This project is developed for educational and hackathon purposes.
