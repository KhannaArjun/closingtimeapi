def apiResponse(message, flag, data):
    return {
            "message" : message,
            "error": flag,
            "data": data
        }