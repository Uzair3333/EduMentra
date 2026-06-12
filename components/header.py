"""Header component with EduMentra logo.

Provides a consistent branded header for all pages.
"""

import flet as ft


def app_header(title: str = "EduMentra") -> ft.Container:
    """Create a header with logo and title for app pages.
    
    Args:
        title: The title to display next to the logo (default: "EduMentra")
        
    Returns:
        A Container with logo and title
    """
    return ft.Container(
        content=ft.Row(
            [
                ft.Image(
                    src="assets/logo.png",
                    width=50,
                    height=50,
                    fit=ft.BoxFit.CONTAIN,
                ),
                ft.Column(
                    [
                        ft.Text(
                            title,
                            size=28,
                            weight="bold",
                            color="blue",
                        ),
                        ft.Text(
                            "Master Your Learning",
                            size=12,
                            color="grey",
                        ),
                    ],
                    spacing=2,
                ),
            ],
            spacing=15,
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=20,
        border_radius=10,
    )
