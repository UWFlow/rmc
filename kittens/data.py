import os
import json

data_path = os.path.join(os.path.dirname(__file__), 'data.json')


def get_kitten_data():
    with open(data_path, 'r') as kitten_file:
        return json.load(kitten_file)


def add_kitten_data(new_flickr_info):
    """Add the provided flickr API response info to the data list.

    If it's already in the data list, update it.

    Return the index of the data in the list.
    """
    kitten_data = get_kitten_data()

    for (i, kitten_info) in enumerate(kitten_data):
        if kitten_info['id'] == new_flickr_info['id']:
            kitten_data[i] = new_flickr_info
            index = i
            break
    else:
        # Break didn't hit, the photo info is new
        index = len(kitten_data)
        kitten_data.append(new_flickr_info)

    with open(data_path, 'w') as kitten_file:
        json.dump(kitten_data, kitten_file, indent=2)

    return index
