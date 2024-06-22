import requests as req
from lxml import html
from utils import web_video_longer_than, web_get_video_length

posts_url_base = "https://gelbooru.com/index.php?page=post&s=view&id="

XPATH_POSTS = "/html/body/div[1]/main/div[7]/article"
XPATH_POST_IMAGE_DATA = '/html/body/div[1]/main/div[3]/section[1]/picture/img/@src'

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}
cookie = {
    "fringeBenefits": "yup",
    "comment_threshold": "0",
    "tag_blacklist": "gigantic_breasts%2520huge_breasts%2520pregnant%2520"

}

class Gelooru:
    BASE_LINK = 'https://gelbooru.com/'
    PHP_BASE = 'index.php?'
    BASE_RESEARCH = 'page=post&s=list&tags='
    BASE_POST = 'page=post&s=view&id='

    XPATH_POST_LIST = '/html/body/div[1]/main/div[7]/article'
    XPATH_POST_LINK = 'a/@id'
    XPATH_IMAGE = '/html/body/div[1]/main/div[3]/section[1]/picture/img/@src'
    XPATH_VIDEO = '/html/body/div[1]/main/div[3]/video/source[1]/@src'
    # XPATH_POST_TAGS = 'a/img/@alt'

    XPATH_LASTPAGE = '//*[@id="paginator"]/a[@alt="last page"]/@href'

    PAGE_SELECTOR = '&pid='
    U_PID = 42  # questo deve essere moltiplicato per in numero della pagina che vogliamo selezionare
    # esempio utilizzo f'{BASE_LINK}{PHP_BASE}{BASE_RESEARCH}{tags}{PAGE_SELECTOR}{U_PID*numeropagina}'
    PID = 0

    TAG_VIDEO = "VIDEO"
    TAG_IMAGE = "IMAGE"

    def __init__(self):
        self.n_page = 0
        self.tags = []
        self.video_duration_filter: list[int] = None
        self.link = None
        self.tree = None

    def build_link(self, tags: list[str, str] = None, n_page: int = None) -> str:
        if n_page:  # Manage None page
            self.n_page = n_page

        if self.n_page < 0:  # Manage negative numbers
            self.n_page = self.lastPage()

        self.tags = tags
        if not tags:  # Manage None tags
            self.tags = 'all'

        return f'{self.BASE_LINK}{self.PHP_BASE}{self.BASE_RESEARCH}{"+".join(self.tags)}{self.PAGE_SELECTOR}{self.U_PID * self.n_page}'

    def build_post_link(self, post_id: str or int):
        if isinstance(post_id, int):
            post_id = str(post_id)

        return f"{self.BASE_LINK}{self.PHP_BASE}{self.BASE_POST}{post_id}"

    def is_url(self, url: str) -> bool:
        return self.BASE_LINK in url

    def get_content_from_url(self, url: str) -> html.HtmlElement:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        cookie = {
            "fringeBenefits": "yup",
            "comment_threshold": "0"
        }

        response = req.get(url, headers=headers, cookies=cookie)

        if response.status_code == 200:
            return html.fromstring(response.content)

    def last_page(self) -> int:
        if url := self.tree.xpath(self.XPATH_LASTPAGE).__len__() != 0:  # Prevent error
            return int(url[0].split(self.PAGE_SELECTOR)[-1])
        return 0

    def set_page(self, tags: list[str, str] = None, n_page: int = None) -> None:
        self.link = self.build_link(tags, n_page)
        self.tree = self.get_content_from_url(self.link)

    def set_video_duration_filter(self, min: int = None, max: int = None):
        if min or max:
            self.video_duration_filter = [min, max]
        else:
            self.video_duration_filter = None

    def get_id_from_url(self, url: str) -> str:
        return url.split("&id=")[0]

    def get_tags_from_url(self, url: str) -> str:
        url = url.split('&tags=')[-1]
        if self.PAGE_SELECTOR in url:
            return url.split(self.PAGE_SELECTOR)[0]
        return url.replace('+', ', ')

    def get_npage_from_url(self, url: str) -> int:
        if self.PAGE_SELECTOR in url:
            return int(url.split(self.PAGE_SELECTOR)[-1]) // self.U_PID
        return 0

    def get_posts(self) -> list[dict[str:str, str:str, str:str]]:

        posts = self.tree.xpath(self.XPATH_POST_LIST)
        new_posts_list = []
        for index, post in enumerate(posts):
            post_id = post.xpath(self.XPATH_POST_LINK)[0][1:]
            post_data = self.get_post_from_id(post_id)

            if post_data["tag"] == self.TAG_VIDEO:
                if (min := self.video_duration_filter[0]) or (max := self.video_duration_filter[1]):
                    video_duration, _ = web_get_video_length(post_data["source"])
                    if min:
                        if video_duration < min:
                            continue
                    if max:
                        if video_duration > max:
                            continue
            new_posts_list.append(post_data)

        return posts

    def get_posts_from_page(self, n_page: int = None) -> list[dict[str:str, str:str, str:str]]:
        self.set_page(n_page=n_page)

        return self.get_posts()

    def get_posts_form_pages(self, page: list[int, int]) -> dict[str:list[dict[str:str, str:str, str:str]]]:
        # Ex of use: get_posts_form_pages(range(0, 10))

        posts_pages = {}  # Example: "page 1": [ UrlPosts ]
        for n_page in page:
            posts_pages[f"page {n_page}"] = self.get_posts_from_page(n_page)
        return posts_pages

    def get_posts_from_url(self, url: str) -> list[dict[str:str, str:str, str:str]]:
        tree = self.get_content_from_url(url)

        posts = []
        for post in tree.xpath(self.XPATH_POST_LIST)[0]:
            posts.append(self.get_postdata_from_url(f'{self.BASE_LINK}{post.xpath(self.XPATH_POST_LINK)[0]}'))
        return posts

    def get_post_from_url(self, url: str) -> dict[str:str, str:str, str:str]:
        return self.get_postdata_from_url(url)

    def get_post_from_id(self, post_id: str or int) -> dict[str:str, str:str, str:str]:
        return self.get_postdata_from_url(
            self.build_post_link(post_id)
        )

    def get_post_from_index(self, index: int) -> dict[str:str, str:str, str:str]:
        return self.get_posts_from_page()[index]

    def get_postdata_from_url(self, url: str) -> dict[str:str, str:str, str:str]:
        tree = self.get_content_from_url(url)

        link = self.tree.xpath(self.XPATH_IMAGE)  # Get image from post
        tag = self.TAG_IMAGE  # Set tag as a image

        if link.__len__() == 0:  # Prevent tag error
            link = tree.xpath(self.XPATH_VIDEO)  # Get video from post
            tag = self.TAG_VIDEO  # Set tag as a video

        if link.__len__() == 0:
            link = 'Empty'
            tag = 'NONE'

        return {
            'id': self.get_id_from_url(link[0]),
            'tag': tag,
            'source': link[0]
        }


def get_page(link: str):
    page = req.get(link,
                   headers=headers,
                   cookies=cookie, stream=True)
    # xcontent: html.HtmlElement = html.fromstring(page.content)
    return page


if __name__ == '__main__':
    pass

    #    size_box = parse_box(f)
    #    print("MajorBrand: ", str(f.read(4), encoding="utf-8"))
    #    print("MinorVersion: ", int.from_bytes(f.read(4)))
    #    if size_box > 8:
    #        for i in range(((size_box-16)//4)):
    #            print("CompatibleBrand: ", str(f.read(4), encoding="utf-8"))
#
#    size_box = parse_box(f)
#    size_box = parse_box(f)
#    print("Flags: ", int.from_bytes(f.read(4)))
#    print("Version: ", int.from_bytes(f.read(1)))
#    print("CreationTime: ", int.from_bytes(f.read(4)))
#    print("ModificationTime: ", int.from_bytes(f.read(4)))
#    time_scale = int.from_bytes(f.read(4))
#    print("Timescale: ", time_scale)
#    duration = int.from_bytes(f.read(4))
#    print("Duration: ", duration//time_scale)

# download_path = "download/"
#
# client = Gelooru()
#
# client.set_page(
#    ["custom_udon"]
# )
#
# posts_path = f"{download_path}/{" ".join(client.tags)}"
# os.makedirs(posts_path, exist_ok=True)
#
# posts_list = client.get_posts()
#
# for post in posts_list:
#    for file_size, dl_content, download_speed in download(filename=f"{posts_path}/{post["source"].split("/")[-1]}",
#                                                        url=post["source"]):
#        download_speed, type_data = scale_data(download_speed * 8)
#        print(
#            f'Downloaded: {loading_bar(dl_content, file_size, 20)} {dl_content // (file_size // 100)}% Speed: {download_speed} {type_data}/s     ',
#            end='\r')
