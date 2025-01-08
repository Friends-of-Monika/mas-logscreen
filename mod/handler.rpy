init -900 python in _fom_log_screen_handler:
    from store.mas_logging import LOG_MAP
    from store import mas_logging

    from store._fom_log_screen_utils import quote
    from store._fom_log_screen_config import get_config

    from store import config
    from store import persistent

    import store
    import logging
    import colorsys
    import datetime
    import random


    class RecordPrinter(object):
        def print_record(self, record):
            pass

    class StructPrinter(RecordPrinter):
        def __init__(self):
            super(StructPrinter, self).__init__()

        def print_logger(self, logger):
            return quote(logger)

        def print_level(self, levelno):
            return quote(logging._levelNames.get(levelno, "UNKNOWN"))

        def print_time(self, time):
            return quote(datetime.datetime.fromtimestamp(time).strftime("%H:%M:%S"))

        def print_message(self, msg):
            return quote(msg)

    class DefaultStructPrinter(StructPrinter):
        def __init__(self):
            super(DefaultStructPrinter, self).__init__()

        def print_record(self, record):
            return "{time} {logger} {level} {message}".format(
                logger=self.print_logger(record.name),
                level=self.print_level(record.levelno),
                time=self.print_time(record.created),
                message=self.print_message(record.msg))

        def print_level(self, level):
            return "[" + super(DefaultStructPrinter, self).print_level(level) + "]"

        def print_logger(self, logger):
            return "[" + super(DefaultStructPrinter, self).print_logger(logger) + "]"

    class TruncatingStructPrinter(DefaultStructPrinter):
        TRUNC_FORMAT = "... ({remaining} characters)"

        def __init__(self):
            super(TruncatingStructPrinter, self).__init__()
            self._config = get_config()

        def print_record(self, record):
            full = super(TruncatingStructPrinter, self).print_record(record)
            trunc_len = self._config.font_trunclen

            result_str = full
            if len(full) > trunc_len:
                trunc = self.TRUNC_FORMAT.format(remaining=len(full) - trunc_len)

                result_str = full[:trunc_len]
                if result_str.endswith("[") or result_str.endswith("{"):
                    result_str = result_str[:-1] + quote(result_str[-1])
                    result_str = result_str.ljust(trunc_len) + "{:>23}".format(trunc)
                else:
                    result_str = result_str.ljust(trunc_len) + "{:>24}".format(trunc)

            return result_str


    class ColorStructPrinter(StructPrinter):
        def __init__(self, printer):
            super(ColorStructPrinter, self).__init__()
            self._config = get_config()
            self.printer = printer

        def print_record(self, record):
            msg = self.printer.print_record(record)
            color = self.get_color(record)
            opacity = self._config.panel_text_opacity_hex
            return "{color=" + color + opacity + "}" + msg + "{/color}"

        def get_color(self, record):
            return "#FFFFFF"

    class RandomColorStructPrinter(ColorStructPrinter):
        def __init__(self, printer):
            super(RandomColorStructPrinter, self).__init__(printer)
            self._logger_colors = {}

        def get_color(self, record):
            if record.name not in self._logger_colors:
                self._logger_colors[record.name] = self.random_color()
            return self._logger_colors[record.name]

        def random_color(self):
            hue = random.uniform(0, 360)
            saturation = random.uniform(0.4, 0.6)
            lightness = random.uniform(0.7, 0.85)
            r, g, b = colorsys.hls_to_rgb(hue / 360, lightness, saturation)
            r, g, b = int(r * 255), int(g * 255), int(b * 255)
            return "#{0:02x}{1:02x}{2:02x}".format(r, g, b)

    class LevelColorStructPrinter(ColorStructPrinter):
        def __init__(self, printer):
            super(LevelColorStructPrinter, self).__init__(printer)
            self.level_colors = {
                logging.DEBUG: "#90CAF9",
                logging.INFO: "#FAFAFA",
                logging.WARNING: "#FFEB3B",
                logging.ERROR: "#EF5350",
                logging.NOTSET: "#757575"
            }

        def get_color(self, record):
            color = self.level_colors.get(record.levelno, None)
            if color is None:
                color = self.level_colors[logging.NOTSET]
            return color

    class ConfigurableColorStructPrinter(ColorStructPrinter):
        def __init__(self, printer):
            super(ConfigurableColorStructPrinter, self).__init__(printer)
            self._config = get_config()
            self._schemes = {0: ColorStructPrinter(printer),
                             1: LevelColorStructPrinter(printer),
                             2: RandomColorStructPrinter(printer)}

        def print_record(self, record):
            return self._schemes[self._config.color_scheme].print_record(record)

    class SizeStructPrinter(StructPrinter):
        def __init__(self, printer):
            super(SizeStructPrinter, self).__init__()
            self.printer = printer

        def get_size(self, record):
            return "+0"

        def print_record(self, record):
            msg = self.printer.print_record(record)
            size = self.get_size(record)
            return "{size=" + size + "}" + msg + "{/size}"

    class ConfigurableSizeStructPrinter(SizeStructPrinter):
        def __init__(self, printer):
            super(ConfigurableSizeStructPrinter, self).__init__(printer)
            self._config = get_config()

        def get_size(self, record):
            return self._config.font_ssize

    class RecordFilter(object):
        def accept(self, record):
            pass

    class LevelFilter(RecordFilter):
        def __init__(self):
            super(LevelFilter, self).__init__()
            self._config = get_config()

        def accept(self, record):
            logger_level = self._config.get_logger_level(record.name)
            return record.levelno >= logger_level


    class ScreenLogHandler(logging.Handler):
        _INSTANCE = None

        def __init__(self):
            super(ScreenLogHandler, self).__init__()

            self._buffer_lines = 200
            self._config = get_config()

            self._printer = self._get_printer()
            self._filter = LevelFilter()

            self._records_buffer = []
            self._display_lines = []

        def _get_printer(self):
            trunc = TruncatingStructPrinter()
            color = ConfigurableColorStructPrinter(trunc)
            size = ConfigurableSizeStructPrinter(color)
            return size

        @classmethod
        def instance(cls):
            if cls._INSTANCE is None:
                cls._INSTANCE = cls()
            return cls._INSTANCE

        @property
        def display_lines(self):
            return self._display_lines

        def emit(self, record):
            self._push_buffer_record(record)
            self.update_log_lines()

        def _push_buffer_record(self, record):
            if len(self._records_buffer) == self._buffer_lines:
                self._records_buffer.pop(0)

            self._records_buffer.append(record)
            self._config.add_default_logger_level(record.name)

        def update_log_lines(self):
            new_lines = []

            for record in self._records_buffer:
                if self._filter.accept(record):
                    msg = self._printer.print_record(record)
                    new_lines.append(msg)

            new_lines[::] = new_lines[-self._config.display_lines:]
            if new_lines != self._display_lines:
                # Check if we need to update displayed lines at all
                self._display_lines[::] = new_lines


    def get_handler():
        return ScreenLogHandler.instance()

    def add_handler(logger, handler):
        if isinstance(logger, logging.LoggerAdapter):
            logger = logger.logger
        logger.addHandler(handler)

    def add_all_handlers():
        handler = get_handler()
        for logger in list(mas_logging.LOG_MAP.values()):
            add_handler(logger, handler)

    def decorate_init_log(fn):
        handler = get_handler()

        def decorated(*args, **kwargs):
            logger = fn(*args, **kwargs)
            add_handler(logger, handler)
            return logger

        return decorated


    def show_screen():
        renpy.show_screen("fom_log_screen")
        renpy.restart_interaction()

    def hide_screen():
        renpy.hide_screen("fom_log_screen")
        renpy.restart_interaction()

    def is_shown():
        return bool(renpy.get_screen("fom_log_screen"))

    def toggle_screen():
        if is_shown():
            hide_screen()
        else:
            show_screen()


    config.keymap["fom_toggle_log_screen"] = ["K_l"]
    config.underlay.append(renpy.Keymap(fom_toggle_log_screen=toggle_screen))

    add_all_handlers()
    mas_logging.init_log = decorate_init_log(mas_logging.init_log)
