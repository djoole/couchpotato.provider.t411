#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
A module to use Allocine API V3 in Python
Base on work from: http://wiki.gromez.fr/dev/api/allocine_v3
Forked from : https://github.com/xbgmsharp/allocine (by Francois Lacroix)
License : GPL

Sample code:

    from allocine import allocine
    api = allocine()
    search = api.search("Harry Potter")

"""

from datetime import date
import urllib2, urllib
import hashlib, base64
import json

__description__ = "A module to use Allocine API V3 in Python"

class allocine(object):
    """An interface to the Allocine API"""
    def __init__(self):
        """Init values"""
        self._api_url = 'http://api.allocine.fr/rest/v3'
        self._partner_key  = 'aXBob25lLXYy'
        self._secret_key = '29d185d98c984a359e6e6f26a0474269'
        self._user_agent = 'AlloCine/2.9.5 CFNetwork/548.1.4 Darwin/11.0.0'

    def _do_request(self, params=None):
        """Generate and send the request"""
        # build the URL
        query_url = self._api_url+'/search';

        # create signature to ask allocine api
        sed = date.today().strftime('%Y%m%d')
        sha1 = hashlib.sha1(self._secret_key+urllib.urlencode(params)+'&sed='+sed).digest()
        sig = urllib2.quote(base64.b64encode(sha1))

        query_url += '?'+urllib.urlencode(params)+'&sed='+sed+'&sig='+sig

        # do the request
        req = urllib2.Request(query_url)
        req.add_header('User-agent', self._user_agent)

        response = json.load(urllib2.urlopen(req, timeout = 6))

        return response;
    
    def search(self, query):
        """Search for a term
        Param:
            query -- Term to search for
        """
        # build the params
        params = {}
        params['format'] = 'json'
        params['partner'] = self._partner_key
        params['q'] = query
        params['filter'] = "movie"

        # do the request
        response = self._do_request(params);

        return response;
