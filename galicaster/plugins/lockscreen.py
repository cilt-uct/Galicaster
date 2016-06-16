# -*- coding:utf-8 -*-
# Galicaster, Multistream Recorder and Player
#
#       galicaster/plugins/lockscreen
#
# Copyright (c) 2016, Teltek Video Research <galicaster@teltek.es>
#
# This work is licensed under the Creative Commons Attribution-
# NonCommercial-ShareAlike 3.0 Unported License. To view a copy of 
# this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California, 94105, USA.

"""
"""

from galicaster.classui import message
from galicaster.core import context

from galicaster.utils.systemcalls import write_dconf_settings
from galicaster.utils.i18n import _

import ldap
from gi.repository import Gtk
from galicaster.core import core

def init():
    global conf, logger, bindings, default_bindings
    dispatcher = context.get_dispatcher()
    logger = context.get_logger()
    conf = context.get_conf()    
    dispatcher.connect('init', show_msg)

    bindings = conf.get_json('lockscreen', 'bindings')
    default_bindings = conf.get_json('lockscreen', 'defaultbindings')

def show_msg(element=None):
    global logger, bindings, conf
    logger.info("On init: write dconf bindings")
    write_dconf_settings(bindings, logger, logaserror=False)


    buttonDIS = show_buttons(core.DIS)
    buttonREC = show_buttons(core.REC)
    buttonMMA = show_buttons(core.MMA)

    text = {"title" : _("Lock screen"),
            "main" : _("Please insert the password")}

    show = []
    auth_method = conf.get_choice('lockscreen', 'authentication', ['basic', 'ldap'], 'basic')
    if auth_method == "ldap":
        show = ["username_label","username_entry"]
        text = {"title" : _("Lock screen"),
            "main" : _("LDAP authentication")}

    if buttonDIS is not None:
        buttonDIS.connect("clicked",lock,text,show)
    if buttonREC is not None:
        buttonREC.connect("clicked",lock,text,show)
    if buttonMMA is not None:
        buttonMMA.connect("clicked",lock,text,show)

    lock(None,text,show)
    
def lock(element,text,show):
    global logger
    message.PopUp(message.LOCKSCREEN, text,
                            context.get_mainwindow(),
                            None, response_action=on_unlock, close_on_response=False,show=show)
    logger.info("Galicaster locked")

def show_buttons(ui):
    global logger
    try:
        builder = context.get_mainwindow().nbox.get_nth_page(ui).gui    
    except Exception as error:
        logger.debug("La vista no existe")
        return None

    box = builder.get_object("box2")
    button = Gtk.Button()
    hbox = Gtk.Box()
    button.add(hbox)
    label = Gtk.Label("Lockscreen")
    label.set_padding(10,10)
    icon = Gtk.Image().new_from_icon_name("gtk-dialog-authentication",3)
    hbox.pack_start(label,True,True,0)
    hbox.pack_start(icon,True,True,0)
    box.pack_start(button,True,True,0)
    box.reorder_child(button,0)
    box.set_spacing(5)
    box.show_all()
    return button


def on_unlock(self, response=None, **kwargs):
    global conf, logger, default_bindings
    
    builder = kwargs.get('builder', None)
    popup = kwargs.get('popup', None)

    lentry = builder.get_object("unlockpass")
    userentry = builder.get_object("username_entry")

    auth_method = conf.get_choice('lockscreen', 'authentication', ['basic', 'ldap'], 'basic')
    if auth_method == "basic":
        if conf.get('lockscreen', 'password') == lentry.get_text():
            logger.info("Galicaster unlocked")
            popup.dialog_destroy()
            write_dconf_settings(default_bindings, logger, logaserror=False)
        else:
            lmessage = builder.get_object("lockmessage")
            lmessage.set_text("Wrong password")
    else:
        if connect_ldap(userentry.get_text(),lentry.get_text()):
            logger.info("Galicaster unlocked")
            popup.dialog_destroy()
            write_dconf_settings(default_bindings, logger, logaserror=False)
        else:
            lmessage = builder.get_object("lockmessage")
            lmessage.set_text("Wrong username/password")
        


def connect_ldap(user,password):
    global logger, conf
    
    ldapserver = conf.get("lockscreen","ldapserver")
    ldapserverport = conf.get("lockscreen","ldapserverport")
    ldapcn_list = conf.get_list("lockscreen","ldapcn")
    ldapou_list = conf.get_list("lockscreen","ldapou")
    ldapdc_list = conf.get_list("lockscreen","ldapdc")

    ldapOU = ""
    for x in ldapou_list:
        ldapOU += ", ou=" + x
    
    ldapCN = ""
    for x in ldapcn_list:
        ldapCN += ", cn=" + x

    ldapDC = ""
    for x in ldapdc_list:
        ldapDC += "dc=" + x

    l = ldap.initialize(ldapserver+":"+ldapserverport)
    username = "uid="+user+ldapOU+ldapCN+ldapDC
    
    try:
        l.protocol_version = ldap.VERSION3
        l.simple_bind_s(username, password)
        valid = True
        logger.info("Connect to LDAP server success with username: {}".format(user))
    except Exception as error:
        logger.info("Can't connect to to LDAP server: {}".format(error))
        return False
    return True
