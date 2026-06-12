"""EduMentra - AI-Powered Study Companion Application

A desktop application built with Flet that helps students master their learning through:
- Subject and topic organization
- AI-powered quiz generation
- Study material analysis with OCR
- Daily task planning
- Progress tracking

Entry point: Initializes the app, sets up database, and manages navigation between pages.
"""

import flet as ft
from backend.db import create_tables
from pages.ai_tools import ai_tools_view
from pages.home import home_page
from pages.subject import topic_view, subject_view
from pages.planner import planner_view


def main(page: ft.Page) -> None:
    """Initialize and run the EduMentra application.
    
    Args:
        page: The main Flet page object
    """
    create_tables()
    page.title = "EduMentra"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0

    file_picker = ft.FilePicker()

    def go_to_topic_view(sid: int, sname: str) -> None:
        """Navigate to the topic view for a specific subject.
        
        Args:
            sid: Subject ID
            sname: Subject name
        """
        content_container.content = topic_view(page, sid, sname, content_container)
        page.update()

    content_container = ft.Container(
        content=home_page(page, on_open_subject=go_to_topic_view), expand=True
    )

    def on_navigation_change(e) -> None:
        """Handle navigation bar selection changes.
        
        Args:
            e: The navigation change event
        """
        index = e.control.selected_index
        if index == 0:
            content_container.content = home_page(page, on_open_subject=go_to_topic_view)
        elif index == 1:
            content_container.content = subject_view(page, content_container)
        elif index == 2:
            content_container.content = planner_view(page)
        elif index == 3:
            content_container.content = ai_tools_view(page, file_picker)
        page.update()

    page.navigation_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.HOME, label="Home"),
            ft.NavigationBarDestination(icon=ft.Icons.BOOK, label="Subjects"),
            ft.NavigationBarDestination(icon=ft.Icons.CALENDAR_MONTH, label="Planner"),
            ft.NavigationBarDestination(icon=ft.Icons.AUTO_AWESOME, label="AI Notes"),
        ],
        selected_index=0,
        on_change=on_navigation_change,
    )

    page.add(content_container)


if __name__ == "__main__":
    ft.run(main)