from .main import t411

def autoload():
    return t411()

config = [{
    'name': 't411',
    'groups': [
        {
            'tab': 'searcher',
            'list': 'torrent_providers',
            'name': 't411',
            'description': 'See <a href="https://www.t411.ai/">T411</a>',
            'icon': 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAc5JREFUOI3tkk9IU3EAxz/vrbWeb+/NNdtmBS5kEHWwYfYHKulWCbtIh4i8JAYN6pRReKwMiooOElEGYkllUIgVTBhZRGHRKnBbaeGyOf+smshLeO/56xCMvHcJ+ty+l8/h+/3Cf6Q/w4VPYtvrkZk2c/DRzlQmbc3ajiKKnvvpC05MBcIfWb/5PTJ9RKWZRYJoUkRS77Ld+eL8Os/YMOM3z8PEKI1HY0xNFngaH6KuPsKHOShaNljSArUNLVxsuP5bc3zwTfuDpKB2n6CpQ0C12NIYE32js6L9dkK0nOkUL6dtUVW3W1xKpMX+1rOCrbEXADLAhuzA2ubtIfaEVDBtwMmRE8foudFNua5x9VQXd/oHKFNU4re6WOHR4cd0uCRI9vRa8VfDPLx3DZxOmtoO4xSCTRtrUL1eMDIEdRVddaNrOj6tDITDLAmg8DZvLyN66CQ4ZNLjBRLPhviay2MYBlBBld+Dx1OOoigskSQIrMyUStz7WKh3Tzf3OueKu8yaerBMiN+nsno1a1b5eZ7Konl9GO7laEtdVLqVsW8uf2yy82D/ohlb04LL5zquzAfDO8h/XkB2fEd25fAGvqBWpAhFnnBAGvm7T/r3+QVQzKvI28pwFwAAAABJRU5ErkJggg==',
            'wizard': True,
            'options': [
                {
                    'name': 'enabled',
                    'type': 'enabler',
                    'default': False,
                },
                {
                    'name': 'username',
                    'default': '',
                },
                {
                    'name': 'password',
                    'default': '',
                    'type': 'password',
                },
                {
                    'name': 'ignore_year',
                    'label': 'ignore year',
                    'default': 0,
                    'type': 'bool',
                    'description': 'Will ignore the year in the search results',
                },
                {
                    'name': 'multi',
                    'label': 'ignore lang in multi',
                    'default': 0,
                    'type': 'bool',
                    'description': 'Will ignore "french" and "truefrench" if "multi" is detected',

                },
                {
                    'name': 'seed_ratio',
                    'label': 'Seed ratio',
                    'type': 'float',
                    'default': 1,
                    'description': 'Will not be (re)moved until this seed ratio is met.',
                },
                {
                    'name': 'seed_time',
                    'label': 'Seed time',
                    'type': 'int',
                    'default': 40,
                    'description': 'Will not be (re)moved until this seed time (in hours) is met.',
                },
                {
                    'name': 'extra_score',
                    'advanced': True,
                    'label': 'Extra Score',
                    'type': 'int',
                    'default': 20,
                    'description': 'Starting score for each release found via this provider.',
                }
            ],
        },
    ],
}]
