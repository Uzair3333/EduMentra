"""Business logic for EduMentra.

Provides data access functions for:
- Subject management (add, retrieve, delete)
- Topic management (add, retrieve, delete, track progress)
- Task management (add, retrieve, mark complete, delete)
- Quiz functionality (save results, track progress)
- Notes management (retrieve and associate with topics)
"""

from backend.db import connect_db


# --- SUBJECT FUNCTIONS ---
def add_subject(name: str) -> None:
    """Add a new subject to the database.
    
    Args:
        name: The name of the subject to add
    """
    try:
        conn, cursor = connect_db()
        cursor.execute("INSERT INTO subjects (name) VALUES (?)", (name,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error adding subject: {e}")


def get_subjects() -> list:
    """Retrieve all subjects from the database.
    
    Returns:
        List of tuples containing (id, name, created_at) for each subject
    """
    try:
        conn, cursor = connect_db()
        cursor.execute("SELECT id, name FROM subjects")
        subjects = cursor.fetchall()
        conn.close()
        return subjects
    except Exception as e:
        print(f"Error retrieving subjects: {e}")
        return []


def delete_subject(subject_id: int) -> None:
    """Delete a subject and all associated topics.
    
    Args:
        subject_id: The ID of the subject to delete
    """
    try:
        conn, cursor = connect_db()
        cursor.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error deleting subject: {e}")


# --- TOPIC FUNCTIONS ---
def add_topic(subject_id: int, name: str) -> None:
    """Add a new topic to a subject.
    
    Args:
        subject_id: The ID of the parent subject
        name: The name of the topic
    """
    try:
        conn, cursor = connect_db()
        cursor.execute(
            "INSERT INTO topics (subject_id, name, progress) VALUES (?, ?, 0)",
            (subject_id, name),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error adding topic: {e}")


def get_topics(subject_id: int) -> list:
    """Retrieve all topics for a given subject.
    
    Args:
        subject_id: The ID of the subject
        
    Returns:
        List of tuples containing (id, subject_id, name, progress) for each topic
    """
    try:
        conn, cursor = connect_db()
        cursor.execute(
            "SELECT id, subject_id, name, progress FROM topics WHERE subject_id = ?",
            (subject_id,),
        )
        topics = cursor.fetchall()
        conn.close()
        return topics
    except Exception as e:
        print(f"Error retrieving topics: {e}")
        return []


def get_topics_with_subject() -> list:
    """Retrieve all topics with their associated subject information.
    
    Returns:
        List of tuples containing (subject_name, topic_name, topic_id, progress, subject_id)
    """
    try:
        conn, cursor = connect_db()
        cursor.execute("""
            SELECT s.name, t.name, t.id, t.progress, s.id 
            FROM subjects s 
            LEFT JOIN topics t ON s.id = t.subject_id
        """)
        data = cursor.fetchall()
        conn.close()
        return data
    except Exception as e:
        print(f"Error retrieving topics with subject: {e}")
        return []


def delete_topic(topic_id: int) -> None:
    """Delete a topic and all associated data.
    
    Args:
        topic_id: The ID of the topic to delete
    """
    try:
        conn, cursor = connect_db()
        # Foreign keys with ON DELETE CASCADE handle related data
        cursor.execute("DELETE FROM topics WHERE id = ?", (topic_id,))
        conn.commit()
    except Exception as e:
        print(f"Error deleting topic: {e}")
    finally:
        conn.close()


# --- TASK FUNCTIONS ---
def add_task(title: str, date: str) -> None:
    """Add a new task for a specific date.
    
    Args:
        title: The task title
        date: The date for the task (format: YYYY-MM-DD)
    """
    try:
        conn, cursor = connect_db()
        cursor.execute(
            "INSERT INTO tasks (title, date, completed) VALUES (?, ?, 0)",
            (title, date),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error adding task: {e}")


def get_tasks(date: str) -> list:
    """Retrieve all tasks for a specific date.
    
    Args:
        date: The date to retrieve tasks for (format: YYYY-MM-DD)
        
    Returns:
        List of tuples containing (id, title, completed) for each task
    """
    try:
        conn, cursor = connect_db()
        cursor.execute("SELECT id, title, completed FROM tasks WHERE date = ?", (date,))
        tasks = cursor.fetchall()
        conn.close()
        return tasks
    except Exception as e:
        print(f"Error retrieving tasks: {e}")
        return []


def mark_task_status(task_id: int, status: int) -> None:
    """Update a task's completion status.
    
    Args:
        task_id: The ID of the task
        status: 0 for incomplete, 1 for complete
    """
    try:
        conn, cursor = connect_db()
        cursor.execute("UPDATE tasks SET completed = ? WHERE id = ?", (status, task_id))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error updating task status: {e}")


def mark_task_complete(task_id: int) -> None:
    """Mark a task as complete.
    
    Args:
        task_id: The ID of the task to mark complete
    """
    try:
        conn, cursor = connect_db()
        cursor.execute("UPDATE tasks SET completed = 1 WHERE id = ?", (task_id,))
        conn.commit()
    except Exception as e:
        print(f"Error marking task complete: {e}")
    finally:
        conn.close()


def delete_task(task_id: int) -> None:
    """Delete a task.
    
    Args:
        task_id: The ID of the task to delete
    """
    try:
        conn, cursor = connect_db()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error deleting task: {e}")


# --- QUIZ FUNCTIONS ---
def save_quiz_result(
    topic_id: int, score: int, total: int, questions_json: str = ""
) -> None:
    """Save quiz attempt results.
    
    Args:
        topic_id: The ID of the topic the quiz covers
        score: Number of questions answered correctly
        total: Total number of questions
        questions_json: JSON string containing quiz questions (optional)
    """
    try:
        conn, cursor = connect_db()
        cursor.execute(
            """
            INSERT INTO quiz_history (topic_id, score, total, questions_json)
            VALUES (?, ?, ?, ?)
        """,
            (topic_id, score, total, questions_json),
        )
        conn.commit()
        conn.close()
        update_topic_progress(topic_id)
    except Exception as e:
        print(f"Error saving quiz result: {e}")


def get_latest_score(topic_id: int) -> tuple | None:
    """Get the latest quiz score for a topic.
    
    Args:
        topic_id: The ID of the topic
        
    Returns:
        Tuple containing (score, total) or None if no quizzes taken
    """
    try:
        conn, cursor = connect_db()
        cursor.execute(
            """
            SELECT score, total FROM quiz_history 
            WHERE topic_id = ? 
            ORDER BY created_at DESC LIMIT 1
        """,
            (topic_id,),
        )
        result = cursor.fetchone()
        conn.close()
        return result
    except Exception as e:
        print(f"Error retrieving latest score: {e}")
        return None


def update_topic_progress(topic_id: int) -> None:
    """Calculate and update a topic's progress based on quiz performance.
    
    Progress is calculated as the percentage of correct answers across all quizzes.
    
    Args:
        topic_id: The ID of the topic to update
    """
    try:
        conn, cursor = connect_db()
        cursor.execute(
            "SELECT score, total FROM quiz_history WHERE topic_id = ?", (topic_id,)
        )
        results = cursor.fetchall()

        if results:
            total_score = sum(score for score, total in results)
            total_possible = sum(total for score, total in results)
            progress = (total_score / total_possible * 100) if total_possible > 0 else 0
        else:
            progress = 0

        cursor.execute("UPDATE topics SET progress = ? WHERE id = ?", (int(progress), topic_id))
        conn.commit()
    except Exception as e:
        print(f"Error updating topic progress: {e}")
    finally:
        conn.close()


def get_notes_for_topic(topic_id: int) -> list:
    """Retrieve all notes for a topic.
    
    Args:
        topic_id: The ID of the topic
        
    Returns:
        List of tuples containing (content, created_at) for each note, 
        ordered by creation date (newest first)
    """
    try:
        conn, cursor = connect_db()
        cursor.execute(
            """
            SELECT content, created_at FROM notes 
            WHERE topic_id = ? 
            ORDER BY created_at DESC
        """,
            (topic_id,),
        )
        notes = cursor.fetchall()
        conn.close()
        return notes
    except Exception as e:
        print(f"Error retrieving notes: {e}")
        return []