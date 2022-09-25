
from typing import Dict, List, TypedDict, Union


class UpgradeType:
    SHIP = "ship"
    CORE = "core"

class UpgradeCost(TypedDict):
    ore: Union[float, int]
    electricity: Union[float, int]
    seconds: int

class UpgradeEffect(TypedDict):
    field: str
    delta: float

class UpgradeSummary(TypedDict):
    """ Data that is sent to the front end.
    """
    name: str
    current_level: int
    max_level: int
    seconds_researched: Union[int, float, None]
    current_cost: Union[UpgradeCost, None]

class BaseUpgrade:

    def __init__(self):
        self.seconds_researched: Union[int, float, None] = None

    def __str__(self):
        return f"<{self.slug}>"

    def __repr__(self):
        return self.__str__()

class ShipUpgrade(BaseUpgrade):
    """ Ship upgrades increase the stats of a ship
    """
    def __init__(
        self,
        name: str,
        slug: str,
        max_level: int,
        required_core_upgrades: Dict[int, List[str]] = {},
        cost_progression: Dict[int, UpgradeCost] = {},
        effect_progression: Dict[int, List[UpgradeEffect]] = {},
        current_level: int = 0,
    ):
        super().__init__()
        self.name = name
        self.slug = slug
        self.max_level = max_level
        self.required_core_upgrades = required_core_upgrades
        self.cost_progression = cost_progression
        self.effect_progression = effect_progression
        self.current_level = current_level

    def at_max_level(self) -> bool:
        return self.max_level <= self.current_level

class CoreUpgrade(BaseUpgrade):
    def __init__(
        self,
        name: str,
        slug: str,
        cost: UpgradeCost,
    ):
        """ Core upgrades unlock ship upgrades.
        """
        super().__init__()
        self.name = name
        self.slug = slug
        self.cost = cost
        self.earned = False



def get_upgrade_profile_1() -> Dict[str, List[Union[ShipUpgrade, CoreUpgrade]]]:

    # Core Upgrades
    titanium_alloy_hull = CoreUpgrade(
        "Titanium Allow Hull",
        "titanium_alloy_hull",
        {
            "ore": 200,
            "electricity": 10_000,
            "seconds": 75,
        },
    )
    advanced_electronics = CoreUpgrade(
        "Advanced Electronics",
        "advanced_electronics",
        {
            "ore": 150,
            "electricity": 30_000,
            "seconds": 50,
        },
    )
    liquid_nitrogen_cooling = CoreUpgrade(
        "Liquid Nitrogen Cooling",
        "liquid_nitrogen_cooling",
        {
            "ore": 175,
            "electricity": 20_000,
            "seconds": 65,
        },
    )


    # Ship Upgrades
    scanner_range = ShipUpgrade(
        "Scanner Range",
        "scanner_range",
        4,
        required_core_upgrades={3: [advanced_electronics.slug]},
        cost_progression = {
            1: {
                "ore": 75,
                "electricity": 50_000,
                "seconds": 30,
            },
            2: {
                "ore": 95,
                "electricity": 70_000,
                "seconds": 45,
            },
            3: {
                "ore": 150,
                "electricity": 90_000,
                "seconds": 55,
            },
        },
        effect_progression = {
            1: [{'field': 'scanner_radar_range', 'delta': 600},
                {'field': 'scanner_ir_range', 'delta': 800}],
            2: [{'field': 'scanner_radar_range', 'delta': 600},
                {'field': 'scanner_ir_range', 'delta': 800}],
            3: [{'field': 'scanner_radar_range', 'delta': 600},
                {'field': 'scanner_ir_range', 'delta': 800}],
            4: [{'field': 'scanner_radar_range', 'delta': 600},
                {'field': 'scanner_ir_range', 'delta': 800}]
        },
    )
    radar_sensitivity = ShipUpgrade(
        "Radar Sensitivity",
        "radar_sensitivity",
        3,
        required_core_upgrades={1: [advanced_electronics.slug]},
        cost_progression = {
            1: {
                "ore": 50,
                "electricity": 20_000,
                "seconds": 30,
            },
            2: {
                "ore": 120,
                "electricity": 30_000,
                "seconds": 45,
            },
            3: {
                "ore": 200,
                "electricity": 40_000,
                "seconds": 55,
            },
        },
        effect_progression = {
            1: [{'field': 'scanner_radar_sensitivity', 'delta': 1}],
            2: [{'field': 'scanner_radar_sensitivity', 'delta': 1}],
            3: [{'field': 'scanner_radar_sensitivity', 'delta': 1}],
        },
    )
    scanner_lock_traversal = ShipUpgrade(
        "Scanner Lock Traversal",
        "scanner_lock_traversal",
        3,
        required_core_upgrades={1: [advanced_electronics.slug]},
        cost_progression = {
            1: {
                "ore": 60,
                "electricity": 20_000,
                "seconds": 30,
            },
            2: {
                "ore": 90,
                "electricity": 30_000,
                "seconds": 45,
            },
            3: {
                "ore": 120,
                "electricity": 40_000,
                "seconds": 55,
            },
        },
        effect_progression = {
            1: [{'field': 'scanner_locking_max_traversal_degrees', 'delta': 0.5},
                {'field': 'scanner_locked_max_traversal_degrees', 'delta': 0.6}],
            2: [{'field': 'scanner_locking_max_traversal_degrees', 'delta': 0.5},
                {'field': 'scanner_locked_max_traversal_degrees', 'delta': 0.6}],
            3: [{'field': 'scanner_locking_max_traversal_degrees', 'delta': 0.5},
                {'field': 'scanner_locked_max_traversal_degrees', 'delta': 0.6}],
            4: [{'field': 'scanner_locking_max_traversal_degrees', 'delta': 0.5},
                {'field': 'scanner_locked_max_traversal_degrees', 'delta': 0.6}]
        },
    )
    engine_newtons = ShipUpgrade(
        "Engine Newtons",
        "engine_newtons",
        2,
        required_core_upgrades={2: [titanium_alloy_hull.slug]},
        cost_progression = {
            1: {
                "ore": 60,
                "electricity": 40_000,
                "seconds": 30,
            },
            2: {
                "ore": 90,
                "electricity": 50_000,
                "seconds": 60,
            },
        },
        effect_progression = {
            1: [{'field': 'engine_newtons', 'delta': 900}],
            2: [{'field': 'engine_newtons', 'delta': 1600}],
        },
    )

    return {
        UpgradeType.SHIP: [
            engine_newtons,
            scanner_lock_traversal,
            radar_sensitivity,
            scanner_range,
        ],
        UpgradeType.CORE: [
            titanium_alloy_hull,
            advanced_electronics,
            liquid_nitrogen_cooling,
        ]
    }

