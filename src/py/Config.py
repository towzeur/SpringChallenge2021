from typing import Callable, Any
#import java.util.Properties
#import java.util.function.Function

class Config:

    STARTING_SUN       : int = 0
    MAP_RING_COUNT     : int = 3
    STARTING_NUTRIENTS : int = 20
    MAX_ROUNDS         : int = 24
    MAX_EMPTY_CELLS    : int = 10

    @staticmethod
    def load(params: Properties):
        STARTING_SUN = Config.getFromParams(params, "STARTING_SUN", STARTING_SUN)
        MAP_RING_COUNT = Config.getFromParams(params, "MAP_RING_COUNT", MAP_RING_COUNT)
        STARTING_NUTRIENTS = Config.getFromParams(params, "STARTING_NUTRIENTS_LUSH", STARTING_NUTRIENTS)
        MAX_ROUNDS = Config.getFromParams(params, "MAX_ROUNDS", MAX_ROUNDS)
        MAX_EMPTY_CELLS = Config.getFromParams(params, "MAX_EMPTY_CELLS", MAX_EMPTY_CELLS)
    

    @staticmethod
    def export(params: Properties):
        pass
    
    @staticmethod
    def getFromParams(params: Properties, name: str, defaultValue: int) -> int:
        return Config._getFromParams(params, name, defaultValue, int)
    

    @staticmethod
    def _getFromParams(params: Properties, name: str, defaultValue: Any, convert: Callable[[str], Any]):
        inputValue: str = params.getProperty(name)
        if inputValue is not None:
            try:
                return convert(inputValue)
            except ValueError:
                pass
        return defaultValue
    
