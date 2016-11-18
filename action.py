import asyncio
import json

import aiohttp

from aiohttp import web

from decorators import audit, audit_and_gen_response


# TODO: Abstract container platform one day...
class ActionHandlerMixin:

    def json_payload(self, data):
        try:
            json_data = json.loads(data)
            return json_data, True
        except ValueError:
            return None, False

    def number_payload(self, data):
        try:
            number = float(data)
            return number, True
        except ValueError:
            return None, False

    async def _register_ws(self, instance, outbound_ws):
        if instance not in self.actor_stream:
            self.action_listener[instance] = asyncio.ensure_future(self._loop.run_in_executor(None, self._stream_action_results, instance))

        if instance not in self.ws_group:
            self.ws_group[instance] = []

        self.ws_group[instance].append(outbound_ws)

    async def _cleanup(self, old_instance, new_instance):
        # Kick off new listener for new instance
        self.action_listener[new_instance] = asyncio.ensure_future(self._loop.run_in_executor(None, self._stream_action_results, new_instance))
        # Swap websocket connections to new instance
        self.ws_group[new_instance] = self.ws_group.pop(old_instance)

    @audit
    async def consume_ws(self, request):
        # Handle all websocket connections (input from clients)
        # TODO: Check if this is a streamable image
        image = request.match_info.get('action_id', None)
        # Grab an instance for us to use
        instance = await self._get_action_instance(image, is_detached=True)
        if instance:
            ws = web.WebSocketResponse()
            await ws.prepare(request)
            # We will spawn our output coroutine to send data to client

            await self._register_ws(instance, ws)

            async for msg in ws:
                # Since we are passing this data to our action instance, lets make sure it still exists
                new_instance = await self._test_and_set_action_instance(instance, image)
                if new_instance != instance:
                    await self._cleanup(instance, new_instance)
                    instance = new_instance
                    # output_future = asyncio.ensure_future(self._loop.run_in_executor(None, self._stream_action_results, instance, ws))
                if msg.tp == aiohttp.MsgType.text:
                    await self._send_to_action_instance(instance, msg.data)
                elif msg.tp == aiohttp.MsgType.binary:
                    await self._send_to_action_instance(instance, msg.data, binary=True)
                elif msg.tp == aiohttp.MsgType.error:
                    # Need to handle the close gracefully
                    print('ws connection closed with exception %s' %
                          ws.exception())
            # Handle remaining output
            await self.action_listener[instance]
            return 200
        else:
            # No such image exists
            return 404

    @audit_and_gen_response
    async def consume(self, request):
        # TODO Turn the various get params into env variables
        action_id = request.match_info.get('action_id', None)
        if request.method != "GET":
            await request.post()
        params = request.GET if request.method == 'GET' else request.POST
        payload = {k: v for k, v in params.items()}
        try:
            instance = await self._get_action_instance(action_id, is_detached=False, payload=payload)
            if instance is not None:
                result_future = self._loop.run_in_executor(None, self._get_action_results, instance)
                result = await result_future
                # Test to see what type of data this is
                # Is it JSON?
                return_data, success = self.json_payload(result)
                print(return_data, success)
                if success:
                    return return_data, 200, None
                # Is it a Number?
                return_data, success = self.number_payload(result.strip())
                print(return_data, success)
                if success:
                    return return_data, 200, None
                # Default it to being a string
                return result.strip(), 200, None
            else:
                return None, 404, "Action not found."
        except:
            # TODO: Break this down by error
            return None, 500, "Internal Error"
