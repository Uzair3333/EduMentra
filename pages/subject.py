import flet as ft
from backend.logic import *
from backend.ai import generate_quiz_from_ai
from components.header import app_header
import asyncio

def show_message(page: ft.Page, message):
    snack_bar = ft.SnackBar(content=ft.Text(message))
    snack_bar.open = True
    page.overlay.append(snack_bar)

async def start_quiz(page:ft.Page, topic_name, topic_id, subject_id, subject_name, content_container, go_back_callback):
    loading_dialog = ft.AlertDialog(
        content=ft.Row([
            ft.ProgressRing(color=ft.Colors.BLUE),
            ft.Text(" AI is thinking...")
        ], alignment="center"),
        modal=True
    )
    page.show_dialog(loading_dialog)

    quiz_data = await asyncio.to_thread(generate_quiz_from_ai, topic_name)

    page.pop_dialog()

    if quiz_data == "RATE_LIMIT":
        show_message(page, "AI rate limit reached. Please try again later.")
    elif quiz_data:
        content_container.content = quiz_page(page, topic_name, quiz_data, topic_id, go_back_callback, subject_id, subject_name)
        page.update()
    else:
        show_message(page, "Failed to generate quiz. Please try again.")

    page.update()


def subject_view(page:ft.Page, content_container):

    def remove_subject(subject_id):
        delete_subject(subject_id)
        show_message(page, "Subject deleted")
        load_subjects()

    def remove_topic(topic_id):
        delete_topic(topic_id)
        show_message(page, "Topic deleted")
        load_subjects()

    def build_subject_items():
        items = []
        data = get_topics_with_subject()
        grouped = {}
        for sub_name, top_name, tid, prog, sid in data:
            if sid not in grouped:
                grouped[sid] = {
                    "name": sub_name,
                    "topics": []
                }
            if top_name:
                grouped[sid]["topics"].append((tid, top_name, prog))

        for sid, group in grouped.items():
            subject_name = group["name"]

            items.append(
                ft.Container(
                    content=ft.Column([
                        ft.Container(
                            content=ft.Row([
                                ft.Text(subject_name, weight="bold", size=18),
                                ft.IconButton(
                                    ft.Icons.DELETE,
                                    icon_color="red",
                                    on_click=lambda e, sid=sid: remove_subject(sid)
                                )
                            ], alignment="spaceBetween"),
                            on_click=lambda e, sid=sid, sname=subject_name: (
                                setattr(content_container, 'content', topic_view(page, sid, sname, content_container)),
                                page.update()
                            )
                        ),
                        ft.Text(f"{len(group['topics'])} topics", size=14, color=ft.Colors.GREY)
                    ], spacing=10),
                    padding=15,
                    border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
                    border_radius=10,
                    margin=ft.margin.only(bottom=15)
                )
            )

        return items

    subject_list = ft.Column(scroll=ft.ScrollMode.ADAPTIVE, expand=True)

    def load_subjects():
        subject_list.controls = build_subject_items()
        page.update()

    subject_list.controls = build_subject_items()

    return ft.Column([
        app_header("All Subjects"),
        ft.Divider(),
        subject_list
    ], expand=True)

def topic_view(page: ft.Page, subject_id, subject_name, content_container):
    topic_input = ft.TextField(label="New Topic", expand=True)
    topics_column = ft.Column(spacing=10)
    old_progress = {}

    def topic_detail_view(topic_id, topic_name):
        notes = get_notes_for_topic(topic_id)
        
        notes_list = ft.Column(scroll=ft.ScrollMode.ADAPTIVE, expand=True)

        if not notes:
            notes_list.controls.append(ft.Text("No AI notes saved for this topic yet.", italic=True))
        else:
            for content, date in notes:
                notes_list.controls.append(
                    ft.Card(
                        content=ft.Container(
                            padding=15,
                            content=ft.Column([
                                ft.Text(f"Saved on: {date}", size=12, color="grey"),
                                ft.Markdown(content, selectable=True),
                            ])
                        )
                    )
                )

        return ft.Container(
            content=ft.Column([
                ft.Text(f"AI Notes for {topic_name}", size=25, weight="bold"),
                ft.ElevatedButton(
                    "Back to Topics",
                    icon=ft.Icons.ARROW_BACK,
                    on_click=lambda _: (setattr(content_container, 'content', topic_view(page, subject_id, subject_name, content_container)), page.update())
                ),
                ft.Divider(),
                notes_list
            ], spacing=15),
            padding=20
        )

    def view_ai_notes(topic_id, topic_name):
        content_container.content = topic_detail_view(topic_id, topic_name)
        page.update()

    # 1. Define the refresh logic
    def load_topics():
        topics_column.controls.clear()
        topics = get_topics(subject_id)
        
        for topic in topics:
            tid, _, name, progress, *_ = topic
            score_data = get_latest_score(tid)
            
            if score_data:
                actual_score, total_qs = score_data
                score_text = f"Last Score: {actual_score}/{total_qs}"
                score_color = ft.Colors.GREEN if actual_score > 3 else (
                    ft.Colors.ORANGE if actual_score == 3 else ft.Colors.RED
                )
            else:
                score_text = "No attempts yet"
                score_color = ft.Colors.GREY_500

            progress_bar = ft.ProgressBar(value=old_progress.get(tid, progress) / 100, color="blue")

            topics_column.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(name, size=18, weight="bold", expand=True),
                            ft.Container(
                                content=ft.Text(score_text, size=11, color="white", weight="bold"),
                                bgcolor=score_color,
                                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                border_radius=5,
                            )
                        ], alignment="spaceBetween"),
                        progress_bar,
                        ft.Row([
                            ft.Text(f"{progress}%", size=12, color=ft.Colors.GREY),
                            ft.Row([
                                ft.ElevatedButton(
                                    "View AI Notes",
                                    icon=ft.Icons.NOTE,
                                    bgcolor="purple",
                                    color="white",
                                    on_click=lambda e, n=name, i=tid: view_ai_notes(i, n)
                                ),
                                ft.ElevatedButton(
                                    "Quiz Me", 
                                    icon=ft.Icons.QUIZ, 
                                    on_click=lambda e, n=name, i=tid: page.run_task(
                                        start_quiz, page, n, i, subject_id, subject_name, content_container, lambda: setattr(content_container, 'content', topic_view(page, subject_id, subject_name, content_container))
                                    )
                                ),
                                ft.IconButton(
                                    ft.Icons.DELETE, 
                                    icon_color="red", 
                                    on_click=lambda e, tid=tid: remove_topic(tid)
                                )
                            ], spacing=10)
                        ], alignment="spaceBetween")
                    ]),
                    padding=15, 
                    border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT), 
                    border_radius=10,
                    margin=ft.margin.only(bottom=10)
                )
            )

            # Animate progress if it changed
            if tid in old_progress and old_progress[tid] != progress:
                async def animate(pb=progress_bar, start=old_progress[tid], end=progress):
                    steps = 20
                    step = (end - start) / steps
                    current = start
                    for _ in range(steps):
                        current += step
                        pb.value = current / 100
                        page.update()
                        await asyncio.sleep(0.02)
                    pb.value = end / 100
                    page.update()
                page.run_task(animate)

            old_progress[tid] = progress

        page.update()

    # 3. Helper actions
    def add_new_topic(e):
        if topic_input.value:
            add_topic(subject_id, topic_input.value)
            show_message(page, "Topic added")
            topic_input.value = ""
            load_topics()
    
    def remove_topic(tid):
        delete_topic(tid)
        show_message(page, "Topic deleted")
        load_topics()

    # Initial run
    load_topics()

    return ft.Container(content=ft.Column([
        ft.Row([
            ft.ElevatedButton(
                "Back to Subjects",
                icon=ft.Icons.ARROW_BACK,
                on_click=lambda _: (setattr(content_container, 'content', subject_view(page, content_container)), page.update())
            ),
            ft.Text(subject_name, size=25, weight="bold")
        ], alignment="spaceBetween"),
        ft.Row([topic_input, ft.ElevatedButton("Add", on_click=add_new_topic)]),
        ft.Divider(),
        topics_column
    ], spacing=15), padding=20)

# 🏆 NEW: The Quiz Page UI
def quiz_page(page: ft.Page, topic_name, quiz_data, topic_id, go_back_callback, subject_id, subject_name):
    user_selections = {}

    def submit_quiz(e):
        try:
            score = 0
            # 1. Calculate the score
            for i, q in enumerate(quiz_data):
                if user_selections.get(i) == q['answer']:
                    score += 1
            
            # 2. Save the result to the database (Using the topic_id passed to quiz_page)
            save_quiz_result(
                topic_id=topic_id, 
                score=score, 
                total=len(quiz_data)
            )
            
            result_dialog = ft.AlertDialog(
                title=ft.Text("Quiz Results Saved!"),
                content=ft.Column([
                    ft.Text(f"Topic: {topic_name}", size=16),
                    ft.Text(f"Score: {score} / {len(quiz_data)}", size=20, weight="bold", color="green"),
                ], tight=True),
                actions=[
                    ft.TextButton("Back to Topics", on_click=lambda e: (page.pop_dialog(), go_back_callback(), page.update()))
                ],
            )

            # 4. Display the dialog
            page.show_dialog(result_dialog)
            
        except Exception as ex:
            # This will catch things like 'total' column missing or topic_id being null
            print(f"Error in submit_quiz: {ex}")
            # Still show the dialog so the user isn't stuck
            page.show_dialog(ft.AlertDialog(title=ft.Text("Error saving results, but you finished!")))

    

    # --- THE FIX IS HERE ---
    # We use a Column with scroll="always" or "adaptive"
    quiz_content = ft.Column(
        scroll=ft.ScrollMode.ALWAYS, # This enables the scrollbar
        expand=True,                 # This tells it to take up available space
        spacing=20
    )

    for i, q in enumerate(quiz_data):
        def save_ans(e, idx=i):
            user_selections[idx] = e.control.value

        quiz_content.controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Text(f"{i+1}. {q['question']}", size=16, weight="bold"),
                    ft.RadioGroup(
                        content=ft.Column([
                            ft.Radio(value=opt, label=opt) for opt in q['options']
                        ]),
                        on_change=save_ans
                    ),
                    ft.Divider()
                ]),
                padding=10
            )
        )

    # Add the Submit button at the very end of the column
    quiz_content.controls.append(
        ft.ElevatedButton(
            "Finish & Score", 
            on_click=submit_quiz, 
            bgcolor="blue", 
            color="white", 
            height=50
        )
    )

    return ft.Container(
        padding=20,
        expand=True, # Make sure the main container expands to the page height
        content=ft.Column([
            ft.Text(f"Quiz: {topic_name}", size=24, weight="bold", color="blue"),
            quiz_content # This is our scrollable column
        ], expand=True)
    )

