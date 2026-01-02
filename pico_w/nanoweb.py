import uasyncio as asyncio
import uerrno
import ujson

class HttpError(Exception):
    pass


class Request:
    def __init__(self):
        self.url = ""
        self.method = ""
        self.headers = {}
        self.body = {}    
        self.route = ""
        self.read = None
        self.write = None
        self.close = None


async def write(request, data):
    await request.write(
        data.encode('ISO-8859-1') if type(data) == str else data
    )


async def error(request, code, reason):
    await request.write("HTTP/1.1 %s %s\r\n\r\n" % (code, reason))
    await request.write("<h1>%s</h1>" % (reason))


async def send_file(request, filename, segment=64, binary=False):
    try:
        with open(filename, 'rb' if binary else 'r') as f:
            while True:
                data = f.read(segment)
                if not data:
                    break
                await request.write(data)
    except OSError as e:
        if e.args[0] != uerrno.ENOENT:
            raise
        raise HttpError(request, 404, "File Not Found")


class Nanoweb:
    extract_headers = ('Authorization', 'Content-Length', 'Content-Type')
    routes = {}
    assets_extensions = ('html', 'css', 'js')

    callback_request = None
    callback_error = staticmethod(error)

    STATIC_DIR = './'
    INDEX_FILE = STATIC_DIR + 'index.html'

    def __init__(self, port=80, address='0.0.0.0'):
        self.port = port
        self.address = address

    def route(self, route):
        """Route decorator"""
        def decorator(func):
            self.routes[route] = func
            return func
        return decorator

    async def generate_output(self, request, handler):
        """Generate output from handler
        `handler` can be :
         * dict representing the template context
         * string, considered as a path to a file
         * tuple where the first item is filename and the second
           is the template context
         * callable, the output of which is sent to the client
        """
        while True:
            if isinstance(handler, dict):
                self.logMsg("generate_output...dict")                                            
                handler = (request.url, handler)

            if isinstance(handler, str):
                await write(request, "HTTP/1.1 200 OK\r\n\r\n")
                await send_file(request, handler)
            elif isinstance(handler, tuple):
                await write(request, "HTTP/1.1 200 OK\r\n\r\n")
                filename, context = handler
                context = context() if callable(context) else context
                try:
                    with open(filename, "r") as f:
                        for l in f:
                            await write(request, l.format(**context))
                except OSError as e:
                    if e.args[0] != uerrno.ENOENT:
                        raise
                    raise HttpError(request, 404, "File Not Found")
            else:
                self.logMsg("generate_output...handler" + str(handler))                                                            
                handler = await handler(request)
                
                if handler:
                    self.logMsg("handler OK...")
                    # handler can return data that can be fed back
                    # to the input of the function
                    continue
            break

    def logMsg(self, msg):
        return
        print(msg)
        
    async def handle_x(self, reader, writer):
        items = await reader.readline()
        self.logMsg("Reader...first readline" + str(items))        
        items = items.decode('ascii').split()
        
        if len(items) != 3:
            return

        request = Request()
        #self.logMsg("new request...headers")
        #self.logMsg(request.headers)
        request.read = reader.read
        request.write = writer.awrite
        request.close = writer.aclose
        request.method, request.url, version = items
        self.logMsg("Method: " + request.method)
        self.logMsg("URL: " + request.url)
        self.logMsg("Version: " + version)        

        try:
            try:
                if version not in ("HTTP/1.0", "HTTP/1.1"):
                    raise HttpError(request, 505, "Version Not Supported")

                while True:
                    items = await reader.readline()
                    self.logMsg("Reader...second readline" + str(items))                            
                    items = items.decode('ascii').split(":", 1)

                    if len(items) == 2:
                        self.logMsg("2 items...")                                                    
                        header, value = items
                        value = value.strip()
                        self.logMsg("Header: " + header)                        
                        self.logMsg("Value: " + value)

                        if header in self.extract_headers:
                            request.headers[header] = value
                            
                        self.logMsg(request.headers)
                    elif len(items) == 1:
                        self.logMsg("1 item...")                                                    
#                        self.logMsg("1 item left: " + str(items))
 #                       self.logMsg("request.headers: " + str(type(request.headers)))
                        self.logMsg(request.headers)
                       
                        if (request.headers.get('Content-Length') != None
                                and request.headers.get('Content-Length') != '0'):
                            self.logMsg("Content-Length present... " + value)                            
                            bytesleft = int(request.headers.get('Content-Length', 0))
                            self.logMsg("Todo item bytes left..." + str(bytesleft))
                            body = await reader.read(bytesleft)
                            body = body.decode()
                            
                            try:
                                self.logMsg("Body:\r\n" + str(body))                
                                parsed = ujson.loads(str(body))
                                request.body = parsed
                            except (ValueError, TypeError):
                                print("json parsing error")
                                    
                        break                        
                
                if self.callback_request:
                    print("in callback_request")
                    self.callback_request(request)

                if request.url in self.routes:
                    # 1. If current url exists in routes
                    self.logMsg("route found: " + request.url)                    
                    request.route = request.url
                    await self.generate_output(request, self.routes[request.url])
                else:
                    # 2. Search url in routes with wildcard
                    for route, handler in self.routes.items():
                        if (route == request.url or request.url.startswith(route[:-1])):
#                            or (route[-1] == '*' and
                                #or request.url.startswith(route[:-1]):
                            request.route = route
                            self.logMsg("wildcard route found: " + request.url)                                                
                            await self.generate_output(request, handler)
                            break
                    else:
                        # 3. Try to load index file
                        if request.url in ('', '/'):
                            await send_file(request, self.INDEX_FILE)
                        else:
                            # 4. Current url have an assets extension ?
                            for extension in self.assets_extensions:
                                if request.url.endswith('.' + extension):
                                    await send_file(
                                        request,
                                        '%s/%s' % (
                                            self.STATIC_DIR,
                                            request.url,
                                        ),
                                        binary=True,
                                    )
                                    break
                            else:
                                raise HttpError(request, 404, "File Not Found")
            except HttpError as e:
                request, code, message = e.args
                await self.callback_error(request, code, message)
        except OSError as e:
            # Skip ECONNRESET error (client abort request)
            if e.args[0] != uerrno.ECONNRESET:
                raise
        finally:
            await writer.aclose()

    async def handle(self, reader, writer):
        items = await reader.readline()
        items = items.decode('ascii').split()
        if len(items) != 3:
            return

        request = Request()
        request.read = reader.read
        request.write = writer.awrite
        request.close = writer.aclose

        request.method, request.url, version = items

        try:
            try:
                if version not in ("HTTP/1.0", "HTTP/1.1"):
                    raise HttpError(request, 505, "Version Not Supported")

                while True:
                    items = await reader.readline()
                    items = items.decode('ascii').split(":", 1)

                    if len(items) == 2:
                        header, value = items
                        value = value.strip()

                        if header in self.extract_headers:
                            request.headers[header] = value
                    elif len(items) == 1:
                        break

                if self.callback_request:
                    self.callback_request(request)

                if request.url in self.routes:
                    # 1. If current url exists in routes
                    request.route = request.url
                    await self.generate_output(request,
                                               self.routes[request.url])
                else:
                    # 2. Search url in routes with wildcard
                    for route, handler in self.routes.items():
                        if route == request.url \
                            or (route[-1] == '*' and
                                request.url.startswith(route[:-1])):
                            request.route = route
                            await self.generate_output(request, handler)
                            break
                    else:
                        # 3. Try to load index file
                        if request.url in ('', '/'):
                            await send_file(request, self.INDEX_FILE)
                        else:
                            # 4. Current url have an assets extension ?
                            for extension in self.assets_extensions:
                                if request.url.endswith('.' + extension):
                                    await send_file(
                                        request,
                                        '%s/%s' % (
                                            self.STATIC_DIR,
                                            request.url,
                                        ),
                                        binary=True,
                                    )
                                    break
                            else:
                                raise HttpError(request, 404, "File Not Found")
            except HttpError as e:
                request, code, message = e.args
                await self.callback_error(request, code, message)
        except OSError as e:
            # Skip ECONNRESET error (client abort request)
            if e.args[0] != uerrno.ECONNRESET:
                raise
        finally:
            await writer.aclose()
            
    async def run(self):
        return await asyncio.start_server(self.handle_x, self.address, self.port)
