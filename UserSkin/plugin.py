# -*- coding: utf-8 -*-

# UserSkin, based on AtileHD concept by schomi & plnick
#
# maintainer: j00zek
#
# extension for openpli, all skins, descriptions, bar selections and other @j00zek 2014/2015
# Uszanuj czyj�� prac� i NIE przyw�aszczaj sobie autorstwa!

#This plugin is free software, you are allowed to
#modify it (if you keep the license),
#but you are not allowed to distribute/publish
#it without source code (this version and your modifications).
#This means you also have to distribute
#source code of your modifications.

from debug import printDEBUG
from inits import *
from translate import _

from Components.ActionMap import ActionMap

from Components.config import *
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.Sources.List import List
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Tools.Directories import resolveFilename, pathExists,SCOPE_SKIN
from Tools.LoadPixmap import LoadPixmap
#from Tools import Notifications
#import shutil
#import re
        
def Plugins(**kwargs):
    return [PluginDescriptor(name=_("UserSkin Setup"), description=_("Personalize your Skin"), where = PluginDescriptor.WHERE_MENU, fnc=menu)]

def menu(menuid, **kwargs):
    if menuid == "vtimain" or menuid == "system":
        return [(_("Setup - UserSkin") + " " + CurrentSkinName, main, "UserSkin_Menu", 40)]
    return []

def main(session, **kwargs):
    printDEBUG("Opening Menu ...")
    session.open(UserSkin_Menu)

def readSkinConfig():
    skinHistory = False
    skinUpdate = False
    skinAddOns = False
    skinComponents = False
    if pathExists("%s%s" % (SkinPath,'skin.config')):
        with open("%s%s" % (SkinPath,'skin.config'), 'r') as cf:
            for cfg in cf:
                if cfg[:8] == "history=":
                    skinHistory = True
                if cfg[:8] == "skinurl=":
                    skinUpdate = True
                if cfg[:7] == "addons=":
                    skinAddOns = True
                if cfg[:11] == "components=":
                    skinComponents = True
    return skinHistory, skinUpdate, skinAddOns, skinComponents
  
class UserSkin_Menu(Screen):
        skin = """
<screen position="center,center" size="560,320">
        <widget source="list" render="Listbox" position="0,0" size="560,320" scrollbarMode="showOnDemand">
                <convert type="TemplatedMultiContent">
                        {"template": [
                                MultiContentEntryPixmapAlphaTest(pos = (12, 2), size = (40, 40), png = 0),
                                MultiContentEntryText(pos = (58, 2), size = (500, 40), font=0, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = 1),
                                ],
                                "fonts": [gFont("Regular", 24)],
                                "itemHeight": 44
                        }
                </convert>
        </widget>
</screen>"""

        def __init__(self, session):
                Screen.__init__(self, session)
                self.setup_title = _("UserSkinMenu")
                Screen.setTitle(self, self.setup_title)
                self["list"] = List()
                self["setupActions"] = ActionMap(["SetupActions", "MenuActions"],
                {
                        "cancel": self.quit,
                        "ok": self.openSelected,
                        "menu": self.quit,
                }, -2)
                self.setTitle(_("UserSkin menu %s") % UserSkinInfo)
                self.createsetup()

        def createsetup(self):
                skinHistory, skinUpdate, skinAddOns, skinComponents = readSkinConfig()
                l = [(self.buildListEntry(_("Skin personalization"), "config.png",'config'))]
                
                l.append(self.buildListEntry(_("miniTV skin creator"), "lcd.png",'LCDskin')),
                    
                if skinUpdate:
                    l.append(self.buildListEntry(_("Update main skin"), "skin.png",'getskin')),
                if skinAddOns:
                    l.append(self.buildListEntry(_("Download addons"), "addon.png",'getaddons'))
                   
                #l.append(self.buildListEntry(_("Delete addons"), "remove.png",'delete_addons')),

                if skinComponents:
                    l.append(self.buildListEntry(_("Download additional Components/plugins"), "plugin.png",'getcomponents'))

                l.append(self.buildListEntry(_("List loaded screens"), "import.png",'ListScreens')),

                if skinHistory:
                    l.append(self.buildListEntry(_("History of changes"), "history.png",'history')),
                l.append(self.buildListEntry(_("Import foreign skin"), "import.png",'importskin')),
                l.append(self.buildListEntry(_("About"), "about.png",'about')),
                self["list"].list = l

        def buildListEntry(self, description, image, optionname):
                pixmap = LoadPixmap(getPixmapPath(image))
                return((pixmap, description, optionname))

        def refresh(self):
            index = self["list"].getIndex()
            self.createsetup()
            if index is not None and len(self["list"].list) > index:
                self["list"].setIndex(index)
            else:
                self["list"].setIndex(0)

        def rebootQuestion(self):
            def rebootQuestionAnswered(ret):
                if ret:
                    from enigma import quitMainloop
                    quitMainloop(3)
                    self.quit()
                return
            if pathExists("/tmp/.rebootGUI"):
                self.session.openWithCallback(rebootQuestionAnswered, MessageBox,_("Restart GUI now?"),  type = MessageBox.TYPE_YESNO, timeout = 10, default = False)
          
          
        def openSelected(self):
            selected = str(self["list"].getCurrent()[2])
            if selected == 'about':
                from about import UserSkin_About
                self.session.openWithCallback(self.refresh,UserSkin_About)
                return
            elif selected == 'config':
                from skinconfig import UserSkin_Config
                self.session.openWithCallback(self.quit,UserSkin_Config)
                return
            elif selected == 'LCDskin':
                from miniTVskinner import miniTVskinner
                self.session.openWithCallback(self.LCDskinRet,miniTVskinner)
                return
            elif selected == 'ListScreens':
                from ScreensLister import ScreensLister
                self.session.openWithCallback(self.doNothing,ScreensLister)
                return
            elif selected == 'getaddons':
                from myComponents import myMenu
                self.session.openWithCallback(self.refresh, myMenu, MenuFolder = '%sscripts' % PluginPath, MenuFile = '_Getaddons', MenuTitle = _("Download addons"))
                return
            elif selected == 'delete_addons':
                from myComponents import myMenu
                self.session.openWithCallback(self.refresh, myMenu, MenuFolder = '%sscripts' % PluginPath, MenuFile = '_Deleteaddons', MenuTitle = _("Delete addons"))
                return
            elif selected == 'getcomponents':
                from myComponents import myMenu
                self.session.openWithCallback(self.rebootQuestion, myMenu, MenuFolder = '%sscripts' % PluginPath, MenuFile = '_Getcomponents', MenuTitle = _("Download additional Components/plugins"))
                return
            elif selected == 'importskin':
                from myComponents import myMenu
                self.session.openWithCallback(self.refresh, myMenu, MenuFolder = '%sImportSkinScripts' % PluginPath, MenuFile = '_Skins2Import', MenuTitle = _("Import foreign skin"))
                return
            elif selected == 'getskin':
                def goUpdate(ret):
                    if ret is True:
                        from myComponents import UserSkinconsole
                        runlist = []
                        runlist.append( ('chmod 755 %sscripts/SkinUpdate.sh' % PluginPath) )
                        runlist.append( ('%sscripts/SkinUpdate.sh %s' % (PluginPath,SkinPath)) )
                        self.session.openWithCallback(self.rebootQuestion, UserSkinconsole, title = _("Updating skin"), cmdlist = runlist)
                    return
                    
                self.session.openWithCallback(goUpdate, MessageBox,_("Do you want to update skin?"),  type = MessageBox.TYPE_YESNO, timeout = 10, default = False)
                return
            elif selected == 'history':
                from myComponents import UserSkinconsole
                self.session.openWithCallback(self.refresh, UserSkinconsole, title = _("History of changes"), cmdlist = [ '%sscripts/SkinHistory.sh %s' % (PluginPath,SkinPath) ])
                return

        def LCDskinRet(self, retDict = None):
            if retDict is not None:
                print retDict
                from miniTVskinner import miniTVskinner
                self.session.openWithCallback(self.LCDskinRet,miniTVskinner)
            return
              
        def doNothing(self):
            return
                
        def quit(self):
            self.close()
