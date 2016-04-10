from tornado import ioloop
from tornado import web
from tornado import options

from app.user import UserProcess, UserStatus, ShowtimeProcess
from lib import config
from lib import processors


# Set basic options
options.define("port", default=6060, type=int, help="What port to run on")
options.define("debug", default=False, type=bool, help="Debug Mode")
options.define("config", default='dev',
               type=str, help="Section of config file to read")


if __name__ == "__main__":
    options.parse_command_line()
    port = options.options.port
    debug = options.options.debug
    config.read_config(options.options.config)
    CONFIG = config.CONFIG

    processor_handlers = [
        ph
        for p in processors.processors
        for ph in p.register_handlers()
    ]
    print("Registering process handlers:")
    print('\t' + "\n\t".join(ph[0] for ph in processor_handlers))

    app = web.Application(
        [
            (r'/api/showtime/process', ShowtimeProcess),
            (r'/api/user/process', UserProcess),
            (r'/api/user/status', UserStatus),
        ] + processor_handlers,
        debug=debug,
        cookie_secret=CONFIG.get("cookie_secret"),
    )

    print("Listening on port: " + str(port))
    app.listen(port, protocol='https')
    ioloop.IOLoop.current().start()
