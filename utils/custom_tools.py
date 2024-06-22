import ssl
from typing import IO
from http.client import HTTPResponse
from urllib.request import urlopen, Request
from timeit import default_timer as timer
from .other import scale_data, path_manager, calibrate_dl_speed


def parse_box(io: [IO, HTTPResponse]):
    buffer = io.read(4)
    size_box = int.from_bytes(buffer)
    buffer += io.read(4)
    name_box = str(buffer[4:8], encoding="utf-8")
    return buffer, size_box - 8, name_box


def get_video_length(io: [IO, HTTPResponse]) -> tuple[int, bytes]:
    buffer = []
    for _ in range(0, 100):  # setaccia i primi 400 byte
        temp_buffer = io.read(4)
        try:
            str_temp_buffer = str(temp_buffer, encoding="utf-8")
        except UnicodeError:
            str_temp_buffer = ""

        if not temp_buffer:  # fine del file o byte corrotti
            return 1
        buffer.append(temp_buffer)

        if str_temp_buffer == "mvhd":
            buffer.append(io.read(21))
            time_scale = int.from_bytes(buffer[-1][-8:-4])
            raw_duration = int.from_bytes(buffer[-1][-4:len(buffer[-1])])
            return (raw_duration // time_scale), b"".join(buffer)
    return 2


def video_longer_than(io: [IO, HTTPResponse], sec: int) -> tuple[bool, bytes]:
    duration, buffer = get_video_length(io)
    return duration > sec, buffer


def web_get_video_length(url: str) -> tuple[int, bytes]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    context = ssl._create_unverified_context()

    uopen: HTTPResponse = urlopen(Request(url, headers=headers), context=context)

    length, temp_buffer = get_video_length(uopen)

    return length, temp_buffer


def web_video_longer_than(url: str, sec: int):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    context = ssl._create_unverified_context()

    uopen: HTTPResponse = urlopen(Request(url, headers=headers), context=context)

    is_longer, temp_buffer = video_longer_than(uopen, sec)

    return is_longer, temp_buffer


def continue_download(file_name: str, io: HTTPResponse, buffer: bytes):
    # Path Manager
    path, filename = path_manager(file_name)

    # Download Area
    dl_content = len(buffer)

    file_size = int(io.info()['Content-Length'])  # file_size is in bytes

    scale_size, type_data = scale_data(file_size * 8)

    print(f'Start downloading: {filename} Size: {scale_size}{type_data}  ')  # scale_data richiede il dato in Bit

    # Create/Write File
    with open(f'{path}/{filename}', 'wb') as f:
        f.write(buffer)
        download_speed = 10

        while dl_content != file_size:

            # Manage for a maximum download speed
            start = timer()
            buffer = io.read(download_speed)

            # Calculate max speed on a second
            calibrate_dl_speed(
                timer() - start, download_speed,
                file_size, dl_content
            )

            # Esclude None content
            if buffer:
                # Count downloaded Byte
                dl_content += len(buffer)
                # Write buffer on file
                f.write(buffer)
                yield file_size, dl_content, download_speed
