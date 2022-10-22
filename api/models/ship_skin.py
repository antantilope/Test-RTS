
from typing import TypedDict, Dict


class ShipSkin(TypedDict):
    slug: str
    preview_color_hex: str


DEFAULT_SKIN_SLUG = "type_1_gray"

ship_skins: Dict[str, ShipSkin] = {
    "type_1_blue":{
        "slug": "type_1_blue",
        "preview_color_hex": "#0062ff",
    },
    "type_1_dark_purple":{
        "slug": "type_1_dark_purple",
        "preview_color_hex": "#721ba1",
    },
    "type_1_gray":{
        "slug": "type_1_gray",
        "preview_color_hex": "#a2b0bd",
    },
    "type_1_green":{
        "slug": "type_1_green",
        "preview_color_hex": "#2e8f39",
    },
    "type_1_light_green":{
        "slug": "type_1_light_green",
        "preview_color_hex": "#b2cc5e",
    },
    "type_1_neon_blue":{
        "slug": "type_1_neon_blue",
        "preview_color_hex": "#00ddff",
    },
    "type_1_orange":{
        "slug": "type_1_orange",
        "preview_color_hex": "#ffa21f",
    },
    "type_1_pink":{
        "slug": "type_1_pink",
        "preview_color_hex": "#faa2ee",
    },
    "type_1_purple":{
        "slug": "type_1_purple",
        "preview_color_hex": "#886bfa",
    },
    "type_1_red":{
        "slug": "type_1_red",
        "preview_color_hex": "#cc2b2b",
    },
    "type_1_yellow":{
        "slug": "type_1_yellow",
        "preview_color_hex": "#ffff1c",
    },
}

