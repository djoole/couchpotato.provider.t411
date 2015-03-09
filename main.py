from bs4 import BeautifulSoup
from couchpotato.core.helpers.encoding import tryUrlencode
from couchpotato.core.helpers.variable import tryInt
from couchpotato.core.logger import CPLog
from couchpotato.core.media._base.providers.torrent.base import TorrentProvider
from couchpotato.core.media.movie.providers.base import MovieProvider
import traceback

log = CPLog(__name__)


class t411(TorrentProvider, MovieProvider):

    urls = {
        'test' : 'https://www.t411.io',
        'login' : 'https://www.t411.io/users/login/',
        'login_check': 'https://www.t411.io',
        'detail': 'https://www.t411.io/torrents/?id=%s',
        'search': 'https://www.t411.io/torrents/search/?search=%s %s',
        'download' : 'http://www.t411.io/torrents/download/?id=%s',
    }

    http_time_between_calls = 1 #seconds
    cat_backup_id = None

    def _searchOnTitle(self, title, movie, quality, results):

        log.debug('Searching T411 for %s' % (title))

        url = self.urls['search'] % (title.replace(':', ''), quality['identifier'])
        data = self.getHTMLData(url)

        log.debug('Received data from T411')
        if data:
            log.debug('Data is valid from T411')
            html = BeautifulSoup(data)

            try:
                result_table = html.find('table', attrs = {'class':'results'})
                if not result_table:
                    log.debug('No table results from T411')
                    return

                torrents = result_table.find('tbody').findAll('tr')
                for result in torrents:
                    idt = result.findAll('td')[2].findAll('a')[0]['href'][1:].replace('torrents/nfo/?id=','')
                    release_name = result.findAll('td')[1].findAll('a')[0]['title']
                    words = title.lower().replace(':',' ').split()
                    if self.conf('ignore_year'):
                        index = release_name.lower().find(words[-1] if words[-1] != 'the' else words[-2]) + len(words[-1] if words[-1] != 'the' else words[-2]) +1
                        index2 = index + 7
                        if not str(movie['info']['year']) in release_name[index:index2]:
                            release_name = release_name[0:index] + '(' + str(movie['info']['year']) + ').' + release_name[index:]
                    if 'the' not in release_name.lower() and (words[-1] == 'the' or words[0] == 'the'):
                        release_name = 'the.' + release_name
                    if 'multi' in release_name.lower():
                        release_name = release_name.lower().replace('truefrench','').replace('french','')
                    age = result.findAll('td')[4].text
                    results.append({
                        'id': idt,
                        'name': release_name,
                        'url': self.urls['download'] % idt,
                        'detail_url': self.urls['detail'] % idt,
                        'size': self.parseSize(str(result.findAll('td')[5].text)),
                        'seeders': result.findAll('td')[7].text,
                        'leechers': result.findAll('td')[8].text,
                    })

            except:
                log.error('Failed to parse T411: %s' % (traceback.format_exc()))

    def getLoginParams(self):
        log.debug('Getting login params for T411')
        return {
             'login': self.conf('username'),
             'password': self.conf('password'),
             'remember': '1',
             'url': '/'
        }

    def loginSuccess(self, output):
        log.debug('Checking login success for T411: %s' % ('True' if ('logout' in output.lower()) else 'False'))
        return 'logout' in output.lower()

    loginCheckSuccess = loginSuccess
