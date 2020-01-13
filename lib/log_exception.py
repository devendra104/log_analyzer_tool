class LogException:
    @staticmethod
    def PATH_NOT_FOUND(msg):
        print("ALERT!!!!!!!!!!!!!!!!!:{}".format(msg))

    @staticmethod
    def PARAMIKO_EXCEPTION(msg):
        print("ALERT!!!!!!!!!!!!!!!!!!!{}".format(msg))

    @staticmethod
    def PATTERN_MATCH_EXCEPTION(msg):
        print("Pattern Matching Error in Method: {}".format(msg))

    @staticmethod
    def JOB_DOES_NOT_EXIST(msg):
        print("Job does not Exist on the target server: {}".format(msg))
