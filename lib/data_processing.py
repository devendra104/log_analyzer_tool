from pymongo import MongoClient


def extracting_build_info(search_type=None, data_selection=None):
    connection = MongoClient()
    db = connection.test_database1
    collections = db.files
    if search_type:
        if type(data_selection) == 'str':
            fs = collections.find({'{}'.format(search_type): '{}'.format(data_selection)})
        else:
            fs = collections.find({'{}'.format(search_type): data_selection})
    else:
        fs = collections.find()
    connection.close()
    return fs
