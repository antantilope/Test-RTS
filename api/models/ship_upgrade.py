
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
        required_core_upgrades: Dict[int, List[str]] = {},
        cost_progression: Dict[int, UpgradeCost] = {},
        effect_progression: Dict[int, List[UpgradeEffect]] = {},
        current_level: int = 0,
    ):

        max_level = max(cost_progression.keys())
        if max_level != max(effect_progression.keys()):
            raise Exception("ship upgrade improperly configured")

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
        },
    )
    radar_sensitivity = ShipUpgrade(
        "Radar Sensitivity",
        "radar_sensitivity",
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
    anti_radar_coating = ShipUpgrade(
        "Anti Radar Coating",
        "anti_radar_coating",
        required_core_upgrades={},
        cost_progression = {
            1: {
                "ore": 150,
                "electricity": 0,
                "seconds": 45,
            },
            2: {
                "ore": 200,
                "electricity": 0,
                "seconds": 60,
            },
            3: {
                "ore": 250,
                "electricity": 0,
                "seconds": 75,
            },
        },
        effect_progression = {
            1: [{'field': 'anti_radar_coating_level', 'delta': 1}],
            2: [{'field': 'anti_radar_coating_level', 'delta': 1}],
            3: [{'field': 'anti_radar_coating_level', 'delta': 1}],
        },
    )
    scanner_lock_traversal = ShipUpgrade(
        "Scanner Lock Traversal",
        "scanner_lock_traversal",
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
        },
    )
    engine_newtons = ShipUpgrade(
        "Engine Newtons",
        "engine_newtons",
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
    ore_capacity = ShipUpgrade(
        "Ore Capacity",
        "ore_capacity",
        required_core_upgrades={1: [titanium_alloy_hull.slug]},
        cost_progression = {
            1: {
                "ore": 100,
                "electricity": 35_000,
                "seconds": 45,
            },
            2: {
                "ore": 125,
                "electricity": 50_0000,
                "seconds": 65,
            },
        },
        effect_progression = {
            1: [{'field': 'cargo_ore_mass_capacity_kg', 'delta': 40}],
            2: [{'field': 'cargo_ore_mass_capacity_kg', 'delta': 50}],
        },
    )
    battery_capacity = ShipUpgrade(
        "Battery Capacity",
        "battery_capacity",
        required_core_upgrades={
            2: [advanced_electronics.slug],
            3: [titanium_alloy_hull.slug],
        },
        cost_progression = {
            1: {
                "ore": 50,
                "electricity": 20_000,
                "seconds": 35,
            },
            2: {
                "ore": 65,
                "electricity": 30_000,
                "seconds": 45,
            },
            3: {
                "ore": 80,
                "electricity": 45_000,
                "seconds": 60,
            },
            4: {
                "ore": 105,
                "electricity": 50_0000,
                "seconds": 60,
            },
        },
        effect_progression = {
            1: [{'field': 'battery_capacity', 'delta': 100_000}],
            2: [{'field': 'battery_capacity', 'delta': 100_000}],
            3: [{'field': 'battery_capacity', 'delta': 100_000}],
            4: [{'field': 'battery_capacity', 'delta': 100_000}],
        },
    )
    fuel_capacity = ShipUpgrade(
        "Fuel Capacity",
        "fuel_capacity",
        required_core_upgrades={
            3: [titanium_alloy_hull.slug],
        },
        cost_progression = {
            1: {
                "ore": 80,
                "electricity": 15_000,
                "seconds": 35,
            },
            2: {
                "ore": 100,
                "electricity": 20_000,
                "seconds": 45,
            },
            3: {
                "ore": 120,
                "electricity": 25_000,
                "seconds": 60,
            },
            4: {
                "ore": 140,
                "electricity": 30_0000,
                "seconds": 80,
            },
        },
        effect_progression = {
            1: [{'field': 'fuel_capacity', 'delta': 7_000}],
            2: [{'field': 'fuel_capacity', 'delta': 7_000}],
            3: [{'field': 'fuel_capacity', 'delta': 7_000}],
            4: [{'field': 'fuel_capacity', 'delta': 7_000}],
        },
    )

    return {
        UpgradeType.SHIP: [
            engine_newtons,
            scanner_lock_traversal,
            radar_sensitivity,
            anti_radar_coating,
            scanner_range,
            ore_capacity,
            battery_capacity,
            fuel_capacity,
        ],
        UpgradeType.CORE: [
            titanium_alloy_hull,
            advanced_electronics,
            liquid_nitrogen_cooling,
        ]
    }

