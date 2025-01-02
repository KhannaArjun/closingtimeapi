
def get_dev_db():
    CONNECTION_STRING = "mongodb+srv://sclosingtime:sclosingtime@sclosingtime.1bd7w.mongodb.net/sclosingtime?retryWrites=true&w=majority&ssl=true&ssl_cert_reqs=CERT_NONE"
    db_name = "closingtime"
    # uName = closingtime
    # password = "closingtime"
    return CONNECTION_STRING, db_name


def get_prod_db():
    CONNECTION_STRING = "mongodb+srv://sclosingtime:sclosingtime@sclosingtime.ryu6d.mongodb.net/sclosingtime?retryWrites=true&w=majority&ssl=true&ssl_cert_reqs=CERT_NONE"
    db_name = "sclosingtime"
    # u_name = "closingtimeprod"
    # password = "closingtimeprod"

    # mongodb + srv: // < username >: < password >@closingtimeprod.ryu6d.mongodb.net / myFirstDatabase
    #
    # ?retryWrites = true & w = majority

    return CONNECTION_STRING, db_name

# mongodb+srv://sclosingtime:kMkVUstECvlgS2JX@cluster0ct.sjo2d.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0CT
# python -m pip install "pymongo[srv]"


