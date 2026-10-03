"""Theme registrations for the Ani-Watch TUI."""

from textual.theme import Theme


MIDNIGHT_THEME = Theme(
    name="midnight",
    primary="#7aa2f7",
    secondary="#565f89",
    accent="#bb9af7",
    foreground="#c0caf5",
    background="#1a1b26",
    success="#9ece6a",
    warning="#e0af68",
    error="#f7768e",
    surface="#24283b",
    panel="#1f2335",
    dark=True,
)

SOLARIZED_THEME = Theme(
    name="solarized",
    primary="#268bd2",
    secondary="#2aa198",
    accent="#b58900",
    foreground="#839496",
    background="#002b36",
    success="#859900",
    warning="#cb4b16",
    error="#dc322f",
    surface="#073642",
    panel="#073642",
    dark=True,
)

THEMES = (MIDNIGHT_THEME, SOLARIZED_THEME)
