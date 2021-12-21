from anicli_ru import Anime
from anicli_ru.utils import kodik_decoder
import re


class Anime2(Anime):
    BASE_URL = "https://animania.online/index.php"

    def search(self, q: str):
        r = self.request_get(self.BASE_URL, params=dict(do="search", subaction="search", story=q))
        results = re.findall(r'<a class="short-poster img-box" href="(.*?\.html)" data-title=".*?: (.*?)"', r.text)
        return results

    def ongoing(self):
        r = self.request_get(self.BASE_URL)
        results = re.findall(r'<a class="ksupdate_block_list_link" href="(.*?)">(.*?)</a>', r.text)
        results_eps = re.findall(r'<span class="cell cell-\d"><a href=".*?">(.*?)</a></span>', r.text)
        return results, results_eps

    def episodes(self, url):
        r = self.request_get(url)
        dubs = re.findall(r"""onclick="kodikSlider\.season\('(\d+)', this\)" style="display:none;">(.*?)</span>""",
                          r.text)
        re_video = re.compile(r"""<span onclick="kodikSlider\.player\('(.*?)', this\);">""")
        videos_chunks = re.findall(
            r"""(<li id="season\d+" style="display:none;">(<span onclick="kodikSlider\.player\('.*?', this\);"> .*?</span>){1,})""",
            r.text)
        info = list(zip(
            [n[0] for n in dubs],
            [n[1] for n in dubs],
            [re.findall(re_video, c[0]) for c in videos_chunks]
        ))
        return info


if __name__ == '__main__':
    pass
