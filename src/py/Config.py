from typing import Callable, Any

from py.java.compat import Properties


class Config:

    STARTING_SUN: int = 0
    MAP_RING_COUNT: int = 3
    STARTING_NUTRIENTS: int = 20
    MAX_ROUNDS: int = 24
    MAX_EMPTY_CELLS: int = 10

    @staticmethod
    def load(params: Properties):
        Config.STARTING_SUN = Config.getFromParams(params, "STARTING_SUN", 0)
        Config.MAP_RING_COUNT = Config.getFromParams(params, "MAP_RING_COUNT", 3)
        Config.STARTING_NUTRIENTS = Config.getFromParams(
            params, "STARTING_NUTRIENTS_LUSH", 20
        )
        Config.MAX_ROUNDS = Config.getFromParams(params, "MAX_ROUNDS", 24)
        Config.MAX_EMPTY_CELLS = Config.getFromParams(params, "MAX_EMPTY_CELLS", 10)

    @staticmethod
    def export(params: Properties):
        pass

    @staticmethod
    def getFromParams(params: Properties, name: str, defaultValue: int) -> int:
        return Config._getFromParams(params, name, defaultValue, int)

    @staticmethod
    def _getFromParams(
        params: Properties, name: str, defaultValue: Any, convert: Callable[[str], Any]
    ):
        inputValue: str = params.getProperty(name)
        if inputValue:
            try:
                return convert(inputValue)
            except ValueError:
                pass
        return defaultValue
