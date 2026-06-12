import flet as ft
import sqlite3
import asyncio
from backend.ai import analyze_study_material
from components.header import app_header

def ai_tools_view(page: ft.Page, file_picker: ft.FilePicker):
    # --- Database Helper ---
    def get_topics():
        conn = sqlite3.connect("edumentra.db")
        cursor = conn.cursor()
        # Fetching ID and Name to populate the dropdown
        # Only show each topic once. Duplicates can appear in legacy DBs.
        cursor.execute("SELECT id, name FROM topics GROUP BY id, name ORDER BY name")
        rows = cursor.fetchall()
        conn.close()
        return [ft.dropdown.Option(key=str(row[0]), text=row[1]) for row in rows]

    # --- UI Elements ---
    result_display = ft.Markdown(
        value="Upload a photo to get started...",
        selectable=True,
        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
    )
    
    loading_indicator = ft.ProgressBar(visible=False, color="purple")
    
    topic_dropdown = ft.Dropdown(
        label="Select Topic to save notes",
        hint_text="Choose a topic...",
        options=get_topics(),
        width=300,
        border_color="purple",
    )

    save_button = ft.ElevatedButton(
        "Save to Topic",
        icon=ft.Icons.SAVE,
        bgcolor="purple",
        color="white",
        visible=False, # Hidden until AI finishes
        on_click=lambda _: save_note()
    )

    # --- Logic ---
    def save_note():
        if not topic_dropdown.value:
            snack_bar = ft.SnackBar(content=ft.Text("Please select a topic before saving."))
            snack_bar.open = True
            page.overlay.append(snack_bar)
            return

        try:
            conn = sqlite3.connect("edumentra.db")
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO notes (topic_id, content) VALUES (?, ?)",
                (topic_dropdown.value, result_display.value)
            )
            conn.commit()
            conn.close()
            
            snack_bar = ft.SnackBar(content=ft.Text("✅ Notes successfully linked to topic!"))
            snack_bar.open = True
            page.overlay.append(snack_bar)
            save_button.visible = False # Prevent double-saving
            page.update()
        except Exception as e:
            print(f"Error saving: {e}")

    async def handle_file_pick():
        try:
            files = await file_picker.pick_files(allow_multiple=False)

            # If user cancelled or didn't select a file, don't show analyzing state
            if not files:
                result_display.value = "No file selected."
                page.update()
                return

            # Show analyzing state only after a file is selected
            loading_indicator.visible = True
            result_display.value = "_AI is analyzing..._"
            save_button.visible = False
            page.update()

            # Reject non-image uploads early to avoid PIL/vision errors
            ext = files[0].path.lower().rsplit('.', 1)[-1] if '.' in files[0].path else ''
            allowed_exts = {"jpg", "jpeg", "png", "webp", "gif", "bmp"}
            if ext not in allowed_exts:
                result_display.value = "Error: Please upload an image file (jpg/jpeg/png/webp/gif/bmp). Videos like .mp4 are not supported."
                save_button.visible = False
                page.update()
                return

            # Run analysis off the main thread
            analysis = await asyncio.to_thread(analyze_study_material, files[0].path)
            result_display.value = analysis
            save_button.visible = True  # Now the user can save!

        except Exception as ex:
            result_display.value = f"Error: {str(ex)}"
        finally:
            loading_indicator.visible = False
            page.update()

    return ft.Container(
        expand=True,
        padding=20,
        content=ft.Column([
            app_header("AI Study Assistant"),
            ft.Text("Transform your photos into structured study notes.", size=16, color=ft.Colors.BLACK_54),
            
            ft.Row([
                ft.ElevatedButton(
                    "Step 1: Upload Notes", 
                    icon=ft.Icons.IMAGE,
                    on_click=lambda _: page.run_task(handle_file_pick)
                ),
                topic_dropdown,
                save_button,
            ], alignment=ft.MainAxisAlignment.START, spacing=20),
            
            loading_indicator,
            
            ft.Divider(height=30),
            
            # This container ensures the text fills the width
            ft.Container(
                content=result_display,
                expand=True,
                alignment=ft.Alignment.TOP_LEFT,
            )
        ], 
        scroll=ft.ScrollMode.ADAPTIVE, 
        expand=True,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH # Fills the width
        )
    )