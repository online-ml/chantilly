import contextlib
import os
import random
import shelve
import typing

import creme.base
import creme.metrics
import creme.utils
import flask

from . import exceptions
from . import flavors


def get_shelf() -> shelve.Shelf:
    if 'shelf' not in flask.g:
        flask.g.shelf = shelve.open(flask.current_app.config['SHELVE_PATH'])
    return flask.g.shelf


def close_shelf(e=None):
    shelf = flask.g.pop('shelf', None)

    if shelf is not None:
        shelf.close()


def drop_db():

    # Delete the current shelf if it exists
    with contextlib.suppress(FileNotFoundError):
        os.remove(f"{flask.current_app.config['SHELVE_PATH']}.db")


def set_flavor(flavor: str):

    drop_db()

    try:
        flavor = {f().name: f() for f in [flavors.RegressionFlavor]}[flavor]
    except KeyError:
        raise exceptions.UnknownFlavor

    shelf = get_shelf()
    shelf['flavor'] = flavor

    reset_metrics()


def reset_metrics():

    shelf = get_shelf()
    try:
        flavor = shelf['flavor']
    except KeyError:
        raise exceptions.FlavorNotSet

    shelf['metrics'] = flavor.default_metrics()


def add_model(model: creme.base.Estimator, name: str = None) -> str:

    shelf = get_shelf()

    # Pick a name if none is given
    if name is not None:
        while True:
            name = _random_name()
            if f'models/{name}' not in shelf:
                break

    shelf['models/{name}'] = model

    return name


def delete_model(name: str):
    shelf = get_shelf()
    del shelf['models/{name}']


def _random_name() -> str:
    return f'{random.choice(ADJECTIVES)}-{random.choice(NAMES)}'


NAMES = [
    'apple',
    'apricot',
    'avocado',
    'banana',
    'bean',
    'blackberry',
    'blackcurrant',
    'blueberry',
    'boysenberry',
    'cherry',
    'coconut',
    'couscous',
    'fig',
    'grape',
    'grapefruit',
    'hummus',
    'kiwi',
    'lemon',
    'lime',
    'lychee',
    'mandarin',
    'mango',
    'melon',
    'nectarine',
    'orange',
    'papaya',
    'passion',
    'peach',
    'pear',
    'pineapple',
    'pizza',
    'porridge',
    'plum',
    'pomegranate',
    'quince',
    'raspberry',
    'ratatouille',
    'samosa',
    'strawberry',
    'sushi',
    'watermelon',
    'weetabix'
]

ADJECTIVES = [
    'abhorrent',
    'ablaze',
    'abnormal',
    'abrasive',
    'acidic',
    'alluring',
    'ambiguous',
    'amuck',
    'apathetic',
    'aquatic',
    'auspicious',
    'axiomatic',
    'barbarous',
    'bawdy',
    'belligerent',
    'berserk',
    'bewildered',
    'billowy',
    'boorish',
    'brainless',
    'bustling',
    'cagey',
    'calculating',
    'callous',
    'capricious',
    'ceaseless',
    'chemical',
    'chivalrous',
    'cloistered',
    'coherent',
    'colossal',
    'combative',
    'cooing',
    'cumbersome',
    'cynical',
    'daffy',
    'damaged',
    'deadpan',
    'deafening',
    'debonair',
    'decisive',
    'defective',
    'defiant',
    'demonic',
    'delerious',
    'deranged',
    'devilish',
    'didactic',
    'diligent',
    'direful',
    'disastrous',
    'disillusioned',
    'dispensable',
    'divergent',
    'domineering',
    'draconian',
    'dynamic',
    'earsplitting',
    'earthy',
    'eatable',
    'efficacious',
    'elastic',
    'elated',
    'elfin',
    'elite',
    'enchanted',
    'endurable',
    'erratic',
    'ethereal',
    'evanescent',
    'exuberant',
    'exultant',
    'fabulous',
    'fallacious',
    'fanatical',
    'fearless',
    'feeble',
    'feigned',
    'fierce',
    'flagrant',
    'fluttering',
    'frantic',
    'fretful',
    'fumbling',
    'furtive',
    'gainful',
    'gamy',
    'garrulous',
    'gaudy',
    'glistening',
    'grandiose',
    'grotesque',
    'gruesome',
    'guiltless',
    'guttural',
    'habitual',
    'hallowed',
    'hapless',
    'harmonious',
    'hellish',
    'hideous',
    'highfalutin',
    'hissing',
    'holistic',
    'hulking',
    'humdrum',
    'hypnotic',
    'hysterical',
    'icky',
    'idiotic',
    'illustrious',
    'immense',
    'immenent',
    'incandescent',
    'industrious',
    'infamous',
    'inquisitive',
    'insidious',
    'invincible',
    'jaded',
    'jazzy',
    'jittery',
    'judicious',
    'jumbled',
    'juvenile',
    'kaput',
    'keen',
    'knotty',
    'knowing',
    'lackadaisical',
    'lamentable',
    'languid',
    'lavish',
    'lewd',
    'longing',
    'loutish',
    'ludicrous',
    'lush',
    'luxuriant',
    'lyrical',
    'macabre',
    'maddening',
    'mammoth',
    'maniacal',
    'meek',
    'melodic',
    'merciful',
    'mere',
    'miscreant',
    'momentous',
    'nappy',
    'nebulous',
    'nimble',
    'nippy',
    'nonchalant',
    'nondescript',
    'noxious',
    'numberless',
    'oafish',
    'obeisant',
    'obsequious',
    'oceanic',
    'omniscient',
    'onerous',
    'optimal',
    'ossified',
    'overwrought',
    'paltry',
    'parched',
    'parsimonious',
    'penitent',
    'perpetual',
    'picayune',
    'piquant',
    'placid',
    'plucky',
    'prickly',
    'probable',
    'profuse',
    'psychedelic',
    'quack',
    'quaint',
    'quarrelsome',
    'questionable',
    'quirky',
    'quixotic',
    'quizzical',
    'rabbid',
    'rambunctious',
    'rampat',
    'raspy',
    'recondite',
    'resolute',
    'rhetorical',
    'ritzy',
    'ruddy',
    'sable',
    'sassy',
    'savory',
    'scandalous',
    'scintillating',
    'sedate',
    'shaggy',
    'shrill',
    'smoggy',
    'somber',
    'sordid',
    'spiffy',
    'spurious',
    'taboo',
    'tacit',
    'tangy',
    'tawdry',
    'tedious',
    'tenuous',
    'testy',
    'thundering',
    'ubiquitous',
    'ultra',
    'unwieldy',
    'uppity',
    'utopian',
    'utter',
    'vacuous',
    'vagabond',
    'vengeful',
    'venomous',
    'verdant',
    'versed',
    'victorious',
    'vigorous',
    'vivacious',
    'voiceless',
    'volatile',
    'voracious',
    'vulgar',
    'wacky',
    'waggish',
    'wakeful',
    'warlike',
    'wary',
    'whimsical',
    'whispering',
    'wiggly',
    'wiry',
    'wistful',
    'woebegone',
    'woozy',
    'wrathful',
    'wretched',
    'wry',
    'yummy',
    'yappy',
    'yielding',
    'zany',
    'zazzy',
    'zealous',
    'zesty',
    'zippy',
    'zoetic',
    'zoic',
    'zonked'
]
