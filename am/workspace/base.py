import os
import shutil
import textwrap

from datetime import datetime
from importlib.resources import files
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from am import data

console = Console()

class WorkspaceBase:
    """
    Workspace methods that do not rely on other classes.
    """
    def __init__(
            self,
            name: str = None,
            filename: str = None,
            workspace_path = None,
            verbose = False,
            **kwargs,
        ):
        self.set_name(name, filename)

        self.workspace_path = workspace_path
        self.verbose = verbose

        super().__init__(**kwargs)
    
    def set_name(self, name = None, filename = None):
        """
        Sets the `name` and `filename` values of the class.

        @param name: Name of workspace
        @param filename: `filename` override of workspace (no spaces)
        """
        # Sets `name` to approximate timestamp.
        if name is None:
            self.name = datetime.now().strftime("%Y%m%d_%H%M%S")
        else:
            self.name = name

        # Autogenerates `filename` from `name` if not provided.
        if filename == None:
            self.filename = self.name.replace(" ", "_")
        else:
            self.filename = filename

    def create_workspace(self, portfolio_path):
        """
        Called by Portfolio `manage.py`
        Creates folder to store data related to am workspace.

        @param portfolio_dir: Portfolio directory
        """
            
        self.workspace_path = os.path.join(portfolio_path, self.filename)

        # Creates workspace folder directory in portfolio directory.
        if not os.path.isdir(self.workspace_path):
            os.makedirs(self.workspace_path)
            # Print `create_workspace` success message.
            console.print(
                textwrap.dedent(f"""
                [bold green]✅ Workspace created successfully![/bold green]

                [cyan]Workspace folder:[/cyan] [bold]{self.filename}[/bold]
                [cyan]Location:[/cyan] [bold]{self.workspace_path}[/bold]

                Manage workspace with [magenta]manage.py[/magenta] at [underline]{self.workspace_path}[/underline]
                """),
                highlight=True
            )

            # Create a syntax-highlighted code block
            syntax = Syntax(f"cd {self.workspace_path}", "bash", theme="github-dark", line_numbers=False)

            # Wrap it in a bordered panel
            panel = Panel(
                syntax,  # Embed syntax highlighting inside the panel
                title="[cyan]Navigate to Workspace[/cyan]",  # Title on top
                border_style="blue",  # Blue border
                expand=False  # Keeps panel width minimal
            )
            console.print("Next Steps:")
            console.print(panel)
        else:
            warning = textwrap.dedent(f"""
            Folder for job `{self.filename}` already exists.
            Following operations may overwrite existing files within folder.
            """)
            print(warning)
            return self.workspace_path

        # Copy over `manage.py` file to created workspace.
        resource_path = os.path.join("workspace", "manage.py")
        manage_py_resource_path = files(data).joinpath(resource_path)
        manage_py_workspace_path = os.path.join(self.workspace_path, "manage.py")
        shutil.copy(manage_py_resource_path, manage_py_workspace_path)

        # Create `parts` folder and copy over `README.md`
        workspace_parts_path = os.path.join(self.workspace_path, "parts")
        os.makedirs(workspace_parts_path)

        resource_path = os.path.join("workspace", "parts", "README.md")
        README_md_resource_path = files(data).joinpath(resource_path)
        README_md_workspace_path = os.path.join(self.workspace_path, "parts", "README.md")
        shutil.copy(README_md_resource_path, README_md_workspace_path)

        # TODO: Generate workspace .xml

        return self.workspace_path
