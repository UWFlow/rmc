import rmc.shared.constants as c
import rmc.models as m
import rmc.data.evals.conversion as conv

import mongoengine as me
import sys


def import_all_critiques(eng_file):
    m.CritiqueCourse.objects._collection.drop()
    conv.import_engineering_critiques(eng_file)

if __name__ == '__main__':
    if (len(sys.argv) < 2):
        print 'Please pass the Eng data filename as the first Argument'
        sys.exit()
    me.connect(c.MONGO_DB_RMC, host=c.MONGO_HOST, port=c.MONGO_PORT)

    eng_file = open(sys.argv[1], 'r')
    import_all_critiques(eng_file)
