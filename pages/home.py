import flet as ft
from backend.logic import (
    add_subject,
    get_subjects,
    delete_subject,
)
from components.header import app_header

def show_message(page: ft.Page, message):
    snack_bar = ft.SnackBar(content=ft.Text(message))
    snack_bar.open = True
    page.overlay.append(snack_bar)


def home_page(page: ft.Page, on_open_subject=None):
    subject_input = ft.TextField(label="Add New Subject", expand=True)
    subjects_column = ft.Column(spacing=10)

    def remove_subject(sid):
        delete_subject(sid)
        show_message(page, "Subject deleted")
        load_subjects()

    def load_subjects():
        subjects_column.controls.clear()
        subjects = get_subjects()
        # Show only a small subset on the Home page to avoid duplicating the
        # full "All Subjects" view. Adjust this number if needed.
        subjects = subjects[:5]

        for sid, name, *_ in subjects:
            subjects_column.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.TextButton(
                            content=name,
                            on_click=lambda e, sid=sid, sname=name: open_subject(sid, sname),
                            expand=True
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE,
                            icon_color="red",
                            on_click=lambda e, sid=sid: remove_subject(sid)
                        )
                    ]),
                    padding=12,
                    border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
                    border_radius=10,
                )
            )

        page.update()

    def handle_add(e):
            if subject_input.value:
                add_subject(subject_input.value)
                subject_input.value = ""
                show_message(page, "Subject added successfully")
                load_subjects()
            page.update()

    def open_subject(subject_id, subject_name):
        if callable(on_open_subject):
            on_open_subject(subject_id, subject_name)
        else:
            show_message(page, f"Cannot open subject '{subject_name}' — navigation unavailable")

    load_subjects()

    return ft.Column([
        app_header("EduMentra"),
        ft.Container(
            padding=20,
            content=ft.Column([
                ft.Text("Ready to master your studies today?", size=16, color="grey"),
                ft.Divider(height=20),
                ft.Row([subject_input, ft.ElevatedButton("Add", on_click=handle_add)]),
                ft.Divider(height=20),
                ft.Text("Your Subjects", size=20, weight="w600"),
                subjects_column,
            ])
        )
    ], scroll=ft.ScrollMode.ADAPTIVE)