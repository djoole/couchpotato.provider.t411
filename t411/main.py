from bs4 import BeautifulSoup
from couchpotato.core.helpers.encoding import tryUrlencode
from couchpotato.core.helpers.variable import tryInt
from couchpotato.core.logger import CPLog
from couchpotato.core.media._base.providers.torrent.base import TorrentProvider
from couchpotato.core.media.movie.providers.base import MovieProvider
import traceback

log = CPLog(__name__)

import ast
import operator

_binOps = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.div,
    ast.Mod: operator.mod
}


def _arithmeticEval(s):
    """
    A safe eval supporting basic arithmetic operations.

    :param s: expression to evaluate
    :return: value
    """
    node = ast.parse(s, mode='eval')

    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        elif isinstance(node, ast.Str):
            return node.s
        elif isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.BinOp):
            return _binOps[type(node.op)](_eval(node.left), _eval(node.right))
        else:
            raise Exception('Unsupported type {}'.format(node))

    return _eval(node.body)


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

        if 'confirmer le captcha' in output.lower():
            log.debug('Too many login attempts. A captcha is displayed.')
            output = self._solveCaptcha(output)

        return 'logout' in output.lower()

    def _solveCaptcha(self, output):
        """
        When trying to connect too many times with wrong password, a captcha can be requested.
        This captcha is really simple and can be solved by the provider.

        <label for="pass">204 + 65 = </label>
            <input type="text" size="40" name="captchaAnswer" id="lgn" value=""/>
            <input type="hidden" name="captchaQuery" value="204 + 65 = ">
            <input type="hidden" name="captchaToken" value="005d54a7428aaf587460207408e92145">
        <br/>

        :param output: initial login output
        :return: output after captcha resolution
        """
        html = BeautifulSoup(output)

        query = html.find('input', {'name': 'captchaQuery'})
        token = html.find('input', {'name': 'captchaToken'})
        if not query or not token:
            log.error('Unable to solve login captcha.')
            return output

        query_expr = query.attrs['value'].strip('= ')
        log.debug(u'Captcha query: ' + query_expr)
        answer = _arithmeticEval(query_expr)

        log.debug(u'Captcha answer: %s' % answer)

        login_params = self.getLoginParams()

        login_params['captchaAnswer'] = answer
        login_params['captchaQuery'] = query.attrs['value']
        login_params['captchaToken'] = token.attrs['value']

        return self.urlopen(self.urls['login'], data = login_params)

    loginCheckSuccess = loginSuccess
