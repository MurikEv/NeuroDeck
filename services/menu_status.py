"""Small, non-blocking status snapshot for the menu header."""

from datetime import datetime

from services import network_service


NETWORK_INDICATOR_NOTE = (
    "The three bars indicate Internet connectivity, not Wi-Fi signal strength."
)


def read_menu_status(now=None, network_status=None):
    """Format the clock and the existing network monitor's latest result.

    This function never probes the network or starts a monitor. Optional inputs
    make the display states easy to test without changing the system clock.
    """
    if now is None:
        now = datetime.now()
    if network_status is None:
        network_status = network_service.get_network_status()

    if network_status.get("last_checked_at") is None:
        network_state = "checking"
        network_bars = 0
        network_message = "Checking Internet connectivity."
    elif network_status.get("online", False):
        network_state = "online"
        network_bars = 3
        network_message = "Internet connection available."
    else:
        network_state = "offline"
        network_bars = 0
        network_message = "Internet connection unavailable."

    return {
        "time_text": now.strftime("%H:%M"),
        "network_bars": network_bars,
        "network_state": network_state,
        "network_label": "NET",
        "network_tooltip": f"{network_message} {NETWORK_INDICATOR_NOTE}",
    }
