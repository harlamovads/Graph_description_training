# Test preview version link available [here](https://huggingface.co/spaces/Zlovoblachko/lang_learn_app)

---
title: Language Learning App
emoji: 🎓
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
license: mit
app_port: 7860
---

# Language Learning Application

A comprehensive AI-powered language learning platform for teachers and students.

## Features

### For Students 👨‍🎓
- **Writing Submission**: Submit writing assignments with image prompts
- **Grammar Analysis**: Get detailed AI-powered grammar feedback
- **Exercise Practice**: Complete targeted grammar exercises
- **Progress Tracking**: View your improvement over time
- **Interactive Dashboard**: Track assignments and exercise scores

### For Teachers 👩‍🏫
- **Task Creation**: Create writing assignments with visual prompts
- **Student Management**: Invite students and manage classes
- **Submission Review**: Review and provide feedback on student work
- **Exercise Generation**: Create custom exercises from student errors
- **Analytics Dashboard**: Monitor student progress and performance

## Technology Stack

- **Frontend**: React.js with Material-UI
- **Backend**: Flask with RESTful APIs
- **Database**: PostgreSQL
- **AI Models**: 
  - T5-based grammar correction model
  - ELECTRA-based error detection
- **Authentication**: JWT-based secure login system

## AI-Powered Features

### Grammar Error Detection & Correction
- Advanced neural networks analyze student writing
- Identifies multiple error types (spelling, grammar, style)
- Provides contextual corrections and explanations
- Visual highlighting of errors in the interface

### Intelligent Exercise Generation
- Automatically creates practice exercises from student errors
- Finds similar sentences from error database
- Adaptive difficulty based on error patterns
- Immediate feedback and scoring

## How to Use

### Getting Started
1. **Register** as either a teacher or student
2. **Teachers**: Generate invitation codes for your students
3. **Students**: Use invitation codes or register independently

### Workflow for Teachers
1. Create writing tasks with visual prompts (charts, graphs, images)
2. Assign tasks to students
3. Review submissions with AI-generated error analysis
4. Create targeted exercises from common errors
5. Monitor student progress

### Workflow for Students
1. Complete assigned writing tasks
2. Review AI feedback on your submissions
3. Practice with generated exercises
4. Track your improvement over time

## Sample Tasks

The application comes with sample tasks including:
- Chart and graph description exercises
- Data analysis writing prompts
- Academic writing assignments
- Creative writing challenges

## Educational Benefits

- **Immediate Feedback**: Students get instant grammar analysis
- **Targeted Practice**: Exercises focus on individual error patterns
- **Progress Tracking**: Both teachers and students can monitor improvement
- **Scalable Learning**: Supports individual and classroom use
- **Evidence-Based**: Uses state-of-the-art NLP research

## Technical Details

- **Models**: Fine-tuned on academic writing datasets
- **Languages**: Optimized for English language learning
- **Privacy**: All data processed securely
- **Performance**: Optimized for real-time analysis
