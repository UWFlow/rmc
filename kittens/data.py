import os
import json

data_path = os.path.join(os.path.dirname(__file__), 'data.json')


def _get_kitten_data():
    kitten_file = open(data_path, 'r')
    kitten_data = json.load(kitten_file)
    kitten_file.close()
    return kitten_data


def count_kittens():
    return len(_get_kitten_data())


def add_kitten_data(new_flickr_info):
    """Add the provided flickr API response info to the data list.

    If it's already in the data list, update it.

    Return the index of the data in the list.
    """
    kitten_data = _get_kitten_data()

    for (i, kitten_info) in enumerate(kitten_data):
        if kitten_info['id'] == new_flickr_info['id']:
            kitten_data[i] = new_flickr_info
            index = i
            break
    else:
        # Break didn't hit, the photo info is new
        index = len(kitten_data)
        kitten_data.append(new_flickr_info)

    kitten_file = open(data_path, 'w')
    json.dump(kitten_data, kitten_file, indent=2)
    kitten_file.close()
    return index
