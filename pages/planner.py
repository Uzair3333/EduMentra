import flet as ft
from backend.logic import *
from components.header import app_header
from datetime import datetime
import asyncio

def show_message(page: ft.Page, message):
    snack_bar = ft.SnackBar(content=ft.Text(message))
    snack_bar.open = True
    page.overlay.append(snack_bar)

def planner_view(page: ft.Page):
    date_str = datetime.now().strftime("%Y-%m-%d")
    task_input = ft.TextField(label="What needs doing?", expand=True)

    task_list = ft.Column(scroll=ft.ScrollMode.ADAPTIVE, expand=True)
    progress_bar = ft.ProgressBar(value=0, color="green")

    def load_tasks():
        task_list.controls.clear()
        tasks = get_tasks(date_str)
        completed = sum(1 for tid, title, comp, *_ in tasks if comp == 1)
        total = len(tasks)
        progress_bar.value = completed / total if total else 0
        for tid, title, completed, *_ in tasks:
            task_list.controls.append(
                ft.Checkbox(
                    label=title,
                    value=True if completed == 1 else False,
                    on_change=lambda e, i=tid: on_task_change(e, i)
                )
            )
        page.update()

    def on_task_change(e, tid):
        old_tasks = get_tasks(date_str)
        old_completed = sum(1 for t in old_tasks if t[2] == 1)
        mark_task_status(tid, 1 if e.control.value else 0)
        new_tasks = get_tasks(date_str)
        new_completed = sum(1 for t in new_tasks if t[2] == 1)
        total = len(new_tasks)
        if total > 0:
            old_value = old_completed / total
            new_value = new_completed / total
            async def animate():
                current = old_value
                steps = 10
                step = (new_value - old_value) / steps
                for _ in range(steps):
                    current += step
                    progress_bar.value = current
                    page.update()
                    await asyncio.sleep(0.05)
                progress_bar.value = new_value
                page.update()
            page.run_task(animate)
        load_tasks()

    def submit_task(e):
        if task_input.value:
            add_task(task_input.value, date_str)
            task_input.value = ""
            show_message(page, "Task added successfully")
            load_tasks()

    load_tasks()
    def add_new_task(e):
        if task_input.value:
            add_task(task_input.value, date_str)
            show_message(page, "Task added successfully")
            task_input.value = ""
            load_tasks()

    def complete_task(task_id):
        mark_task_complete(task_id)
        show_message(page, "Task completed")
        load_tasks()

    def remove_task(task_id):
        delete_task(task_id)
        show_message(page, "Task deleted")
        load_tasks()

    return ft.Column([
        app_header("Daily Planner"),
        ft.Text("Daily Progress"),
        progress_bar,
        ft.Row([task_input, ft.IconButton(ft.Icons.ADD, on_click=submit_task)], spacing=10),
        task_list
    ], expand=True)


def go_back(page: ft.Page):
    from pages.home import home_page
    content_container = ft.Container(content=home_page(page), expand=True)

    def on_navigation_change(e):
        index = e.control.selected_index
        if index == 0:
            content_container.content = home_page()
        elif index == 1:
            content_container.content = planner_view()
        page.update()

    nav_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.HOME, label="Home"),
            ft.NavigationBarDestination(icon=ft.Icons.CALENDAR_TODAY, label="Planner"),
        ],
        selected_index=0,
        on_change=on_navigation_change,
    )

    page.controls.clear()
    page.add(
        ft.Column([
            content_container,
            nav_bar
        ], expand=True)
    )
    page.update()

