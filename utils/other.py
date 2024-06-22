
def scale_data(data: int) -> tuple[int, str]:
    type_data = "bit"

    # from bit to byte
    if data >= 8:
        data = data / 8
        type_data = "byte"

    # from byte to kilobyte
    if data >= 1024:
        data = data / 1024
        type_data = "kb"

    # from kilobyte to megabyte
    if data >= 1024:
        data = data / 1024
        type_data = "mb"

    # from megabyte to gigabyte
    if data >= 1024:
        data = data / 1024
        type_data = "gb"

    return int(data), type_data


def path_manager(filename):
    if '/' in filename:
        *path, filename = filename.split('/')
        path = "/".join(path)
    elif '\\' in filename:
        *path, filename = filename.split('\\')
        path = "/".join(path)
    else:
        path = "."

    return path, filename


def calibrate_dl_speed(delta_time: float, download_speed: int, file_size: int, dl_content: int):
    download_speed = download_speed // delta_time

    # Manage error
    if download_speed > file_size:
        download_speed = 10

    # Manage for ultimate part of file
    if file_size - dl_content <= download_speed:
        download_speed = file_size - dl_content

    return download_speed


def loading_bar(current: int, end: int, length: int) -> str:
    slot_potential = end // length
    full_slot = current // slot_potential
    return f"[{'#' * full_slot}>{'-' * (length - full_slot - 1)}]" if full_slot != length else f"[{'#' * full_slot}{'-' * (length - full_slot)}]"
