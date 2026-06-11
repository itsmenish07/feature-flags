from textual.app import App
from textual.widgets import Header, Footer, Static
import requests

API_URL = "http://127.0.0.1:8000"


def get_flags():
    return requests.get(
        f"{API_URL}/flags"
    ).json()


def toggle_flag(flag_id):
    requests.put(
        f"{API_URL}/flags/{flag_id}"
    )


def get_configs():
    return requests.get(
        f"{API_URL}/configs"
    ).json()

def update_config(config_id, value):

    requests.put(
        f"{API_URL}/configs/{config_id}",
        params={
            "value": value
        }
    )



class Dashboard(App):

    selected_index = 0

    BINDINGS = [
        ("up", "move_up", "Up"),
        ("down", "move_down", "Down"),
        ("space", "toggle", "Toggle"),
        ("r", "refresh", "Refresh"),
        ("q", "quit", "Quit"),
    ]



    def build_text(self):

        self.flags = get_flags()
        configs = get_configs()

        text = "🚀 FEATURE FLAG MANAGER\n\n"

        text += "FLAGS\n"
        text += "------------------------------\n"

        for i, flag in enumerate(self.flags):

            pointer = (
                "> "
                if i == self.selected_index
                else "  "
            )

            status = (
                "ON"
                if flag["enabled"]
                else "OFF"
            )

            text += (
                f"{pointer}"
                f"[{flag['id']}] "
                f"{flag['name']} "
                f"{status}\n"
            )

        text += "\n"

        text += "CONFIGS\n"
        text += "------------------------------\n"

        for config in configs:

            text += (
                f"{config['key']} : "
                f"{config['value']}\n"
            )

        text += "\n"
        text += "------------------------------\n"
        text += "↑ ↓ Select | SPACE Toggle | R Refresh | Q Quit"

        return text
    
    def update_display(self):

        self.query_one(
            "#content"
        ).update(
            self.build_text()
        )

    def compose(self):

        yield Header()

        yield Static(
            self.build_text(),
            id="content"
        )

        yield Footer()

    def action_toggle(self):

        if not self.flags:
            return

        selected_flag = self.flags[
            self.selected_index
        ]

        toggle_flag(
            selected_flag["id"]
        )

        self.update_display()

        self.notify(
            f"Toggled {selected_flag['name']}"
        )

    def action_refresh(self):

        self.update_display()

        self.notify(
            "Refreshed"
        )

    def action_move_up(self):

        if self.selected_index > 0:

            self.selected_index -= 1

            self.update_display()

    def action_move_down(self):

        if self.selected_index < len(self.flags) - 1:

            self.selected_index += 1

            self.update_display()


if __name__ == "__main__":
    Dashboard().run()