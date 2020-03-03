import bson
from utils.common import Common
from pymongo import MongoClient

DB_CONFIG = Common.validation_param_detail("environment_setup.yaml", "config")


def get_db_connection(db_name=None):
    """
    :param db_name:
    :return:
    """
    connection = MongoClient(host=DB_CONFIG["mongodb_container"],
                             port=DB_CONFIG["mongodb_port"])[db_name]
    return connection


def extracting_build_info(job_name=None, build_number=None,
                          component_version=None):
    """
    :param job_name:
    :param build_number:
    :param component_version:
    :return:
    """
    db = get_db_connection(db_name=DB_CONFIG["database_name"])
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
    db = get_db_connection(db_name=DB_CONFIG["database_name"])
    collections = db.files
    fs = collections.find({"{}".format(field_name): "{}".format(field_value)})
    return fs


def regex_data_retrieval(job_name):
    """
    :param job_name:
    :return:
    """
    db = get_db_connection(db_name=DB_CONFIG["database_name"])
    collections = db.files
    fs = collections.find({'Job-Name': {'$regex': '{}'.format(job_name)}})
    return fs


def accessing_data_via_id(build_id=None):
    """
    :param build_id:
    :return:
    """
    db = get_db_connection(db_name=DB_CONFIG["database_name"])
    collections = db.files
    fs = collections.find({"_id": bson.ObjectId("{}".format(build_id))})
    return fs


def accessing_all_data(check_before_insert=False):
    """
    :return:
    """
    db = get_db_connection(db_name=DB_CONFIG["database_name"])
    collections = db.files
    if check_before_insert:
        return collections
    fs = collections.find()
    return fs


def delete_record(build_id=None):
    """
    :param id:
    :return:
    """
    db = get_db_connection(db_name=DB_CONFIG["database_name"])
    collections = db.files
    fs = collections.delete_one({"_id": bson.ObjectId("{}".format(build_id))})
    return fs


def update_record(build_id=None, old_record=None):
    """
    :return:
    """
    db = get_db_connection(db_name=DB_CONFIG["database_name"])
    collections = db.files
    query = {"_id": bson.ObjectId("{}".format(build_id))}
    new_value = {"$set": old_record}
    collections.update(query, new_value)


def accessing_observation_db(check_before_insert=False):
    db = get_db_connection(db_name=DB_CONFIG["observation_db_name"])
    collections = db.files
    if check_before_insert:
        return collections
    fs = collections.find()
    return fs


def db_update(test_data=None, observation_record_key=None, observation_record_value=None):
    """
    This method use to update the log analysis database whenever new record come
    :param dict test_data:
    :param str observation_record_key:
    :param str observation_record_value:
    """
    if observation_record_key and observation_record_value:
            data_status = check_before_insertion(
                 observation_record_key=observation_record_key,
                 observation_record_value=observation_record_value)
    else:
        data_status = check_before_insertion(
            build_no=test_data["Build-Number"],
            job_name=test_data["Job-Name"],
            component_version=test_data["Build-Version"],
            snap_number=test_data["Snap-Version"])
    status = True if data_status else False
    if status:
        return

    if observation_record_key and observation_record_value:
        collections = accessing_observation_db(check_before_insert=True)
    else:
        collections = accessing_all_data(check_before_insert=True)

    if observation_record_key and observation_record_value:
        collections.insert({"{}".format(
            observation_record_key): "{}".format(observation_record_value)})
    else:
        collections.insert(test_data)


def check_before_insertion(observation_record_key=None,
                           observation_record_value=None, build_no=None, job_name=None
                           , component_version=None, snap_number=None):
    """
    This method use to check whether the record present or not and return their
    status.
    :param int build_no:
    :param string job_name:
    :param string component_version:
    :param string snap_number:
    :param str observation_record_key:
    :param str observation_record_value:
    :return: status
    """
    if observation_record_key and observation_record_value:
        collections = accessing_observation_db(check_before_insert=True)
    else:
        collections = accessing_all_data(check_before_insert=True)

    if observation_record_key and observation_record_value:
        fs = collections.find({"{}".format(observation_record_key):
                               "{}".format(observation_record_value)})
    else:
        fs = collections.find(
            {'Build-Number': build_no, 'Job-Name': '{}'.format(job_name),
             "Build-Version": "{}".format(component_version),
             "Snap-Version": "{}".format(snap_number)})
    status = True if fs.count() > 0 else False
    return status
