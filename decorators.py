import ujson
from aiohttp.web import Response
from datetime import datetime
from functools import wraps


def audit(coroutine_handler):
    @wraps(coroutine_handler)
    async def wrapper(self, request):
        print(request.__dict__)
        status = await coroutine_handler(self, request)
        return status

    return wrapper


# Used to form the final response payload for a consumable action
def audit_and_gen_response(coroutine_handler):
    @wraps(coroutine_handler)
    async def wrapper(self, request):
        # TODO: Store an action access event to database
        data = dict()
        action_id = request.match_info.get('action_id', None)
        data['action_id'] = action_id
        start = datetime.now()
        try:
            result, status, error_msg = await coroutine_handler(self, request)
            end = datetime.now()
            data['start'] = start.strftime("%Y-%m-%d %H:%M:%S.%f")
            data['end'] = end.strftime("%Y-%m-%d %H:%M:%S.%f")
            data['total_run_time_ms'] = (end - start).total_seconds() * 1000
            print(status)
            data['success'] = status == 200
            data['status'] = status
            print(result)
            print(error_msg)
            if result is not None:
                data['result'] = result
            if error_msg is not None:
                data['error'] = error_msg

            return Response(status=status,
                            body=ujson.dumps(data, ensure_ascii=False).encode(),
                            content_type='application/json')
        except:
            # TODO: Store an action error event to database
            data['attempted_at'] = start.strftime("%Y-%m-%d %H:%M:%S.%f")
            data['success'] = False
            data['reason'] = "Internal server error. Unable to process request"

            return Response(status=500,
                            content_type='application/json',
                            body=ujson.dumps(data, ensure_ascii=False).encode())

    return wrapper


def rate_limit(coroutine_handler):
    @wraps(coroutine_handler)
    async def wrapper(request):
        # TODO: Check user token
        # TODO: Check for ip token in payload
        # TODO: Check number of requests in past seconds/minutes
        # TODO: If within the allowed limits, continue to run_app, else send rate_limit payload
        return None

    return wrapper
