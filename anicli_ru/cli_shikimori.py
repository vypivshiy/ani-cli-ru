from .shikimori import ShikimoriAPI

class ShikimoriCli:

    def __init__(self):
        self.client = ShikimoriAPI('Api Test',
                                   client_id='bce7ad35b631293ff006be882496b29171792c8839b5094115268da7a97ca34c',
                                   client_secret='811459eada36b14ff0cf0cc353f8162e72a7d6e6c7930b647a5c587d1beffe68')
        self.whoami = self.client.users.whoami().json()
        self.AnimeObj = None
        self.info = None
        if self.whoami:
            nickname = self.whoami['nickname']
            print('Вы автоизованы как', nickname)

    def search(self, keyword: str = None, limit: int = 20, page: int = 1):
        if keyword != None:
            params = {'search': keyword, 'limit': limit, 'page': page}
            search_list = self.client.animes.index(params=params).json()
            self.print_results(search_list, 1)
            choise = input('choise > ')
            if choise == ':r':
                return
            elif choise.isdigit():
                self.AnimeObj = search_list[int(choise)]
                self.get_info()
            else:
                print('Command not found.')
        else:
            keyword = input('s > ')
            self.search(keyword)

    def print_results(self, results, result_type: int):
        # anime search
        if result_type == 1:
            for i, anime in enumerate(results):
                russian = anime.get('russian')
                name = anime.get('name')
                print('[{}] {} | {}'.format(i, russian, name))
        # history
        elif result_type == 2:
            for i, anime in enumerate(results):
                anime_id = anime.get('target').get('id')
                desc = anime.get('description')
                russian = anime.get('target').get('russian')
                name = anime.get('target').get('name')
                print('[{}] {} | {} \n - {}'.format(i, russian, name, desc))
        # rates
        elif result_type == 3:
            if isinstance(results, list):
                for anime in results:
                    print('Episode: {}'.format(anime.get('episodes')))
            else:
                self.user_rate = results
                status = results.get('status')
                episodes = results.get('episodes')
                rewatches = results.get('rewatches')
                score = results.get('score') or 'Нет оценки'
                text = results.get('text') or 'Нет инфы'
                print(f'Status: {status}\nEpisodes: {episodes}\nRewatches: {rewatches}\nMy score: {score}\nText: {text}')
                # print('Episode: {}'.format(results.get('episodes')))

    def get_info(self):
        if self.AnimeObj:
            info = self.client.animes.show(self.AnimeObj.get('id')).json()
            self.info = info
            get = [
                ('name', 'Title:'),
                ('russian', 'Title rus:'),
                ('description', 'Description:'),
                ('episodes', 'Episodes:'),
                ('score', 'Score:')
            ]
            for get, pname in get:
                i = info.get(get)
                print(pname, i)

            user_rate = info.get('user_rate')
            if user_rate:
                self.print_results(user_rate, 3)
        else:
            print('no AnimeObj')

    def get_history(self, limit: int = 20, page: int = 1):
        if not self.whoami:
            print('Для этого действия нужна авторизация.')
            return
        params = {'limit': limit, 'page': page}
        history_list = self.client.users.history(self.whoami['id'], params=params).json()
        self.print_results(history_list, 2)
