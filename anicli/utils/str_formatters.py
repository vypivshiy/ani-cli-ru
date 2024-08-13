def float_to_hms(duration_float: float) -> str:
    """convert float or integet value to human-readable string (HH:MM:SS format)"""
    total_seconds = int(round(duration_float))

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    return f"{hours:02}:{minutes:02}:{seconds:02}"
