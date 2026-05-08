from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Static


class MyComApp(App):
    """MyCom — A modern dual-panel TUI file manager."""

    TITLE = "MyCom"
    CSS = """
    Screen {
        layout: grid;
        grid-size: 2 1;
    }
    .panel {
        border: solid green;
        height: 1fr;
    }
    """

    BINDINGS = [
        ("f10", "quit", "Quit"),
        ("ctrl+q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Left Panel", classes="panel")
        yield Static("Right Panel", classes="panel")
        yield Footer()


def main():
    app = MyComApp()
    app.run()


if __name__ == "__main__":
    main()
