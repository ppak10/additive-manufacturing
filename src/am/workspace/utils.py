import os
import inquirer
from rich.console import Console
from rich.table import Table

console = Console()
class WorkspaceUtils():
    def select_file(self, directory, extension="*"):
        """List and present matching files in a directory recursively, filtered by extension."""

        # If no extension is provided or extension is '*', show all files
        if extension == "*" or not extension:
            extension = None  # No filtering, show all files

        # List matching files
        file_list = [
            file for _, _, files in os.walk(directory)
            for file in files if extension is None or file.endswith(extension)
        ]

        if not file_list:
            console.print(f"[bold red]No files found with extension '{extension}' in {directory}![/bold red]")
            return None

        # Display files in a styled table
        table = Table(header_style="bold cyan")
        table.add_column("#", justify="right", style="bold yellow")
        table.add_column(f"Matching File (*{extension})", style="green")

        for i, file in enumerate(file_list, start=1):
            table.add_row(str(i), file)

        console.print(table)

        # User selection prompt
        questions = [
            inquirer.List(
                "file",
                message="Select a file",
                choices=file_list,
            )
        ]
        answer = inquirer.prompt(questions)
        selected_file = answer["file"] if answer else None

        if selected_file:
            console.print(f"\n[bold green]You selected:[/bold green] {selected_file}")

        return selected_file
    
    def select_folder(self, directory):
        """List and present only the top-level folders in a directory."""

        # List only immediate subdirectories (not recursive)
        folder_list = [
            d for d in os.listdir(directory)
            if os.path.isdir(os.path.join(directory, d))
        ]

        if not folder_list:
            console.print(f"[bold red]No folders found in {directory}![/bold red]")
            return None

        # Display folders in a styled table
        table = Table(header_style="bold cyan")
        table.add_column("#", justify="right", style="bold yellow")
        table.add_column("Folder Path", style="green")

        for i, folder in enumerate(folder_list, start=1):
            table.add_row(str(i), folder)

        console.print(table)

        # User selection prompt
        questions = [
            inquirer.List(
                "folder",
                message="Select a folder",
                choices=folder_list,
            )
        ]
        answer = inquirer.prompt(questions)
        selected_folder = answer["folder"] if answer else None

        if selected_folder:
            console.print(f"\n[bold green]You selected:[/bold green] {selected_folder}")

        return selected_folder