from decimal import Decimal, ROUND_HALF_UP

def human_size(num_bytes: int, decimal: bool = True) -> str:
    """
    Convert a byte value into a precise human-readable string.
    - decimal=True → uses 1000 (MB, GB)
    - decimal=False → uses 1024 (MiB, GiB)
    Example:
        1024*1024 -> 1.05 MB
        384210000 -> 384.21 MB
    """
    if not num_bytes or num_bytes < 0:
        return "0 B"

    base = Decimal(1000 if decimal else 1024)
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB']
    size = Decimal(num_bytes)
    n = 0

    while size >= base and n < len(units) - 1:
        size /= base
        n += 1

    size = size.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    size_str = f"{size:.2f}".rstrip("0").rstrip(".")
    return f"{size_str} {units[n]}"


