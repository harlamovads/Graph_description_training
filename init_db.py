# init_db.py
import os
import sys
import json
from datetime import datetime
from werkzeug.security import generate_password_hash
from app import create_app
from backend.models import db
from backend.models.user import User, Invitation
from backend.models.task import Task, TaskAssignment
from backend.models.sentence import Sentence
from backend.models.exercise import Exercise
from backend.models.submission import Submission  # Make sure this import is correct
from create_placeholders import create_sample_placeholders
from sqlalchemy import text
import json
import os

def load_sentence_database_to_flask():
    """Load sentence database for Flask application"""
    from backend.models.sentence import Sentence
    from backend.models import db
    jsonl_file = 'sentencewise_full.jsonl'
    if not os.path.exists(jsonl_file):
        print(f"Warning: {jsonl_file} not found. Exercise generation will be limited.")
        return
    
    print("Loading sentence database...")
    
    try:
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            loaded_count = 0
            for line_num, line in enumerate(f, 1):
                try:
                    line = line.strip()
                    if not line:
                        continue
                        
                    data = json.loads(line)
                    text = data.get('text', '')
                    tags = data.get('tags', [])
                    
                    if not text or not tags:
                        continue
                    
                    # Create sentence object
                    sentence = Sentence(text=text)
                    sentence.set_error_tags(tags)
                    
                    db.session.add(sentence)
                    loaded_count += 1
                    
                    if line_num % 1000 == 0:
                        db.session.commit()
                        print(f"Loaded {loaded_count} sentences...")
                        
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    print(f"Error processing line {line_num}: {e}")
                    continue
        
        db.session.commit()
        print(f"Successfully loaded {loaded_count} sentences to database")
        
    except Exception as e:
        print(f"Error loading sentence database: {e}")


def init_database():
    """Initialize database with sample data"""
    app = create_app()
    
    # Create uploads directory if it doesn't exist
    uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)
    create_sample_placeholders()
    
    with app.app_context():
        # Drop all tables with CASCADE option to handle dependencies
        # This will forcefully drop all tables regardless of foreign key constraints
        db.session.execute(text("DROP SCHEMA public CASCADE"))
        db.session.execute(text("CREATE SCHEMA public"))
        db.session.execute(text("GRANT ALL ON SCHEMA public TO app_user"))
        db.session.execute(text("GRANT ALL ON SCHEMA public TO public"))
        db.session.commit()
        
        # Create all tables
        db.create_all()
        
        print("Creating sample users...")
        # Create sample users
        teacher = User(
            username="teacher1",
            email="teacher@example.com",
            password_hash=generate_password_hash("password123"),
            role="teacher"
        )
        
        student1 = User(
            username="student1",
            email="student1@example.com",
            password_hash=generate_password_hash("password123"),
            role="student"
        )
        
        student2 = User(
            username="student2",
            email="student2@example.com",
            password_hash=generate_password_hash("password123"),
            role="student"
        )
        
        db.session.add_all([teacher, student1, student2])
        db.session.commit()
        
        print("Creating sample tasks...")
        # Create sample tasks with image URLs
        task1 = Task(
            title="The bar chart shows the global sales of digital games",
            description="The bar chart shows the global sales (in billions of dollars) of different types of digital games between 2000 and 2006.",
            image_url="/uploads/digital_games_chart.png",  # Placeholder filename
            creator_id=teacher.id
        )
        
        task2 = Task(
            title="Poverty in Australia",
            description="The table below shows the proportion of different categories of families living in poverty in Australia in 1999.",
            image_url="/uploads/poverty_australia_table.png",  # Placeholder filename
            creator_id=teacher.id
        )
        
        task3 = Task(
            title="UK commuters graph",
            description="The graph below shows the average number of UK commuters travelling each day by car, bus or train between 1970 and 2030.",
            image_url="/uploads/uk_commuters_graph.png",  # Placeholder filename
            creator_id=teacher.id
        )
        
        db.session.add_all([task1, task2, task3])
        db.session.commit()
        
        print("Creating sample task assignments...")
        # Create sample task assignments
        assignment1 = TaskAssignment(
            task_id=task1.id,
            student_id=student1.id,
            due_date=datetime(2025, 5, 30)
        )
        
        assignment2 = TaskAssignment(
            task_id=task2.id,
            student_id=student2.id,
            due_date=datetime(2025, 6, 15)
        )
        
        assignment3 = TaskAssignment(
            task_id=task3.id,
            student_id=student1.id,
            due_date=datetime(2025, 6, 20)
        )
        
        db.session.add_all([assignment1, assignment2, assignment3])
        db.session.commit()
        
        print("Creating sample sentences...")
        # Add sentences from the provided JSON-like data
        sentence_data = [
            {
                "text": "The chart illustrates the number in percents of overweight children in Canada throughout a 20-years period from 1985 to 2005, while the table demonstrates the percentage of children doing sport exercises regulary over the period from 1990 to 2005.",
                "tags": [
                    {
                        "error_span": "sport",
                        "correction": "sports",
                        "span_start": "188",
                        "span_end": "193",
                        "native_tag": "Noun_number",
                        "first_level_tag": "M",
                        "second_level_tag": "FORM"
                    },
                    {
                        "error_span": "regulary",
                        "correction": "regularly",
                        "span_start": "204",
                        "span_end": "212",
                        "native_tag": "Spelling",
                        "first_level_tag": "R",
                        "second_level_tag": "SPELL"
                    }
                ]
            },
            {
                "text": "According to the graph, boys are more likely to have extra weight in period of 2000-2005, a quater of them had problems with weight in 2005.",
                "tags": [
                    {
                        "error_span": "period",
                        "correction": "the period",
                        "span_start": "69",
                        "span_end": "75",
                        "native_tag": "Articles",
                        "first_level_tag": "M",
                        "second_level_tag": "DET"
                    },
                    {
                        "error_span": "quater",
                        "correction": "quarter",
                        "span_start": "92",
                        "span_end": "98",
                        "native_tag": "Spelling",
                        "first_level_tag": "R",
                        "second_level_tag": "SPELL"
                    }
                ]
            },
            # ... [remaining sentence data unchanged] ...
        ]
        
        # Add the sentences to the database
        for sentence_item in sentence_data:
            sentence = Sentence(
                text=sentence_item["text"]
            )
            sentence.set_error_tags(sentence_item["tags"])
            db.session.add(sentence)
        
        # Add some additional sentences with common grammar errors
        additional_sentences = [
            {
                "text": "She don't like coffee.",
                "tags": [
                    {
                        "error_span": "don't",
                        "correction": "doesn't",
                        "span_start": "4",
                        "span_end": "9",
                        "native_tag": "Verb_agreement",
                        "first_level_tag": "M",
                        "second_level_tag": "SVA"
                    }
                ]
            },
            # ... [remaining additional_sentences unchanged] ...
        ]
        
        for sentence_item in additional_sentences:
            sentence = Sentence(
                text=sentence_item["text"]
            )
            sentence.set_error_tags(sentence_item["tags"])
            db.session.add(sentence)
        
        db.session.commit()
        
        print("Creating sample exercises...")
        # Create a sample exercise with an image
        exercise = Exercise(
            # Removed submission_id as it no longer exists in the model
            creator_id=teacher.id,
            title="Chart Description Exercise",
            instructions="Describe the chart and correct the sentences",
            image_url="/uploads/sample_chart.png",  # Placeholder filename
        )
        
        # Sample sentences for the exercise
        sentences_data = [
            {
                "id": 1,
                "content": "The chart shows sales of digital games between 2000 and 2006."
            },
            {
                "id": 2,
                "content": "Mobile games sales increased most dramaticly of all categories."
            },
            {
                "id": 3,
                "content": "Online games revenue exceeded 7 bilion dollars in 2006."
            }
        ]
        
        exercise.set_sentences(sentences_data)
        db.session.add(exercise)
        db.session.commit()

        print("Creating sample submission with neural network analysis...")
        try:
            
            from backend.services.neural_network_service import HuggingFaceT5GEDInference, generate_html_output
            print('Trying to run model')
            try:
                model = HuggingFaceT5GEDInference()
                print('Model loaded successfully')
            except Exception as e:
                print(f"Error loading HuggingFaceT5GEDInference model: {str(e)}")
                raise
            # Create a sample submission
            sample_text = "The chart illustrates the number in percents of overweight children in Canada throughout a 20-years period from 1985 to 2005, while the table demonstrates the percentage of children doing sport exercises regulary over the period from 1990 to 2005."
        
            # Process the text with the neural network
            with app.app_context():
                model = HuggingFaceT5GEDInference()
                results = model.analyze_text(sample_text)
                html_output = generate_html_output(results)
            
                # Create the submission - now referencing the exercise
                submission = Submission(
                    assignment_id=assignment1.id,
                    student_id=student1.id,
                    exercise_id=exercise.id,  # Now referencing the exercise
                    content=sample_text,
                    status='submitted'
                )
            
                # Set the analysis result
                analysis_result = {
                    "results": results,
                    "html_output": html_output,
                    "total_errors": sum(len(result["error_spans"]) for result in results),
                    "sentences": []
                }
            
                for i, result in enumerate(results):
                    sentence_analysis = {
                        "id": i,
                        "content": result["original"],
                        "errors": []
                    }
                
                    for span in result["error_spans"]:
                        sentence_analysis["errors"].append({
                            "type": span["type"],
                            "start": -1,
                            "end": -1,
                            "original": span["text"],
                            "suggestion": ""
                        })
                
                    analysis_result["sentences"].append(sentence_analysis)

                submission.set_analysis_result(analysis_result)
                submission.analysis_html = html_output  # Make sure this field exists in your model
            
                db.session.add(submission)
                db.session.commit()
            
                print("Neural network sample submission created successfully!")
        except Exception as e:
            print(f"Could not create neural network sample submission: {str(e)}")
            print("Continuing without neural network sample...")
        load_sentence_database_to_flask()
        print("Database initialized successfully!")
if __name__ == "__main__":
    init_database()