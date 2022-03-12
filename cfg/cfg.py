
def get_dev_db():
    CONNECTION_STRING = "mongodb+srv://closingtime:closingtime@closingtime.1bd7w.mongodb.net/closingtime?retryWrites=true&w=majority&ssl=true&ssl_cert_reqs=CERT_NONE"
    db_name = "closingtime"
    # uName = closingtime
    # password = "closingtime"
    return CONNECTION_STRING, db_name


def get_prod_db():
    CONNECTION_STRING = "mongodb+srv://closingtimeprod:closingtimeprod@closingtimeprod.ryu6d.mongodb.net/closingtimeprod?retryWrites=true&w=majority&ssl=true&ssl_cert_reqs=CERT_NONE"
    db_name = "closingtimeprod"
    # u_name = "closingtimeprod"
    # password = "closingtimeprod"

    # mongodb + srv: // < username >: < password >@closingtimeprod.ryu6d.mongodb.net / myFirstDatabase
    #
    # ?retryWrites = true & w = majority

    return CONNECTION_STRING, db_name



