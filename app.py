from aiohttp import web

from client import Client

app = web.Application()

action_client = Client()


# Add all REST routes here
# Handles the creation of authentication tokens for API access
# app.router.add_route("POST", "/login", user_handlers.create_auth_token)
# app.router.add_route("DELETE", "/logout", user_handlers.remove_auth_token)
# app.router.add_route("GET", "/{user_id}/info", user_handlers.user_info)

# Hanldes the production of api services
# app.router.add_route("POST", "/produce", action_handlers.create_api)
# Handles the inventory of a particular user's resources
# app.router.add_route("GET", "/{user_id}/inventory", user_handlers.user_list_api)
# Handles the stats for a particular action
# app.router.add_route("GET", "/{user_id}/{action_id}/metrics", action_handlers.action_metrics)
# Handles the status for a particular action (BUILDING, READY, ERROR, etc.)
# app.router.add_route("GET", "/{user_id}/{action_id}/status", action_handlers.action_status)
# Handles the stats for all actions from a particular user
# app.router.add_route("GET", "/{user_id}/stats", user_handlers.user_metrics)
# Handles the sharing of a private action with another user
# app.router.add_route("POST", "/share", action_handlers.share_actions)

# consume the REST service
app.router.add_route("GET", "/{action_id}/consume", action_client.consume)
app.router.add_route("POST", "/{action_id}/consume", action_client.consume)
app.router.add_route("PUT", "/{action_id}/consume", action_client.consume)
app.router.add_route("GET", "/{action_id}/consume/ws", action_client.consume_ws)
# Add our SockJS Websocket handler to consume streams
# This works because sockjs is implemented on top of aiohttp.
# sockjs.add_endpoint(app, action_client.consume_ws, prefix="/{action_id}/consume/ws/", name="consume-ws")
print("start")
web.run_app(app, port=9090)
