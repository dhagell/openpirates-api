from flask import Flask, abort
from flask import jsonify
from google.cloud import storage
from google.oauth2 import service_account
from PIL import Image
import os
import mimetypes

GOOGLE_STORAGE_PROJECT = os.environ['GOOGLE_STORAGE_PROJECT']
GOOGLE_STORAGE_BUCKET = os.environ['GOOGLE_STORAGE_BUCKET']

app = Flask(__name__)


########################################################################
# Data
########################################################################

# opensea-pirates

FIRST_NAMES = ['Herbie', 'Sprinkles', 'Boris', 'Dave', 'Randy', 'Captain']
LAST_NAMES = ['Starbelly', 'Fisherton', 'McCoy']

BASES = ['jellyfish', 'starfish', 'crab', 'narwhal', 'tealfish', 'goldfish']
EYES = ['big', 'joy', 'wink', 'sleepy', 'content']
MOUTH = ['happy', 'surprised', 'pleased', 'cute']
HAT = ['tricorn', 'bicorn', 'small', 'scarf','cap']
SWORD = ['cutlass', 'saber', 'scimitar', 'dagger']
GLYPHS = ['parrot', 'frog', 'snake']
GREEKSYMBOL = ['omega', 'alpha', 'beta']

INT_ATTRIBUTES = [5, 2, 3, 4, 8]
FLOAT_ATTRIBUTES = [1.4, 2.3, 11.7, 90.2, 1.2]
STR_ATTRIBUTES = [
    'Happy',
    'Sad',
    'Sleepy',
    'Boring'
]
BOOST_ATTRIBUTES = [10, 40, 30]
PERCENT_BOOST_ATTRIBUTES = [5, 10, 15]
NUMBER_ATTRIBUTES = [1, 2, 1, 1]


# opensea-pirates-treasures
ACCESSORIES_IMAGES = [
    'Bamboo-flute.png',
    'Life-ring.png',
    'Message-in-a-bottle.png',
    'Pearl.png',
    'Scuba-mask.png',
    'Trident.png'
]
ACCESSORIES_NAMES = [a.replace('-', ' ').replace('.png', '')
                     for a in ACCESSORIES_IMAGES]
ACCESSORIES_ATTS_INT = [200, 11, 3, 41, 9, 172]
ACCESSORIES_ATTS_PERCENT = [5, 10, 1, 20, 15, 25]
ACCESSORIES_ATTS_LOCATION = ['Head', 'Body', 'Held', 'Held', 'Head', 'Held']
ACCESSORIES_ATTS_RARITY = [
    'Common',
    'Rare',
    'Legendary',
    'Epic',
    'Divine',
    'Hidden'
]
ACCESSORIES_ATTS_DEPTH = [
    'beach',
    'shore',
    'shallows',
    'deeps',
    'shore',
    'deeps'
]
ACCESSORIES_ATTS_GENERATION = [1, 1, 2, 1, 1, 3]


# contractURI() support
CONTRACT_URI_METADATA = {
    'opensea-pirates': {
        'name': 'OpenSea Pirates',
        'description': 'Friendly pirates of the sea.',
        'image': 'https://example.com/image.png',
        'external_link': 'https://github.com/dhagell/opensea-pirates/'
    },
    'opensea-erc1155': {
        'name': 'OpenSea Pirate Treasures',
        'description': "Fun and useful treasures for your OpenSea pirates.",
        'image': 'https://example.com/image.png',
        'external_link': 'https://github.com/dhagell/opensea-erc1155/'
    }
}
CONTRACT_URI_METADATA_AVAILABLE = CONTRACT_URI_METADATA.keys()


########################################################################
# Routes
########################################################################

# opensea-pirates

@app.route('/api/pirate/<token_id>')
def pirate(token_id):
    token_id = int(token_id)
    num_first_names = len(FIRST_NAMES)
    num_last_names = len(LAST_NAMES)
    pirate_name = '%s %s' % (FIRST_NAMES[token_id % num_first_names], LAST_NAMES[token_id % num_last_names])

    base = BASES[token_id % len(BASES)]
    eyes = EYES[token_id % len(EYES)]
    mouth = MOUTH[token_id % len(MOUTH)]
    image_url = _compose_image(['images/bases/base-%s.png' % base,
                                'images/eyes/eyes-%s.png' % eyes,
                                'images/mouths/mouth-%s.png' % mouth],
                               token_id)

    attributes = []
    _add_attribute(attributes, 'Base', BASES, token_id)
    _add_attribute(attributes, 'Eyes', EYES, token_id)
    _add_attribute(attributes, 'Mouth', MOUTH, token_id)
    _add_attribute(attributes, 'Level', INT_ATTRIBUTES, token_id)
    _add_attribute(attributes, 'Stamina', FLOAT_ATTRIBUTES, token_id)
    _add_attribute(attributes, 'Personality', STR_ATTRIBUTES, token_id)
    _add_attribute(attributes, 'Aqua Power', BOOST_ATTRIBUTES, token_id, display_type='boost_number')
    _add_attribute(attributes, 'Stamina Increase', PERCENT_BOOST_ATTRIBUTES, token_id, display_type='boost_percentage')
    _add_attribute(attributes, 'Generation', NUMBER_ATTRIBUTES, token_id, display_type='number')


    return jsonify({
        'name': pirate_name,
        'description': 'Friendly OpenSea Pirate that enjoys a long sail in the ocean.',
        'image': image_url,
        'external_url': 'https://openseapirates.io/%s' % token_id,
        'attributes': attributes
    })


@app.route('/api/box/pirate/<token_id>')
def pirate_box(token_id):
    token_id = int(token_id)
    image_url = _compose_image(['images/box/bootybox.png'], token_id, 'box')

    attributes = []
    _add_attribute(attributes, 'number_inside', [3], token_id)

    return jsonify({
        'name': 'Pirate Booty Box',
        'description': 'This bootybox contains some OpenSea Pirates! It can also be traded!',
        'image': image_url,
        'external_url': 'https://openseapirates.io/%s' % token_id,
        'attributes': attributes
    })


@app.route('/api/factory/pirate/<token_id>')
def pirate_factory(token_id):
    token_id = int(token_id)
    if token_id == 0:
        name = 'One OpenSea Pirate'
        description = 'When you purchase this option, you will receive a single OpenSea pirate of a random variety. ' \
                      'Enjoy and take good care of your aquatic being!'
        image_url = _compose_image(['images/factory/egg.png'], token_id, 'factory')
        num_inside = 1
    elif token_id == 1:
        name = 'Four OpenSea Pirates'
        description = 'When you purchase this option, you will receive four OpenSea pirates of random variety. ' \
                      'Enjoy and take good care of your aquatic beings!'
        image_url = _compose_image(['images/factory/four-eggs.png'], token_id, 'factory')
        num_inside = 4
    elif token_id == 2:
        name = 'One OpenSea Pirate bootybox'
        description = 'When you purchase this option, you will receive one bootybox, which can be opened to reveal three ' \
                      'OpenSea pirates of random variety. Enjoy and take good care of these cute aquatic beings!'
        image_url = _compose_image(['images/box/bootybox.png'], token_id, 'factory')
        num_inside = 3

    attributes = []
    _add_attribute(attributes, 'number_inside', [num_inside], token_id)

    return jsonify({
        'name': name,
        'description': description,
        'image': image_url,
        'external_url': 'https://openseapirates.io/%s' % token_id,
        'attributes': attributes
    })


# opensea-pirates-treasures

@app.route('/api/treasure/<token_id>')
def treasure(token_id):
    token_id = int(token_id)
    num_treasures = len(ACCESSORIES_NAMES)
    if token_id >= num_treasures:
        abort(404, description='No such token')
    treasure_name = ACCESSORIES_NAMES[token_id]
    image_path = 'images/treasure/%s' % ACCESSORIES_IMAGES[token_id]
    image_url = _bucket_image(image_path, token_id, 'treasure')
    attributes = []
    _add_attribute(attributes, 'Aqua Boost', ACCESSORIES_ATTS_INT, token_id, display_type='boost_number')
    _add_attribute(attributes, 'Stamina Increase', ACCESSORIES_ATTS_PERCENT, token_id, display_type='boost_percentage')
    _add_attribute(attributes, 'Location', ACCESSORIES_ATTS_LOCATION, token_id)
    _add_attribute(attributes, 'Depth', ACCESSORIES_ATTS_DEPTH, token_id)
    _add_attribute(attributes, 'Rarity', ACCESSORIES_ATTS_RARITY, token_id)
    _add_attribute(attributes, 'Generation', ACCESSORIES_ATTS_GENERATION, token_id, display_type='number')

    return jsonify({
        'name': treasure_name,
        'description': 'A fun and useful treasure for your friendly OpenSea pirates.',
        'image': image_url,
        'external_url': 'https://openseapirates.io/treasure/%s' % token_id,
        'attributes': attributes
    })


@app.route('/api/box/treasure/<token_id>')
def treasure_box(token_id):
    token_id = int(token_id)
    image_url = _compose_image(['images/box/bootybox.png'], token_id, 'box')

    attributes = []
    _add_attribute(attributes, 'number_inside', [3], token_id)

    return jsonify({
        'name': 'Treasure Booty Box',
        'description': 'This bootybox contains some OpenSea Pirate treasures! It can also be traded!',
        'image': image_url,
        'external_url': 'https://openseapirates.io/box/treasure/%s' % token_id,
        'attributes': attributes
    })


@app.route('/api/factory/treasure/<token_id>')
def treasure_factory(token_id):
    token_id = int(token_id)
    if token_id == 0:
        name = 'One OpenSea Pirate Treasure'
        description = 'When you purchase this option, you will receive a single OpenSea pirate treasure of a random variety. ' \
                      'Enjoy and take good care of your aquatic being!'
        image_url = _compose_image(['images/factory/egg.png'], token_id, 'factory')
        num_inside = 1
    elif token_id == 1:
        name = 'Four OpenSea Pirate Treasures'
        description = 'When you purchase this option, you will receive four OpenSea pirate treasures of random variety. ' \
                      'Enjoy and take good care of your aquatic beings!'
        image_url = _compose_image(['images/factory/four-eggs.png'], token_id, 'factory')
        num_inside = 4
    elif token_id == 2:
        name = 'One OpenSea Pirate Treasure BootyBox'
        description = 'When you purchase this option, you will receive one bootybox, which can be opened to reveal three ' \
                      'OpenSea pirate treasures of random variety. Enjoy and take good care of these cute aquatic beings!'
        image_url = _compose_image(['images/box/bootybox.png'], token_id, 'factory')
        num_inside = 3

    attributes = []
    _add_attribute(attributes, 'number_inside', [num_inside], token_id)

    return jsonify({
        'name': name,
        'description': description,
        'image': image_url,
        'external_url': 'https://openseapirates.io/%s' % token_id,
        'attributes': attributes
    })


# contractURI()

@app.route('/contract/<contract_name>')
def contract_uri(contract_name):
    if not contract_name in CONTRACT_URI_METADATA_AVAILABLE:
        abort(404, description='Resource not found')
    return jsonify(CONTRACT_URI_METADATA[contract_name])


# Error handling

@app.errorhandler(404)
def resource_not_found(e):
    return jsonify(error=str(e)), 404


########################################################################
# Utility code
########################################################################

def _add_attribute(existing, attribute_name, options, token_id, display_type=None):
    trait = {
        'trait_type': attribute_name,
        'value': options[token_id % len(options)]
    }
    if display_type:
        trait['display_type'] = display_type
    existing.append(trait)


def _compose_image(image_files, token_id, path='pirate'):
    composite = None
    for image_file in image_files:
        foreground = Image.open(image_file).convert('RGBA')

        if composite:
            composite = Image.alpha_composite(composite, foreground)
        else:
            composite = foreground

    output_path = 'images/output/%s.png' % token_id
    composite.save(output_path)

    blob = _get_bucket().blob(f'{path}/{token_id}.png')
    blob.upload_from_filename(filename=output_path)
    return blob.public_url


def _bucket_image(image_path, token_id, path='treasure'):
    blob = _get_bucket().blob(f'{path}/{token_id}.png')
    blob.upload_from_filename(filename=image_path)
    return blob.public_url


def _get_bucket():
    credentials = service_account.Credentials.from_service_account_file('credentials/google-storage-credentials.json')
    if credentials.requires_scopes:
        credentials = credentials.with_scopes(['https://www.googleapis.com/auth/devstorage.read_write'])
    client = storage.Client(project=GOOGLE_STORAGE_PROJECT, credentials=credentials)
    return client.get_bucket(GOOGLE_STORAGE_BUCKET)

@app.route("/")
def home():
    return render_template('index.html')
	
	
	
########################################################################
# Main flow of execution
########################################################################

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
