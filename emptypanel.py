import logging

from gi.repository import Gtk

from sugar3.graphics import style
from sugar3.graphics.icon import Icon


def show(activity, icon_name, message, btn_label, btn_callback):
    empty_widgets = Gtk.EventBox()
    empty_widgets.modify_bg(Gtk.StateType.NORMAL,
                            style.COLOR_WHITE.get_gdk_color())

    vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    mvbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    vbox.pack_start(mvbox, True, False, 0)

    image_icon = Icon(pixel_size=style.LARGE_ICON_SIZE,
                      icon_name=icon_name,
                      stroke_color=style.COLOR_BUTTON_GREY.get_svg(),
                      fill_color=style.COLOR_TRANSPARENT.get_svg())
    mvbox.pack_start(image_icon, False, False, style.DEFAULT_PADDING)

    label = Gtk.Label('<span foreground="%s"><b>%s</b></span>' %
                      (style.COLOR_BUTTON_GREY.get_html(),
                       message))
    label.set_use_markup(True)
    mvbox.pack_start(label, False, False, style.DEFAULT_PADDING)

    hbox = Gtk.Box()
    open_image_btn = Gtk.Button()
    open_image_btn.connect('clicked', btn_callback)
    add_image = Gtk.Image.new_from_stock(Gtk.STOCK_ADD,
                                         Gtk.IconSize.BUTTON)
    buttonbox = Gtk.Box()
    buttonbox.pack_start(add_image, False, True, 0)
    buttonbox.pack_end(Gtk.Label(btn_label), True, True, 5)
    open_image_btn.add(buttonbox)
    hbox.pack_start(open_image_btn, True, False, 0)
    mvbox.pack_start(hbox, False, False, style.DEFAULT_PADDING)

    empty_widgets.add(vbox)
    empty_widgets.show_all()
    logging.error('Showing empty Panel')
    activity.set_canvas(empty_widgets)
