import bson
from pymongo import MongoClient
from utils.common import Common

DB_CONFIG = Common.validation_param_detail("environment_setup.yaml", "config")


def get_db_connection(db_name=None):
    """
    :param db_name:
    :return:
    """
    try:
        connection = MongoClient(
            host=DB_CONFIG["mongodb_container"], port=DB_CONFIG["mongodb_port"]
        )[db_name]
        return connection
    except Exception as ex:
        Common.logger.info(f"Failed to stabilised the DB connection: {ex}")
        return


def extracting_build_info(job_name=None, build_number=None, component_version=None):
    """
    :param job_name:
    :param build_number:
    :param component_version:
    :return:
    """
    db = get_db_connection(db_name=DB_CONFIG["database_name"])
    collections = db.files
    try:
        if job_name and build_number and component_version:
            fs = collections.find(
                {
                    "Job-Name": f"{job_name}",
                    "Build-Number": f"{build_number}",
                    "Build-Version": f"{component_version}",
                }
            )
        elif job_name and (not (build_number and component_version)):
            fs = collections.find({"Job-Name": f"{job_name}"})
        return fs
    except Exception as ex:
        Common.logger.warning(f"Failed to extract build information: {ex}")


def extracting_data_by_field(field_name=None, field_value=None):
    """
    :param field_name:
    :param field_value:
    :return:
    """
    db = get_db_connection(db_name=DB_CONFIG["database_name"])
    collections = db.files
    fs = collections.find({f"{field_name}": f"{field_value}"})
    return fs


def regex_data_retrieval(job_name):
    """
    :param job_name:
    :return:
    """
    db = get_db_connection(db_name=DB_CONFIG["database_name"])
    collections = db.files
    Common.logger.info(f"Data retrieval is started {job_name}")
    fs = collections.find({"Job-Name": {"$regex": f"{job_name}"}})
    return fs


def accessing_data_via_id(build_id=None):
    """
    :param build_id:
    :return:
    """
    db = get_db_connection(db_name=DB_CONFIG["database_name"])
    collections = db.files
    Common.logger.info(f"Data accessed via id:  {build_id}")
    fs = collections.find({"_id": bson.ObjectId(f"{build_id}")})
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
    fs = collections.delete_one({"_id": bson.ObjectId(f"{build_id}")})
    Common.logger.info(f"Build ID: {build_id} deleted  successfully")
    return fs


def update_record(build_id=None, old_record=None):
    """
    :return:
    """
    db = get_db_connection(db_name=DB_CONFIG["database_name"])
    collections = db.files
    query = {"_id": bson.ObjectId(f"{build_id}")}
    new_value = {"$set": old_record}
    collections.update(query, new_value)
    Common.logger.info(f"Record updated successfully for build id: {build_id}")


def accessing_observation_db(check_before_insert=False):
    db = get_db_connection(db_name=DB_CONFIG["observation_db_name"])
    collections = db.files
    if check_before_insert:
        return collections
    fs = collections.find()
    return fs


def db_update(
    test_data=None, observation_record_key=None, observation_record_value=None
):
    """
    This method use to update the log analysis database whenever new record come
    :param dict test_data:
    :param str observation_record_key:
    :param str observation_record_value:
    """
    if observation_record_key and observation_record_value:
        data_status = check_before_insertion(
            observation_record_key=observation_record_key,
            observation_record_value=observation_record_value,
        )
    else:
        data_status = check_before_insertion(
            build_no=test_data["Build-Number"],
            job_name=test_data["Job-Name"],
            component_version=test_data["Build-Version"],
            snap_number=test_data["Snap-Version"],
        )
    status = True if data_status else False
    if status:
        return

    if observation_record_key and observation_record_value:
        collections = accessing_observation_db(check_before_insert=True)
    else:
        collections = accessing_all_data(check_before_insert=True)

    if observation_record_key and observation_record_value:
        collections.insert({f"{observation_record_key}": f"{observation_record_value}"})
    else:
        collections.insert(test_data)


def check_before_insertion(
    observation_record_key=None,
    observation_record_value=None,
    build_no=None,
    job_name=None,
    component_version=None,
    snap_number=None,
):
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
        fs = collections.find(
            {f"{observation_record_key}": f"{observation_record_value}"}
        )
    else:
        fs = collections.find(
            {
                "Build-Number": build_no,
                "Job-Name": f"{job_name}",
                "Build-Version": f"{component_version}",
                "Snap-Version": f"{snap_number}",
            }
        )
    status = True if fs.count() > 0 else False
    return status


def data_collection_based_on_job_type(job_name, job_status):
    """
    :return:
    """
    db = get_db_connection(db_name=DB_CONFIG["database_name"])
    collections = db.files
    fs = collections.find({"Job-Name": f"{job_name}", "Build-Status": f"{job_status}"})
    return fs.count()


def extracting_job_status(job_name):
    """
    This method is used to extract the passed and failed data from the database
    :return: collection
    """
    passed = data_collection_based_on_job_type(job_name, "SUCCESS")
    failed = data_collection_based_on_job_type(job_name, "FAILURE")
    unstable = data_collection_based_on_job_type(job_name, "UNSTABLE")
    job_results = {"PASSED": passed, "FAILED": failed, "UNSTABLE": unstable}
    return job_results
