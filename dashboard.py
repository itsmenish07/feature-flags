from textual.app import App
from textual.screen import ModalScreen
from textual.containers import Vertical
from textual.widgets import Header, Footer, Static, Input, Label
import asyncio
import requests
import websockets

API_URL = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000/ws"


def get_flags():
    return requests.get(
        f"{API_URL}/flags"
    ).json()


def toggle_flag(flag_id):
    requests.put(
        f"{API_URL}/flags/{flag_id}"
    )


def update_rule(flag_id, group, rollout):
    requests.put(
        f"{API_URL}/flags/{flag_id}/rule",
        params={
            "target_group": group,
            "rollout_percentage": rollout
        }
    )


def delete_flag(flag_id):
    requests.delete(
        f"{API_URL}/flags/{flag_id}"
    )


def get_configs():
    return requests.get(
        f"{API_URL}/configs"
    ).json()


def delete_config(config_id):
    requests.delete(
        f"{API_URL}/configs/{config_id}"
    )


def update_config(config_id, value):
    requests.put(
        f"{API_URL}/configs/{config_id}",
        params={
            "value": value
        }
    )


class EditScreen(ModalScreen):

    def __init__(self, prompt, value=""):
        super().__init__()
        self.prompt = prompt
        self.start_value = value

    def compose(self):
        with Vertical(id="dialog"):
            yield Label(self.prompt)
            yield Input(value=self.start_value, id="field")

    def on_mount(self):
        self.query_one("#field").focus()

    def on_input_submitted(self, event):
        self.dismiss(event.value)


class Dashboard(App):

    CSS = """
    #dialog {
        width: 60;
        height: auto;
        padding: 1 2;
        border: round $accent;
        background: $surface;
    }
    """

    view = "flags"
    flag_index = 0
    config_index = 0

    BINDINGS = [
        ("up", "move_up", "Up"),
        ("down", "move_down", "Down"),
        ("tab", "switch_view", "Switch"),
        ("space", "toggle", "Toggle"),
        ("enter", "edit", "Edit"),
        ("d", "delete", "Delete"),
        ("r", "refresh", "Refresh"),
        ("q", "quit", "Quit"),
    ]

    def build_text(self):

        self.flags = get_flags()
        self.configs = get_configs()

        text = "🚀 FEATURE FLAG MANAGER\n\n"

        flags_title = "FLAGS" + (
            "  <<" if self.view == "flags" else ""
        )
        text += flags_title + "\n"
        text += "------------------------------\n"

        for i, flag in enumerate(self.flags):

            pointer = (
                "> "
                if self.view == "flags" and i == self.flag_index
                else "  "
            )

            status = "ON" if flag["enabled"] else "OFF"

            group = flag.get("target_group") or "everyone"
            rollout = flag.get("rollout_percentage", 100)

            detail = group
            if rollout < 100:
                detail += f" {rollout}%"

            text += (
                f"{pointer}"
                f"[{flag['id']}] "
                f"{flag['name']} "
                f"{status} "
                f"({detail})\n"
            )

        text += "\n"

        configs_title = "CONFIGS" + (
            "  <<" if self.view == "configs" else ""
        )
        text += configs_title + "\n"
        text += "------------------------------\n"

        for i, config in enumerate(self.configs):

            pointer = (
                "> "
                if self.view == "configs" and i == self.config_index
                else "  "
            )

            text += (
                f"{pointer}"
                f"{config['key']} : "
                f"{config['value']}\n"
            )

        text += "\n"
        text += "------------------------------\n"
        text += (
            "TAB Switch | SPACE Toggle | ENTER Edit | "
            "D Delete | R Refresh | Q Quit"
        )

        return text

    def update_display(self):
        self.query_one("#content").update(self.build_text())

    def compose(self):
        yield Header()
        yield Static(self.build_text(), id="content")
        yield Footer()

    def on_mount(self):
        self.run_worker(self.listen_for_updates(), exclusive=False)

    async def listen_for_updates(self):

        while True:

            try:
                async with websockets.connect(WS_URL) as ws:
                    async for _ in ws:
                        self.update_display()

            except Exception:
                await asyncio.sleep(2)

    def action_switch_view(self):
        self.view = "configs" if self.view == "flags" else "flags"
        self.update_display()

    def action_toggle(self):

        if self.view != "flags" or not self.flags:
            return

        flag = self.flags[self.flag_index]

        toggle_flag(flag["id"])

        self.update_display()
        self.notify(f"Toggled {flag['name']}")

    def action_edit(self):

        if self.view == "flags":

            if not self.flags:
                return

            flag = self.flags[self.flag_index]

            group = flag.get("target_group") or "everyone"
            rollout = flag.get("rollout_percentage", 100)

            self.push_screen(
                EditScreen(
                    f"Rule for {flag['name']} — group,rollout",
                    f"{group},{rollout}"
                ),
                self._save_rule
            )

        else:

            if not self.configs:
                return

            config = self.configs[self.config_index]

            self.push_screen(
                EditScreen(
                    f"Value for {config['key']}",
                    str(config["value"])
                ),
                self._save_config
            )

    def _save_rule(self, result):

        if result is None:
            return

        flag = self.flags[self.flag_index]

        parts = [p.strip() for p in result.split(",")]

        group = parts[0] if parts and parts[0] else "everyone"

        rollout = flag.get("rollout_percentage", 100)
        if len(parts) > 1 and parts[1]:
            try:
                rollout = int(parts[1])
            except ValueError:
                pass

        update_rule(flag["id"], group, rollout)

        self.update_display()
        self.notify(f"Updated {flag['name']}")

    def _save_config(self, result):

        if result is None:
            return

        config = self.configs[self.config_index]

        update_config(config["id"], result)

        self.update_display()
        self.notify(f"Updated {config['key']}")

    def action_delete(self):

        if self.view == "flags":

            if not self.flags:
                return

            flag = self.flags[self.flag_index]

            delete_flag(flag["id"])

            if self.flag_index > 0:
                self.flag_index -= 1

            self.update_display()
            self.notify(f"Deleted {flag['name']}")

        else:

            if not self.configs:
                return

            config = self.configs[self.config_index]

            delete_config(config["id"])

            if self.config_index > 0:
                self.config_index -= 1

            self.update_display()
            self.notify(f"Deleted {config['key']}")

    def action_refresh(self):
        self.update_display()
        self.notify("Refreshed")

    def action_move_up(self):

        if self.view == "flags":
            if self.flag_index > 0:
                self.flag_index -= 1
        else:
            if self.config_index > 0:
                self.config_index -= 1

        self.update_display()

    def action_move_down(self):

        if self.view == "flags":
            if self.flag_index < len(self.flags) - 1:
                self.flag_index += 1
        else:
            if self.config_index < len(self.configs) - 1:
                self.config_index += 1

        self.update_display()


if __name__ == "__main__":
    Dashboard().run()
