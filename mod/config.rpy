default persistent._fom_log_screen_config = None

init -1001 python:
    # Shouldn't put complex mutable objects to 'default'...
    if persistent._fom_log_screen_config is None:
        persistent._fom_log_screen_config = {
            "display_lines": 6,
            "logger_levels": {},
            "panel_opacity": 0x7f,
            "text_opacity": 0xff,
            "color_scheme": 1,
            "show_on_startup": False,
            "font_size": 2
        }

init -1000 python in _fom_log_screen_config:
    from store import persistent
    import logging

    class Config(object):
        _INSTANCE = None

        @classmethod
        def instance(cls):
            if cls._INSTANCE is None:
                cls._INSTANCE = cls()
            return cls._INSTANCE

        @property
        def display_lines(self):
            return persistent._fom_log_screen_config["display_lines"]

        @display_lines.setter
        def display_lines(self, lines):
            persistent._fom_log_screen_config["display_lines"] = lines

        @property
        def logger_levels(self):
            return persistent._fom_log_screen_config["logger_levels"]

        def get_logger_level(self, logger_name):
            levelno = persistent._fom_log_screen_config["logger_levels"].get(logger_name, logging.INFO)
            normalized = (levelno // 10) * 10
            return normalized

        @property
        def logger_level_options(self):
            # NOTE "CRITICAL" is unused, and we'll use it as 'OFF' level
            range_min = logging.DEBUG
            range_max = logging.CRITICAL

            return {"offset": range_min,
                    "range": range_max - 10,
                    "step": 10}

        @property
        def logger_level_names(self):
            return {logging.DEBUG: logging._levelNames[logging.DEBUG],
                    logging.INFO: logging._levelNames[logging.INFO],
                    logging.WARNING: logging._levelNames[logging.WARNING],
                    logging.ERROR: logging._levelNames[logging.ERROR],
                    logging.CRITICAL: "OFF"}

        def add_default_logger_level(self, logger_name):
            if logger_name not in persistent._fom_log_screen_config["logger_levels"]:
                persistent._fom_log_screen_config["logger_levels"][logger_name] = logging.INFO

        @property
        def panel_background_color(self):
            return "#000000" + self.panel_background_opacity_hex

        @property
        def panel_background_opacity_hex(self):
            return "{0:02X}".format(self.panel_opacity)

        @property
        def panel_opacity(self):
            return persistent._fom_log_screen_config["panel_opacity"]

        @panel_opacity.setter
        def panel_opacity(self, opacity):
            opacity = max(0, opacity)
            opacity = min(255, opacity)
            persistent._fom_log_screen_config["panel_opacity"] = opacity

        @property
        def panel_text_opacity_hex(self):
            return "{0:02X}".format(self.panel_text_opacity)

        @property
        def panel_text_opacity(self):
            return persistent._fom_log_screen_config["text_opacity"]

        @panel_text_opacity.setter
        def panel_text_opacity(self, opacity):
            opacity = max(0, opacity)
            opacity = min(255, opacity)
            persistent._fom_log_screen_config["text_opacity"] = opacity

        @property
        def color_scheme_names(self):
            return {0: "No colors",
                    1: "Level color",
                    2: "Logger color"}

        @property
        def color_scheme_options(self):
            return {"offset": 0,
                    "range": len(self.color_scheme_names) - 1,
                    "step": 1}

        @property
        def color_scheme(self):
            return persistent._fom_log_screen_config["color_scheme"]

        @color_scheme.setter
        def color_scheme(self, color_scheme):
            persistent._fom_log_screen_config["color_scheme"] = color_scheme

        @property
        def show_on_startup(self):
            return persistent._fom_log_screen_config["show_on_startup"]

        @show_on_startup.setter
        def show_on_startup(self, show):
            persistent._fom_log_screen_config["show_on_startup"] = show


        # Font sizes are defined here, each tuple has these four items:
        # name, {size=} parameter size, height in pixels, truncation length
        _FONTS = {0: ("Tiny", "-4", 16, 154),
                  1: ("Small", "-2", 18, 130),
                  2: ("Normal", "+0", 20, 114),
                  3: ("Big", "+2", 22, 102)}

        @property
        def font_size_names(self):
            return [font[0] for font in self._FONTS.values()]

        @property
        def font_size_options(self):
            return {"offset": 0,
                    "range": len(self.font_size_names) - 1,
                    "step": 1}

        @property
        def font_size(self):
            return persistent._fom_log_screen_config["font_size"]

        @font_size.setter
        def font_size(self, size):
            persistent._fom_log_screen_config["font_size"] = size

        @property
        def font_ssize(self):
            return self._FONTS[self.font_size][1]

        @property
        def font_ysize(self):
            return self._FONTS[self.font_size][2]

        @property
        def font_trunclen(self):
            return self._FONTS[self.font_size][3]

    def get_config():
        return Config.instance()


screen fom_log_screen_config():
    $ config = _fom_log_screen_config.get_config()

    null height 10
    vbox:
        box_wrap False
        xfill True
        xmaximum 800
        spacing 10

        use fom_log_screen_panel_settings_section
        if len(config.logger_levels) > 0:
            use fom_log_screen_logger_level_section


screen fom_log_screen_panel_settings_section():
    $ tooltip = renpy.get_screen("submods", "screens").scope["tooltip"]

    vbox:
        text _("{size=+4}Panel settings{/size}")
        null height 10

        grid 2 1:
            spacing 20

            vbox:
                use fom_log_screen_max_lines_control
                use fom_log_screen_background_opacity_control
                use fom_log_screen_text_opacity_control
                use fom_log_screen_color_scheme_control
                use fom_log_screen_font_size_control

            vbox:
                use fom_log_screen_toggle_panel_control
                use fom_log_screen_show_on_startup_control


screen fom_log_screen_logger_level_section():
    $ config = _fom_log_screen_config.get_config()

    vbox:
        text _("{size=+4}Log verbosity{/size}")
        null height 10

        for logger_name in list(config.logger_levels.keys()):
            use fom_log_screen_logger_level_control(logger_name)


screen fom_log_screen_max_lines_control():
    $ config = _fom_log_screen_config.get_config()
    use fom_log_screen_control_slider(
        title=_("Max log panel size"),
        value=FieldValue(config, "display_lines", offset=1, range=9),
        display=_("{0} lines").format(config.display_lines),
        tooltip=_("You can configure how many messages will be displayed at once by dragging this slider."))

screen fom_log_screen_background_opacity_control():
    $ config = _fom_log_screen_config.get_config()
    use fom_log_screen_control_slider(
        title=_("Log panel opacity"),
        value=FieldValue(config, "panel_opacity", offset=0, range=254),
        display=_("{0:.0f}%").format(float(config.panel_opacity) / 255 * 100),
        tooltip=_("You can configure log panel opacity level by dragging this slider."))

screen fom_log_screen_logger_level_control(logger_name):
    $ config = _fom_log_screen_config.get_config()
    use fom_log_screen_control_slider(
        title=logger_name,
        value=DictValue(config.logger_levels, logger_name, **config.logger_level_options),
        display=config.logger_level_names[config.get_logger_level(logger_name)],
        tooltip=_("You can filter log messages by severity by dragging this slider."))

screen fom_log_screen_toggle_panel_control():
    use fom_log_screen_control_toggle(
        title=_("Show log panel"),
        action=Function(store._fom_log_screen_handler.toggle_screen),
        selected=store._fom_log_screen_handler.is_shown(),
        tooltip=_("You can toggle log panel by clicking here. Log panel can also be toggled by pressing L."))

screen fom_log_screen_color_scheme_control():
    $ config = _fom_log_screen_config.get_config()
    use fom_log_screen_control_slider(
        title=_("Color scheme"),
        value=FieldValue(config, "color_scheme", **config.color_scheme_options),
        display=config.color_scheme_names[config.color_scheme],
        tooltip=_("You can configure log messages color scheme by dragging this slider."))

screen fom_log_screen_show_on_startup_control():
    $ config = _fom_log_screen_config.get_config()
    use fom_log_screen_control_toggle(
        title=_("Show on startup"),
        action=ToggleField(config, "show_on_startup"),
        selected=config.show_on_startup,
        tooltip=_("You can toggle whether log panel is shown on startup."))

screen fom_log_screen_font_size_control():
    $ config = _fom_log_screen_config.get_config()
    use fom_log_screen_control_slider(
        title=_("Font size"),
        value=FieldValue(config, "font_size", **config.font_size_options),
        display=config.font_size_names[config.font_size],
        tooltip=_("You can adjust log font size by dragging this slider."))

screen fom_log_screen_text_opacity_control():
    $ config = _fom_log_screen_config.get_config()
    use fom_log_screen_control_slider(
        title=_("Log text opacity"),
        value=FieldValue(config, "panel_text_opacity", offset=0, range=254),
        display=_("{0:.0f}%").format(float(config.panel_text_opacity) / 255 * 100),
        tooltip=_("You can configure log text opacity level by dragging this slider."))


screen fom_log_screen_control_slider(title, value, display=None, tooltip=None):
    $ tooltip_disp = renpy.get_screen("submods", "screens").scope["tooltip"]

    hbox:
        spacing 10

        text title
        bar value value:
            style "slider_slider"
            xsize 200

            if tooltip:
                hovered SetField(tooltip_disp, "value", tooltip)
                unhovered SetField(tooltip_disp, "value", tooltip_disp.default)

        if display is not None:
            text display

screen fom_log_screen_control_toggle(title, action, selected, tooltip=None):
    $ tooltip_disp = renpy.get_screen("submods", "screens").scope["tooltip"]

    hbox:
        style_prefix "check"
        textbutton title action action selected selected:
            if tooltip is not None:
                hovered SetField(tooltip_disp, "value", tooltip)
                unhovered SetField(tooltip_disp, "value", tooltip_disp.default)
