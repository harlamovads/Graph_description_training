# init_db.py
"""Idempotent sample-data seeding.

This used to unconditionally DROP SCHEMA public CASCADE and rebuild everything from scratch on
every run - and docker/start.sh ran it on every container start, which meant every restart
silently wiped the database (including Alembic's own version table). Schema creation/changes
are now Alembic's job (see database/migrations/, `flask db upgrade`, run before this script in
docker/start.sh). This script only seeds a small sample teacher/students/tasks, and only if the
database is empty - safe to run against a database that already has real data.
"""
import os
from datetime import datetime
from werkzeug.security import generate_password_hash
from app import create_app
from backend.models import db
from backend.models.user import User
from backend.models.task import Task, TaskAssignment
from create_placeholders import create_sample_placeholders


def seed_sample_data():
    app = create_app()

    uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)
    create_sample_placeholders()

    with app.app_context():
        if User.query.count() > 0:
            print("Database already has data - skipping sample seed.")
            return

        print("Database is empty - creating sample users, tasks, and assignments...")

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

        task1 = Task(
            title="The bar chart shows the global sales of digital games",
            description="The bar chart shows the global sales (in billions of dollars) of different types of digital games between 2000 and 2006.",
            image_url="/uploads/digital_games_chart.png",
            creator_id=teacher.id
        )
        task2 = Task(
            title="Poverty in Australia",
            description="The table below shows the proportion of different categories of families living in poverty in Australia in 1999.",
            image_url="/uploads/poverty_australia_table.png",
            creator_id=teacher.id
        )
        task3 = Task(
            title="UK commuters graph",
            description="The graph below shows the average number of UK commuters travelling each day by car, bus or train between 1970 and 2030.",
            image_url="/uploads/uk_commuters_graph.png",
            creator_id=teacher.id
        )
        db.session.add_all([task1, task2, task3])
        db.session.commit()

        db.session.add_all([
            TaskAssignment(task_id=task1.id, student_id=student1.id, due_date=datetime(2025, 5, 30)),
            TaskAssignment(task_id=task2.id, student_id=student2.id, due_date=datetime(2025, 6, 15)),
            TaskAssignment(task_id=task3.id, student_id=student1.id, due_date=datetime(2025, 6, 20)),
        ])
        db.session.commit()

        print("Sample data created successfully!")


if __name__ == "__main__":
    seed_sample_data()
