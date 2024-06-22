from urllib.request import Request, urlopen
from http.client import HTTPResponse
from timeit import default_timer as timer
from .other import scale_data, path_manager, calibrate_dl_speed
from .other import loading_bar
import ssl


def download(filename: str, url: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    context = ssl._create_unverified_context()

    # Path Manager
    path, filename = path_manager(filename)

    # Download Area
    uopen: HTTPResponse = urlopen(Request(url, headers=headers), context=context)

    dl_content = 0

    file_size = int(uopen.info()['Content-Length'])  # file_size is in bytes

    scale_size, type_data = scale_data(file_size * 8)

    print(f'Start downloading: {filename} Size: {scale_size}{type_data}  ')  # scale_data richiede il dato in Bit

    # Create/Write File
    with open(f'{path}/{filename}', 'wb') as f:
        download_speed = 10

        while dl_content != file_size:

            # Manage for a maximum download speed
            start = timer()
            buffer = uopen.read(download_speed)

            # Calculate max speed on a second
            calibrate_dl_speed(
                timer()-start, download_speed,
                file_size, dl_content
            )

            # Esclude None content
            if buffer:
                # Count downloaded Byte
                dl_content += len(buffer)
                # Write buffer on file
                f.write(buffer)
                yield file_size, dl_content, download_speed


if __name__ == "__main__":
    for file_size, dl_content, download_speed in download(filename="test.mp4",
                                                          url="https://video-cdn1.gelbooru.com/images/ac/91/ac91ccad3d83e9feee352e82b0221999.mp4"):
        download_speed, type_data = scale_data(download_speed * 8)
        print(
            f'Downloaded: {loading_bar(dl_content, file_size, 20)} {dl_content // (file_size // 100)}% Speed: {download_speed} {type_data}/s     ',
            end='\r')
