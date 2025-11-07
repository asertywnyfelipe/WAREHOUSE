# Definicje własnych wyjątków

class WarehouseError(Exception):
    """Bazowy wyjątek magazynowy"""
    pass

class ProductNotFoundError(WarehouseError):
    """Produkt nie istnieje w bazie"""
    pass

class StockLimitExceededError(WarehouseError):
    """Przekroczono maksymalną ilość w pudełku"""
    pass

