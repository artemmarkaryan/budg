from aiohttp import web
import os

# routes
async def handle(request):
	name = request.match_info.get('name', "Anonymous")
	text = "Hello, " + name
	return web.Response(text=text)

app = web.Application()
routes = [
	web.get('/', handle),
	web.get('/{name}', handle)
]
app.add_routes(routes)

if __name__ == '__main__':
	web.run_app(app, port=os.environ.get('PORT', 8080))
