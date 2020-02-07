import bson
from pymongo import MongoClient


def get_db_connection(db_name=None):
    """
    :param db_name:
    :return:
    """
    connection = MongoClient()[db_name]
    return connection


def extracting_build_info(job_name=None, build_number=None,
                          component_version=None):
    """
    :param job_name:
    :param build_number:
    :param component_version:
    :return:
    """
    db = get_db_connection(db_name="test_database1")
    collections = db.files
    if job_name and build_number and component_version:
        fs = collections.find({"Job-Name": '{}'.format(job_name),
                               "Build-Number": '{}'.format(build_number),
                               "Build-Version": "{}".format(component_version)})
    elif job_name and (not (build_number and component_version)):
        fs = collections.find({"Job-Name": '{}'.format(job_name)})
    return fs


def extracting_data_by_field(field_name=None, field_value=None):
    """
    :param field_name:
    :param field_value:
    :return:
    """
    db = get_db_connection(db_name="test_database1")
    collections = db.files
    fs = collections.find({"{}".format(field_name): "{}".format(field_value)})
    return fs


def regex_data_retrieval(job_name):
    """
    :param job_name:
    :return:
    """
    db = get_db_connection(db_name="test_database1")
    collections = db.files
    fs = collections.find({'Job-Name': {'$regex': '{}'.format(job_name)}})
    return fs


def accessing_data_via_id(build_id=None):
    """
    :param build_id:
    :return:
    """
    db = get_db_connection(db_name="test_database1")
    collections = db.files
    fs = collections.find({"_id": bson.ObjectId("{}".format(build_id))})
    return fs


def accessing_all_data():
    """
    :return:
    """
    db = get_db_connection(db_name="test_database1")
    collections = db.files
    fs = collections.find()
    return fs


def delete_record(build_id=None):
    """
    :param id:
    :return:
    """
    db = get_db_connection(db_name="test_database1")
    collections = db.files
    fs = collections.deleteOne({"_id": bson.ObjectId("{}".format(build_id))})
    return fs


def update_record(build_id=None, old_record=None, new_record=None):
    """
    :return:
    """
    db = get_db_connection(db_name="test_database1")
    collections = db.files
    query = {"_id": bson.ObjectId("{}".format(build_id))}
    new_value = {"$set": old_record}
    collections.update(query, new_value)


def accessing_observation_db():
    db = get_db_connection(db_name="observation_record_db")
    collections = db.files
    fs = collections.find()
    return fs
