# Inventory WebUI

This folder contains the shared hardware inventory and a lightweight local WebUI.

## Files

- `HARDWARE_INVENTORY.md` — human-readable inventory
- `hardware_inventory.json` — machine-editable source of truth
- `inventory_webui.py` — local WebUI server (no external dependencies)

## Run

```bash
python /home/openclaw/.openclaw/workspace/inventory/inventory_webui.py
```

Then open:

- `http://<jetson-ip>:8787`

## Behavior

- Add, edit, move, and delete inventory items directly in the WebUI
- Sort by clicking column headers
- Filter by quick search, section (active/spare), and type
- Changes update `hardware_inventory.json`
- Markdown is regenerated automatically into `HARDWARE_INVENTORY.md`
- Change-log entries are appended automatically for WebUI edits

## Autostart (systemd user service)

```bash
systemctl --user status inventory-webui.service
systemctl --user restart inventory-webui.service
```

Service file:
- `~/.config/systemd/user/inventory-webui.service`

## Notes

- This is LAN-local and intentionally simple.
- Keep inventory changes committed/pushed so both humans and assistant stay in sync.
