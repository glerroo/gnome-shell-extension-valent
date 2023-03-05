# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2022 Andy Holmes <andrew.g.r.holmes@gmail.com>

# pylint: disable=fixme,invalid-name

"""
This module provides implementations for :class:`~Valent.ClipboardAdapter`, when
used with the GNOME Shell extension.
"""

# pylint: disable-next=no-name-in-module
from gi.repository import Gio, GLib, GObject, Valent


GNOMESHELL_NAME = 'org.gnome.Shell'
CLIPBOARD_NAME = 'org.gnome.Shell.Extensions.Valent.Clipboard'
CLIPBOARD_PATH = '/org/gnome/Shell/Extensions/Valent/Clipboard'


class ValentGsClipboardAdapter(Valent.ClipboardAdapter):
    """A :class:`~Valent.ClipboardAdapter` that communicates with a D-Bus
    interface exported from inside a GNOME Shell extension.
    """

    __gtype_name__ = 'ValentGsClipboardAdapter'

    def __init__(self):
        Valent.ClipboardAdapter.__init__(self)

        self.proxy = None
        self.mimetypes = []
        self.timestamp = 0
        Gio.DBusProxy.new_for_bus(Gio.BusType.SESSION,
                                  Gio.DBusProxyFlags.DO_NOT_AUTO_START,
                                  None,
                                  GNOMESHELL_NAME,
                                  CLIPBOARD_PATH,
                                  CLIPBOARD_NAME,
                                  None,
                                  self._new_for_bus_cb,
                                  None)

    def _new_for_bus_cb(self, _proxy, result, _user_data):
        try:
            self.proxy = Gio.DBusProxy.new_for_bus_finish(result)
            self.proxy.connect('g-signal', self._on_g_signal)
        except GLib.Error as error:
            print(repr(error))

    def _on_g_signal(self, _proxy, _sender_name, signal_name, parameters):
        if self.proxy is None or self.proxy.props.g_name_owner is None:
            return

        if signal_name == 'Changed':
            metadata = parameters[0]
            self.mimetypes = metadata.get('mimetypes', [])
            self.timestamp = metadata.get('timestamp', Valent.timestamp_ms())
            self.changed()

    def do_get_mimetypes(self):
        """
        Implementation of :meth:`~Valent.ClipboardAdapter.get_mimetypes`.
        """

        return self.mimetypes

    def do_get_timestamp(self):
        """
        Implementation of :meth:`~Valent.ClipboardAdapter.get_timestamp`.
        """

        return self.timestamp

    def _get_bytes_cb(self, proxy, result, task):
        try:
            data = proxy.call_finish(result)[0]
            value = GObject.Value(GObject.TYPE_BYTES, GLib.Bytes(data))
            task.return_value(value)
        except GLib.Error as error:
            task.return_error(error)

    def do_read_bytes(self, mimetype, cancellable, callback, _user_data):
        """
        Implementation of :meth:`~Valent.ClipboardAdapter.read_bytes`.
        """

        # FIXME: we're swallowing `user_data`, since it can't be passed back
        #        into libvalent by libpeas (yet)
        task = Gio.Task.new(self, cancellable, callback)

        if self.proxy is None or self.proxy.props.g_name_owner is None:
            error = GLib.Error.new_literal(Gio.dbus_error_quark(),
                                           'GNOME Shell extension disabled',
                                           Gio.DBusError.NAME_HAS_NO_OWNER)
            task.return_error(error)
            return

        self.proxy.call('GetBytes',
                        GLib.Variant('(s)', (mimetype,)),
                        None,
                        Gio.DBusCallFlags.NO_AUTO_START,
                        -1,
                        cancellable,
                        self._get_bytes_cb,
                        task)

    def do_read_bytes_finish(self, result):
        """
        Implementation of :meth:`~Valent.ClipboardAdapter.read_bytes_finish`.
        """

        return result.propagate_value()[1]

    def _set_bytes_cb(self, proxy, result, task):
        try:
            proxy.call_finish(result)
            task.return_boolean(True)
        except GLib.Error as error:
            task.return_error(error)

    def do_write_bytes(self, mimetype, gbytes, cancellable, callback, _user_data):
        """
        Implementation of :meth:`~Valent.ClipboardAdapter.write_bytes`.
        """

        # FIXME: we're swallowing `user_data`, since it can't be passed back
        #        into libvalent by libpeas (yet)
        task = Gio.Task.new(self, cancellable, callback)

        if self.proxy is None or self.proxy.props.g_name_owner is None:
            error = GLib.Error.new_literal(Gio.dbus_error_quark(),
                                           'GNOME Shell extension disabled',
                                           Gio.DBusError.NAME_HAS_NO_OWNER)
            task.return_error(error)
            return

        self.proxy.call('SetBytes',
                        GLib.Variant('(say)', (mimetype, gbytes.get_data(),)),
                        Gio.DBusCallFlags.NONE,
                        -1,
                        cancellable,
                        self._set_bytes_cb,
                        task)

    def _get_text_cb(self, proxy, result, task):
        try:
            text = proxy.call_finish(result)[0]
            value = GObject.Value(GObject.TYPE_STRING, text)
            task.return_value(value)
        except GLib.Error as error:
            task.return_error(error)

    def do_read_text(self, cancellable, callback, _user_data):
        """
        Implementation of :meth:`~Valent.ClipboardAdapter.read_text`.
        """

        # FIXME: we're swallowing `user_data`, since it can't be passed back
        #        into libvalent by libpeas (yet)
        task = Gio.Task.new(self, cancellable, callback)

        if self.proxy is None or self.proxy.props.g_name_owner is None:
            error = GLib.Error.new_literal(Gio.dbus_error_quark(),
                                           'GNOME Shell extension disabled',
                                           Gio.DBusError.NAME_HAS_NO_OWNER)
            task.return_error(error)
            return

        self.proxy.call('GetText',
                        None,
                        Gio.DBusCallFlags.NO_AUTO_START,
                        -1,
                        cancellable,
                        self._get_text_cb,
                        task)

    def do_read_text_finish(self, result):
        """
        Implementation of :meth:`~Valent.ClipboardAdapter.read_text_finish`.
        """

        return result.propagate_value()[1]

    def _set_text_cb(self, proxy, result, task):
        try:
            proxy.call_finish(result)
            task.return_boolean(True)
        except GLib.Error as error:
            task.return_error(error)

    def do_write_text(self, text, cancellable, callback, _user_data):
        """
        Implementation of :meth:`~Valent.ClipboardAdapter.set_text`.
        """

        # FIXME: we're swallowing `user_data`, since it can't be passed back
        #        into libvalent by libpeas (yet)
        task = Gio.Task.new(self, cancellable, callback)

        if self.proxy is None or self.proxy.props.g_name_owner is None:
            error = GLib.Error.new_literal(Gio.dbus_error_quark(),
                                           'GNOME Shell extension disabled',
                                           Gio.DBusError.NAME_HAS_NO_OWNER)
            task.return_error(error)
            return

        self.proxy.call('SetText',
                        GLib.Variant('(s)', (text,)),
                        Gio.DBusCallFlags.NONE,
                        -1,
                        cancellable,
                        self._set_text_cb,
                        task)
