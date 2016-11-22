# coding: utf8
from bs4 import BeautifulSoup
from couchpotato.core.helpers.encoding import tryUrlencode
from couchpotato.core.helpers.variable import tryInt
from couchpotato.core.logger import CPLog
from couchpotato.core.media._base.providers.torrent.base import TorrentProvider
from couchpotato.core.media.movie.providers.base import MovieProvider
import traceback
import urllib2
import json
import sys
import urllib

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
        'test' : 'https://www.t411.li',
        'login' : 'https://www.t411.li/users/login/',
        'login_check': 'https://www.t411.li',
        'detail': 'https://www.t411.li/torrents/?id=%s',
        'search': 'https://www.t411.li/torrents/search/?search=%s %s',
        'download' : 'http://www.t411.li/torrents/download/?id=%s',
    }

    http_time_between_calls = 1 #seconds
    cat_backup_id = None

    def _searchOnTitle(self, title, movie, quality, results):

        #log.debug ('-----------------------------')
        #log.debug('a debug speech just to show that there is a problem with the function debug for displaying titles with accents. Ex below show the problem for movie Les Associés')
        #log.debug('ddd ' + title)
        #log.debug('sss ' + title)
        #log.debug ('-----------------------------')

        #log.debug('encoding du terminal stdin : ' + sys.stdin.encoding)
        #log.debug('encoding du terminal stdout : ' + sys.stdin.encoding)
        #log.debug('encoding du filesystem : ' + sys.getfilesystemencoding())

        # test the new title and search for it if valid
        newTitle = self.getFrenchTitle(title, str(movie['info']['year']))
        request = ''
        if isinstance(title, str):
            title = title.decode('utf8')
        if newTitle is not None:
            request = (u'(' + title + u')|(' + newTitle + u')').replace(':', '')
        else:
            request = title.replace(':', '')
        request = urllib2.quote(request.encode('iso-8859-1'))

        log.debug('Looking on T411 for movie named %s or %s' % (title, newTitle))
        url = self.urls['search'] % (request, acceptableQualityTerms(quality))
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
                    #if 'the' not in release_name.lower() and (words[-1] == 'the' or words[0] == 'the'):
                    #    release_name = 'the.' + release_name
                    if 'multi' in release_name.lower():
                        release_name = release_name.lower().replace('truefrench','').replace('french','')
                    age = result.findAll('td')[4].text
                    log.debug('result : name=%s, detail_url=%s' % (replaceTitle(release_name, title, newTitle), (self.urls['detail'] % idt)))
                    results.append({
                        'id': idt,
                        'name': replaceTitle(release_name, title, newTitle),
                        'url': self.urls['download'] % idt,
                        'detail_url': self.urls['detail'] % idt,
                        'age' : age,
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

    def getFrenchTitle(self, title, year):
        """
        This function uses TMDB API to get the French movie title of the given title.
        """

        url = "https://api.themoviedb.org/3/search/movie?api_key=0f3094295d96461eb7a672626c54574d&language=fr&query=%s" % title
        log.debug('Looking on TMDB for French title of : ' + title)
        #data = self.getJsonData(url, decode_from = 'utf8')
        data = self.getJsonData(url)
        try:
            if data['results'] != None:
                for res in data['results']:
                    yearI = res['release_date']
                    if year in yearI:
                        break
                frTitle = res['title'].lower()
                if frTitle == title:
                    log.debug('TMDB report identical FR and original title')
                    return None
                else:
                    log.debug(u'L\'API TMDB a trouvé un titre français => ' + frTitle)
                    return frTitle
            else:
                log.debug('TMDB could not find a movie corresponding to : ' + title)
                return None
        except:
            log.error('Failed to parse TMDB API: %s' % (traceback.format_exc()))

def acceptableQualityTerms(quality):
    """
    This function retrieve all the acceptable terms for a quality (eg hdrip and bdrip for brrip)
    Then it creates regex accepted by t411 to search for one of this term

    t411 have to handle alternatives as OR and then the regex is firstAlternative|secondAlternative
    
    In alternatives, there can be "doubled terms" as "br rip" or "bd rip" for brrip
    These doubled terms have to be handled as AND and are then (firstBit&secondBit) 
    """
    alternatives = quality.get('alternative', [])
    # first acceptable term is the identifier itself
    acceptableTerms = [quality['identifier']]
    log.debug('Requesting alternative quality terms for : ' + str(acceptableTerms) )
    # handle single terms
    acceptableTerms.extend([ term for term in alternatives if type(term) == type('') ])
    # handle doubled terms (such as 'dvd rip')
    doubledTerms = [ term for term in alternatives if type(term) == type(('', '')) ]
    acceptableTerms.extend([ '('+first+'%26'+second+')' for (first,second) in doubledTerms ])
    # join everything and return
    log.debug('Found alternative quality terms : ' + str(acceptableTerms).replace('%26', ' '))
    return '|'.join(acceptableTerms)

def replaceTitle(releaseNameI, titleI, newTitleI):
    """
    This function is replacing the title in the release name by the old one,
    so that couchpotato recognise it as a valid release.
    """
    
    if newTitleI is None: # if the newTitle is empty, do nothing
        return releaseNameI
    else:
        # input as lower case
        releaseName = releaseNameI.lower()
        title = titleI.lower()
        newTitle = newTitleI.lower()
        log.debug('Replacing -- ' + newTitle + ' -- in the release -- ' + releaseName + ' -- by the original title -- ' + title)
        separatedWords = []
        for s in releaseName.split(' '):
            separatedWords.extend(s.split('.'))
        # test how far the release name corresponds to the original title
        index = 0
        while separatedWords[index] in title.split(' '):
            index += 1
        # test how far the release name corresponds to the new title
        newIndex = 0
        while separatedWords[newIndex] in newTitle.split(' '):
            newIndex += 1
        # then determine if it correspoinds to the new title or old title
        if index >= newIndex:
            # the release name corresponds to the original title. SO no change needed
            log.debug('The release name is already corresponding. Changed nothing.')
            return releaseNameI
        else:
            # otherwise, we replace the french title by the original title
            finalName = [title]
            finalName.extend(separatedWords[newIndex:])
            newReleaseName = ' '.join(finalName)
            log.debug('The new release name is : ' + newReleaseName)
            return newReleaseName
