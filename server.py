import tornado.web
import tornado.ioloop
import tornado.options

import restful

url_mapping = [
                (r"/recording/(.*)", restful.Recording),
                (r"/signal/(.*)",    restful.Signal),
                (r"/stream/(.*)",    restful.Stream),
              ]


if __name__ == "__main__":
#=========================

  tornado.options.define('port',    default='8888',      help='Server listen port (8888)',  metavar='PORT')
  tornado.options.define('address', default='127.0.0.1', help='Server address (127.0.0.1)', metavar='ADDRESS')
  tornado.options.parse_command_line()

  application = tornado.web.Application(url_mapping, debug=True, )
  application.listen(tornado.options.options.port, tornado.options.options.address)
  
  tornado.ioloop.IOLoop.instance().start()

