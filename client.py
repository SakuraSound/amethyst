import asyncio
import aiohttp
import traceback
from functools import partial

from docker.client import Client as DockerClient
from docker.utils import kwargs_from_env
from action import ActionHandlerMixin
from typing import Optional, List, Union


class Client(ActionHandlerMixin):

    def _docker(self):
        kw = kwargs_from_env()
        kw['tls'].verify = True
        return DockerClient(**kw)

    def __init__(self):
        self._loop = asyncio.get_event_loop()
        self.actor = self._docker()
        self.actor_stream = {}
        self.action_listener = {}
        self.ws_group = {}

    async def get_action_info(self, instance: str) -> dict:
        try:
            return await self._loop.run_in_executor(None, self.actor.inspect_container, instance)
        except:
            return None

    async def _test_and_set_action_instance(self, instance: str, action_image: str, detach=False) -> Optional[str]:
        # Checks to see if the current action we are working with is active or not
        try:
            return instance if (await self._is_action_active(instance)) else await self._get_action_instance(action_image, detach)
        except:
            return None

    async def _is_action_active(self, instance) -> Optional[bool]:
        try:
            # Since there are no kwargs, we can simply use run_in_executor on the function
            info_future = self._loop.run_in_executor(None, self.actor.inspect_container, instance)
            info = await info_future
            return info['State']['Running'] if info else False
        except:
            return False

    async def _get_action_instance(self, image, is_detached=False, payload=None) -> Optional[str]:
        if is_detached:
            # Then this is streaming, and we should reuse the container
            instance_list = await self._list_actions_by_image(image)
            if len(instance_list) > 0:
                # FIXME: For now, just ge the first instance
                return instance_list[0]
        # Otherwise, just spawn a new one (whether its not detached, or if we dont have a detached action running)
        return await self._spawn_action(image, is_detached, payload=payload)

    async def _list_actions_by_image(self, image: str) -> List[str]:
        # Here, we need to use functools.partial, since we have kwargs for our coroutine
        containers = partial(self.actor.containers, filters={"ancestor": image})
        container_list = await self._loop.run_in_executor(None, containers)
        return [c["Id"] for c in container_list]

    async def _send_to_action_instance(self, instance: str, msg: Union[str, Union[bytes, bytearray]], binary=False):
        # For events
        attach_socket = partial(self.actor.attach_socket,
                                instance,
                                params={'stdin': 1,
                                        'stream': 1,
                                        "sig-proxy": 0})
        in_socket = await self._loop.run_in_executor(None, attach_socket)
        with in_socket:
            msg = '{}\n'.format(msg) if not msg.endswith("\n") and not binary else msg
            in_socket.send(msg.encode())

    async def _spawn_action(self, image: str, is_detached: bool, payload={}):
        # asyncio doesnt support kwargs... so we create a partial function (technically the set is a subset of the set, so it makes sense)
        try:
            create_container = partial(self.actor.create_container,
                                       image,
                                       # network_disabled=True,
                                       stdin_open=True,
                                       detach=is_detached,
                                       environment=payload)
            action_fut = self._loop.run_in_executor(None, create_container)
            action = await action_fut
            # TODO: Should this be wrapped too?
            self.actor.start(action['Id'])
            return action['Id']
        except:
            print("Unable to spawn action.")
            traceback.print_exc()
            return None

    # Not a coroutine! Since docker-py is not built to take advantage of asyncio, make sure to launch this using loop.run_in_executor()
    def _get_action_results(self, instance: str):
        print("Getting action results")
        # This should be used for REST style actions, for event-driven and streaming actions, use _listen_action_results
        # Attach to container and grab the output stream, then join all output and store to db
        result_gen = self.actor.attach(instance, stdout=True, stderr=True, stream=True, logs=True)
        # This is a blocking call as result_gen is a blocking generator
        result = "".join([str(output.decode()) for output in result_gen])
        print(result)
        return result

    # Not a coroutine! Since docker-py is not built to take advantage of asyncio, make sure to launch this using loop.run_in_executor()
    def _stream_action_results(self, instance: str):
        # TODO: Currently, a thread is created per websocket... Should change this...
        if instance not in self.actor_stream:
            print("{0} is not attached. Attaching...".format(instance))
            # We are going to store this stream
            self.actor_stream[instance] = self.actor.attach(instance, stdout=True, stderr=True, stream=True)

        '''
        if instance not in self.ws_group:
            self.ws_group[instance] = []
        self.ws_group[instance].append(outbound_ws)
        '''
        # This is a blocking generator that will produce as long as our websocket is open (client is connected) or our stream is open (container is connected)
        for data in self.actor_stream[instance]:
            print(data.decode())
            try:
                self.ws_group[instance] = [ws for ws in self.ws_group[instance] if not ws.closed]
                print("sending to {0} connections".format(len(self.ws_group[instance])))
                for ws in self.ws_group[instance]:
                    ws.send_str(data.decode())
            except ValueError:
                # The client disconnected during the stream
                print("Connection closed by client.")
                break
        print("Channel Closed")
