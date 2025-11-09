# def humanbytes(size):
#     # https://stackoverflow.com/a/49361727/4723940
#     # 2**10 = 1024
#     if not size:
#         return ""
#     power = 2**10
#     n = 0
#     Dic_powerN = {0: ' ', 1: 'Ki', 2: 'Mi', 3: 'Gi', 4: 'Ti'}
#     while size > power:
#         size /= power
#         n += 1
#     return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'

from decimal import Decimal, ROUND_HALF_UP

def humanbytes(size: int) -> str:
    """
    Convert bytes to a human-readable format with exact decimal rounding.
    Example:
        1024*1024 -> 1.05 MB
        384210000 -> 384.21 MB
    """
    if not size or size <= 0:
        return "0 B"

    power = Decimal(1000)
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    size = Decimal(size)
    n = 0

    while size >= power and n < len(units) - 1:
        size /= power
        n += 1

    # round exactly to 2 decimals
    size = size.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # remove trailing .00
    size_str = f"{size:.2f}".rstrip("0").rstrip(".")

    return f"{size_str} {units[n]}"
