import flet as ft
from pages.home import home_page
from pages.planner import planner_view

def bottom_navigation_bar(page: ft.Page, selected_index=0):
    def on_navigation_change(e):
        index = e.control.selected_index
        page.controls.clear()
        if index == 0:
            page.add(home_page(page))
        elif index == 1:
            page.add(planner_view(page))
        page.update()

    return ft.NavigationBar(
        destinations=[
            ft.NavigationDestination(icon=ft.icons.HOME, label="Home"),
            ft.NavigationDestination(icon=ft.icons.CALENDAR_TODAY, label="Planner"),
        ],
        selected_index=selected_index,
        on_change=on_navigation_change,
    )