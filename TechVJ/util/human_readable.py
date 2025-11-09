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

def humanbytes(size):
    """
    Convert bytes to human-readable format (decimal base).
    Example: 1024*1024 -> 1.05 MB
    """
    if not size:
        return ""
    power = 1000  # decimal
    n = 0
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    while size >= power and n < len(units) - 1:
        size /= power
        n += 1
    return f"{size:.2f} {units[n]}"
