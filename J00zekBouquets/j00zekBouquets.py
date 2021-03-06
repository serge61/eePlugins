﻿# -*- coding: utf-8 -*-
#######################################################################
#
#   Coded by j00zek (c)2014/2015/2016/2017
#
#######################################################################

from inits import * 
from Components.ActionMap import ActionMap
from Components.config import *
from Components.ConfigList import ConfigList, ConfigListScreen
from Components.Console import Console
from Components.FileList import FileList, EXTENSIONS
from Components.Label import Label
from enigma import eDVBDB, eServiceReference, eTimer, eConsoleAppContainer
from j00zekConsole import j00zekConsole
from os import system as os_system, remove as os_remove, chmod as os_chmod, symlink as os_symlink #fsync as os_fsync, rename as os_rename, walk as os_walk, listdir, mkdir as os_mkdir
from Screens.InfoBar import InfoBar
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Tools.BoundFunction import boundFunction
from Tools.Directories import fileExists, resolveFilename, pathExists, SCOPE_PLUGINS, SCOPE_SKIN_IMAGE

config.plugins.j00zek = ConfigSubsection()
j00zekConfig = config.plugins.j00zek
j00zekConfig.separator = NoSave(ConfigNothing())

j00zekConfig.chlistEnabled = ConfigYesNo(default = True)
j00zekConfig.chlistServerIP = ConfigText(default = "192.168.1.5", fixed_size = False)
j00zekConfig.chlistServerLogin = ConfigText(default = "root", fixed_size = False)
j00zekConfig.chlistServerPass = ConfigPassword(default = "root", fixed_size = False)
j00zekConfig.chlistServerHidden = ConfigYesNo(default = False)
j00zekConfig.syncPLtransponders = NoSave(ConfigYesNo(default = False))

j00zekConfig.BouquetsEnabled = ConfigYesNo(default = True)
j00zekConfig.BouquetsNC = ConfigSelection(default = "NA", choices = [("NA", "Nie odświerzaj"),
                                                                                      ("49188PL", "HotBird-PL"),
                                                                                      ("49188", "HotBird"),
                                                                                      ("49186", "HotBird & Astra")
                                                                                      ])
j00zekConfig.BouquetsCP = ConfigSelection(default = "NA", choices = [("NA", "Nie odświerzaj"),
                                                                                      ("CP", "Hotbird"),
                                                                                      #("CPPL", "Cyfrowy Polsat-PL")
                                                                                      ])

j00zekConfig.BouquetsClearLameDB = ConfigSelection(default = "norefresh", choices = [("all", "Tak, wszystkie satelity"),
                                                                                      ("pl", "Tak, tylko 'polskie' transpondery"),
                                                                                      ("norefresh", "Nie")
                                                                                      ])
j00zekConfig.BouquetsExcludeBouquet = ConfigYesNo(default = False)
j00zekConfig.BouquetsAction = ConfigSelection(default = "prov", choices = [("prov", "Tworzenie bukietu z układem dostawcy"), ("1st", "Aktualizacja pierwszego bukietu na liście"), ("all", "Aktualizacja pierwszego i Tworzenie bukietu z układem dostawcy")])

j00zekConfig.Clear1st = ConfigYesNo(default = False)

#oscam synchro
j00zekConfig.BouquetsOscam = ConfigYesNo(default = True)
j00zekConfig.BouquetsOscamConfig = ConfigDirectory(default = 'NIEZNANY')
if j00zekConfig.BouquetsOscamConfig.value == 'NIEZNANY':
    try:
        if pathExists(config.plugins.AltSoftcam.camconfig.value):
            j00zekConfig.BouquetsOscamConfig.value = config.plugins.AltSoftcam.camconfig.value
    except:
        for folder in ['/etc/oscam','/var/keys']:
            if fileExists("%s/oscam.conf" % folder):
                j00zekConfig.BouquetsOscamConfig.value = folder
                break

j00zekConfig.Bouquets_srvid = ConfigYesNo(default = False) #PID > Name assigments "0100,0B01:428A|nc+|Filmbox Arthouse"
#local card config helpers
j00zekConfig.Bouquets_caid = ConfigSelection(default = "unknown", choices = [("unknown", 'Nie ustawiono'), ("0100", "NC+ Seca (0100)"), ("0B01", "NC+ Conax (0B01)"), ("0B01", "NC+ Mix"), ("1803", "Polsat (1803)")])
j00zekConfig.Bouquets_Packet = ConfigSelection(default = "unknown", choices = [("unknown", 'Nie ustawiono'), ("scan", "Skanowanie automatyczne")]) #, ("ncstart", "NC-Start+"), ("nccomfort", "NC-Comfort+"), ("ncextra", "NC-Extra+")])
j00zekConfig.Bouquets_services = ConfigYesNo(default = False) #Assigment of PIDs to [j00zekBouquets-packet] 
j00zekConfig.Bouquets_dvbapi = ConfigYesNo(default = False) #we need to know what packet user has

BackupFile='KopiaListyKanalow.tar.gz'
##############################################################

class j00zekBouquets(Screen, ConfigListScreen):

    skin = """
    <screen name="j00zekBouquets" position="60,260" size="600,400" title="j00zekBouquets @j00zek" >
            <widget name="config" position="10,10" size="580,330" zPosition="1" transparent="0" scrollbarMode="showOnDemand" />
            <widget name="key_red" position="0,340" zPosition="2" size="300,30" valign="center" halign="center" font="Regular;22" transparent="1" foregroundColor="red" />
            <widget name="key_green" position="300,340" zPosition="2" size="300,30" valign="center" halign="center" font="Regular;22" transparent="1" foregroundColor="green" />
            <widget name="key_yellow" position="0,370" zPosition="2" size="300,30" valign="center" halign="center" font="Regular;22" transparent="1" foregroundColor="yellow" />
            <widget name="key_blue" position="300,370" zPosition="2" size="300,30" valign="center" halign="center" font="Regular;22" transparent="1" foregroundColor="blue" />
    </screen>"""

    onChangedEntry = [ ]
    LastIndex=0
    CurrIndex=0
    j00zekBouquetsBin=''
        
    def __init__(self, session):
        Screen.__init__(self, session)

        
        self.list = [ ]
        ConfigListScreen.__init__(self, self.list, session = session, on_change = self.changedEntry)
        self["actions"] = ActionMap(["j00zekBouquets"],
            {
                "cancel": self.keyCancel,
                "ok": self.keyOK,
                "red": self.keyRed,
                "green": self.keyGreen,
                "yellow": self.keyYellow,
                "blue": self.keyBlue,
            }, -2)

        self["key_red"] = Label('Załaduj z pliku tar.gz')
        self["key_green"] = Label('Utwórz archiwum tar.gz')
        self["key_blue"] = Label("Pobierz z tunera")
        self["key_yellow"] = Label("Pobierz z satelity")
        
        self.timer = eTimer()
        
        self.onLayoutFinish.append(self.layoutFinished)

    def layoutFinished(self):
        self.setTitle("Wersja %s" % Info)
        with open("/proc/sys/vm/drop_caches", "w") as f: f.write("1\n")
        self.runSetup()

    def runSetup(self):
        self.list = [ ]
        self.list.append(getConfigListEntry('Czyszczenie lamedb:', j00zekConfig.BouquetsClearLameDB))
        self.list.append(getConfigListEntry(' ', j00zekConfig.separator))
        self.list.append(getConfigListEntry('--- Synchronizacja z tunera ---', j00zekConfig.chlistEnabled))
        if j00zekConfig.chlistEnabled.value == True:
            self.list.append(getConfigListEntry('Pobierz listę z tunera:', j00zekConfig.chlistServerIP))
            self.list.append(getConfigListEntry("Konto:", j00zekConfig.chlistServerLogin))
            self.list.append(getConfigListEntry('Hasło:', j00zekConfig.chlistServerPass))
            
        self.list.append(getConfigListEntry(' ', j00zekConfig.separator))
        self.list.append(getConfigListEntry('--- Synchronizacja z satelity ---', j00zekConfig.BouquetsEnabled))
        if j00zekConfig.BouquetsEnabled.value == True:
            self.list.append(getConfigListEntry('nc+:', j00zekConfig.BouquetsNC))
            if j00zekConfig.BouquetsNC.value == '49188PL':
                self.list.append(getConfigListEntry('Synchronizuj listę TR,SID z web:', j00zekConfig.syncPLtransponders))
            self.list.append(getConfigListEntry('Cyfrowy Polsat:', j00zekConfig.BouquetsCP))
            if j00zekConfig.BouquetsNC.value != 'NA' or j00zekConfig.BouquetsCP.value != 'NA':
                self.list.append(getConfigListEntry('Akcja:', j00zekConfig.BouquetsAction))
                if j00zekConfig.BouquetsAction.value == '1st' or j00zekConfig.BouquetsAction.value == 'all':
                    self.list.append(getConfigListEntry("Usuń nieznane pozycje z bukietu:", j00zekConfig.Clear1st))
                self.list.append(getConfigListEntry("Pomiń zdefiniowane kanały:", j00zekConfig.BouquetsExcludeBouquet))
                
                self.list.append(getConfigListEntry(" ", j00zekConfig.separator))                
                self.list.append(getConfigListEntry("--- Synchronizacja nazw kanałów w oscamie ---", j00zekConfig.BouquetsOscam))
                if j00zekConfig.BouquetsOscam.value is True:
                    self.list.append(getConfigListEntry('Katalog konfiguracyjny oscam-a:', j00zekConfig.BouquetsOscamConfig))
                    if fileExists("%s/oscam.srvid" % j00zekConfig.BouquetsOscamConfig.value):
                        self.list.append(getConfigListEntry('Aktualizacja nazw serwisów:', j00zekConfig.Bouquets_srvid))
                    else:
                        j00zekConfig.Bouquets_srvid.value = False
                        self.list.append(getConfigListEntry("Nie znaleziono pliku oscam.srvid", j00zekConfig.separator))

        self["config"].list = self.list
        self["config"].setList(self.list)
    
    def changedEntry(self):
        print "Index: %d" % self["config"].getCurrentIndex()
        for x in self.onChangedEntry:
            x()

    def ConfigureJB(self):
        if pathExists('%scomponents/zapNC.config' % PluginPath) is False:
            self.ZapNC=("1:0:1:1139:2AF8:13E:820000:0:0:0:")
        else:
            with open('%scomponents/zapNC.config' % PluginPath, 'r') as ZAPconfig:
                tmp=ZAPconfig.readline().split('"')[1]
                self.ZapNC=(tmp)
                ZAPconfig.close()
        if pathExists('%scomponents/zapCP.config' % PluginPath) is False:
            self.ZapCP=("1:0:1:3396:3390:71:820000:0:0:0:")
        else:
            with open('%scomponents/zapCP.config' % PluginPath, 'r') as ZAPconfig:
                tmp=ZAPconfig.readline().split('"')[1]
                self.ZapCP=(tmp)
                ZAPconfig.close()
        self.BouquetsNCBin='%scomponents/j00zekBouquetsNC' % (PluginPath)
        self.BouquetsCPBin='%scomponents/j00zekBouquetsCP' % (PluginPath)
        self.ExcludedSIDsTemplate='%scomponents/excludedSIDs.template' % PluginPath
        self.ExcludedSIDsFileName='userbouquet.excludedSIDs.j00zekAutobouquet.tv'
        self.ExcludedSIDsFile='/etc/enigma2/%s' % self.ExcludedSIDsFileName
        self.IncludedTranspondersTemplate='%scomponents/PLtransponders.cfg' % PluginPath
        self.IncludedTranspondersFile='/tmp/transponders.PL'
        self.runlist = []
        self.runlist.append(('[ -f /tmp/.ChannelsNotUpdated ] && rm -f /tmp/.ChannelsNotUpdated 2>/dev/null'))
        if pathExists('%s/components/CheckType.sh' % PluginPath) is True:
            self.runlist.append(('chmod 755 %s/components/*.sh' % PluginPath))
            self.runlist.append(('%s/components/CheckType.sh' % PluginPath))
        
        self.ZapTo=""
        
        #tylko polskie transpondery
        if j00zekConfig.BouquetsNC.value.endswith('PL'):
            if not pathExists(self.IncludedTranspondersFile):
                os_symlink(self.IncludedTranspondersTemplate,self.IncludedTranspondersFile)
        else:
            if pathExists(self.IncludedTranspondersFile):
                os_remove(self.IncludedTranspondersFile)
        #kanaly do pominiecia
        if j00zekConfig.BouquetsExcludeBouquet.value == True:
            self.ExcludeSIDS="ExcludeSIDS"
            ExcludedSIDsFileNeedsUpdate=1
            if pathExists(self.ExcludedSIDsFile) is False:
                from shutil import copy as shutil_copy
                shutil_copy(self.ExcludedSIDsTemplate,self.ExcludedSIDsFile)
        else:
            self.ExcludeSIDS=""
            ExcludedSIDsFileNeedsUpdate=0
            
        #sprawdzamy schemat pliku bouquets.tv
        hasNewline=1
        if j00zekConfig.BouquetsNC.value !="NA":
            ncNeedsUpdate=1
        else:
            ncNeedsUpdate=0
        if j00zekConfig.BouquetsCP.value !="NA":
            cpNeedsUpdate=1
        else:
            cpNeedsUpdate=0
                
        windowsEOL=''
        with open("/etc/enigma2/bouquets.tv", "r") as bouquetsTV:
            for line in bouquetsTV:
                if windowsEOL == '' and line.endswith('\r\n'):
                    windowsEOL='\r'
                if line.endswith('\n'):
                    hasNewline=1
                else:
                    hasNewline=0
                if line.find(self.ExcludedSIDsFileName) > 0:
                    ExcludedSIDsFileNeedsUpdate=0
                if line.find('userbouquet.ncplus.j00zekAutobouquet.tv') > 0:
                    ncNeedsUpdate=0
                if line.find('userbouquet.CP.j00zekAutobouquet.tv') > 0:
                    cpNeedsUpdate=0
            bouquetsTV.close()
        #dopisujemy nasze bukiety
        if ncNeedsUpdate == 1:
            with open("/etc/enigma2/bouquets.tv", "a") as bouquetsTV:
                if hasNewline == 0:
                    bouquetsTV.write('\n')
                bouquetsTV.write('#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "userbouquet.ncplus.j00zekAutobouquet.tv" ORDER BY bouquet%s\n' % windowsEOL)
                bouquetsTV.close()
                hasNewline=1
        if cpNeedsUpdate == 1:
            with open("/etc/enigma2/bouquets.tv", "a") as bouquetsTV:
                if hasNewline == 0:
                    bouquetsTV.write('\n')
                bouquetsTV.write('#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "userbouquet.CP.j00zekAutobouquet.tv" ORDER BY bouquet%s\n' % windowsEOL)
                bouquetsTV.close()
                hasNewline=1
        if ExcludedSIDsFileNeedsUpdate == 1:
            with open("/etc/enigma2/bouquets.tv", "a") as bouquetsTV:
                if hasNewline == 0:
                    bouquetsTV.write('\n')
                bouquetsTV.write('#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "%s" ORDER BY bouquet%s\n' % (self.ExcludedSIDsFileName,windowsEOL))
                bouquetsTV.close()
        
        if j00zekConfig.BouquetsNC.value == '49188PL' and j00zekConfig.syncPLtransponders.value == True:
             self.runlist.append('%scomponents/SyncFromWeb.sh' % PluginPath)
        if j00zekConfig.BouquetsNC.value != 'NA':
            self.runlist.append("%s %s %s %s %s" % ( self.BouquetsNCBin, j00zekConfig.BouquetsNC.value, \
                                j00zekConfig.BouquetsAction.value, self.ZapNC, self.ExcludeSIDS))
            self.ZapTo=self.ZapNC
        if j00zekConfig.BouquetsCP.value != 'NA':
            self.runlist.append("%s %s %s %s %s" % ( self.BouquetsCPBin, j00zekConfig.BouquetsCP.value, \
                                j00zekConfig.BouquetsAction.value, self.ZapCP, self.ExcludeSIDS))
            if self.ZapTo == "":
                self.ZapTo = self.ZapCP
        if j00zekConfig.BouquetsAction.value in ("1st","all") and  j00zekConfig.Clear1st.value == True:
            self.runlist.append(('%s/components/clear1st.sh' % PluginPath))
        return

    def ConfigOscamUpdate(self):
        if j00zekConfig.BouquetsOscam.value is True:
            self.runlist.append('%s/components/j00zekOscamUpdater "%s" "%s" "%s" "%s" "%s" "%s" "%s"' % (PluginPath, 
                                                                   j00zekConfig.Bouquets_srvid.value,
                                                                        j00zekConfig.Bouquets_caid.value,
                                                                             j00zekConfig.Bouquets_Packet.value,
                                                                                  j00zekConfig.Bouquets_services.value,
                                                                                       j00zekConfig.Bouquets_dvbapi.value,
                                                                                            j00zekConfig.BouquetsOscamConfig.value,
                                                                                                j00zekConfig.BouquetsAction.value))
        return
    
    def keyYellow(self):
        try:
            openWebifState = config.OpenWebif.enabled.value
            OpenWebifAuth = config.OpenWebif.auth.value
        except:
            openWebifState = None
            OpenWebifAuth = None
        if j00zekConfig.BouquetsEnabled.value == False:
            return
        elif openWebifState is None:
            self.session.openWithCallback(self.doNothing ,MessageBox,"nie zainstalowano wtyczki OpenWebif - kończę!!!", MessageBox.TYPE_INFO)
            return
        elif openWebifState == False:
            self.session.openWithCallback(self.doNothing ,MessageBox,"Interfejs OpenWebif jest wyłączony - kończę!!!", MessageBox.TYPE_INFO)
            return
        elif OpenWebifAuth == True:
            self.session.openWithCallback(self.doNothing ,MessageBox,"OpenWebif wymaga zalogowania- kończę!!!", MessageBox.TYPE_INFO)
            return
        elif j00zekConfig.BouquetsNC.value != 'NA' or j00zekConfig.BouquetsCP.value != 'NA':
            self.SaveSettings()
            #stopping playing service
            self.prev_root = InfoBar.instance.servicelist.getRoot()
            self.prev_running_service = self.session.nav.getCurrentlyPlayingServiceReference()
            self.session.nav.stopService()
            #cleaningLAMEDB
            if j00zekConfig.BouquetsClearLameDB.value != "norefresh":
                self.ClearLameDB()
                self.BuildLameDB()
            else:
                eDVBDB.getInstance().loadServicelist('%scomponents/j00zekBouquets.lamedb' % PluginPath)
            #configuring excluded SIDs
            #zap to channel on transponder, we use it as hack to simplify selection of the NIM
            self.ConfigureJB()
            self.ConfigOscamUpdate()

            service = eServiceReference(self.ZapTo)
            InfoBar.instance.servicelist.clearPath()
            InfoBar.instance.servicelist.enterPath(service)
            InfoBar.instance.servicelist.setCurrentSelection(service)
            InfoBar.instance.servicelist.zap()
            self.timer.callback.append(self.keyYellowStep2)
            self.timer.start(500,1) # j00zekBouquets waits for e2 to tune.
        return

    def keyYellowStep2(self):
        self.timer.callback.remove(self.keyYellowStep2)
        self.session.openWithCallback(self.keyYellowEndRun ,j00zekConsole, title = "j00zekBouquets v %s (%s, %s)" % (Info, j00zekConfig.BouquetsClearLameDB.value, j00zekConfig.BouquetsNC.value ) , cmdlist = self.runlist)
        
    def keyYellowEndRun(self, ret =0):
        self.reloadLAMEDB()
        self.ZapToPrevChannel()

    def ClearLameDB(self, ret =0):
        #e2 de facto dodaje nowe serwisy a nie przeladowuje lamedb, wiec musimy najperw wszystkie wykasowac...#
        #RESULT removeServices(int dvb_namespace=-1, int tsid=-1, int onid=-1, unsigned int orb_pos=0xFFFFFFFF);
        db = eDVBDB.getInstance()
        if j00zekConfig.BouquetsClearLameDB.value == "all":
            SatPositions=[50,70,90,100,130,160,192,215,235,255,260,284,305,313,330,360,390,400,420,450,490,530,550,570,600,620,642,685,705,720,750,800,852]
            for sat in SatPositions:
                db.removeServices(-1, -1, -1, sat)
        elif j00zekConfig.BouquetsClearLameDB.value == "pl":
            tsid=[0x001a,0x0064,0x0065,0x00c8,0x012c,0x0190,0x02bc,0x03e8,0x044c,0x0514,0x05dc,0x0640,0x1388,0x13ef,0x1518,
                  0x1af4,0x1b58,0x1c20,0x1ce8,0x1e14,0x1e78,0x1edc,0x1fa4,0x22c4,0x23f0,0x24b8,0x251c,0x2580,0x26ac,0x2af8,
                  0x2bc0,0x2c88,0x2cec,0x2d50,0x2db4,0x2e7c,0x2ee0,0x2f44,0x2fa8,0x3070,0x3138,0x319c,0x3200,0x332c,0x3390,
                  0x33f4,0x3c28,0x3cf0,0x3db8,0x3e1c]
            for ts in tsid:
                db.removeServices(-1, ts, -1, 130)

    def BuildLameDB(self):
        # ... teraz dodac to co potrzebujemy :)            
        eDVBDB.getInstance().loadServicelist('%scomponents/j00zekBouquets.lamedb' % PluginPath)
        eDVBDB.getInstance().saveServicelist()

    def reloadLAMEDB(self):
        eDVBDB.getInstance().reloadServicelist()
        eDVBDB.getInstance().reloadBouquets()

    def ZapToPrevChannel(self):
        if InfoBar.instance.servicelist.getRoot() != self.prev_root: #already in correct bouquet?
            InfoBar.instance.servicelist.clearPath()
            if InfoBar.instance.servicelist.getRoot() != self.prev_root:
                InfoBar.instance.servicelist.enterPath(InfoBar.instance.servicelist.bouquet_root)
            InfoBar.instance.servicelist.enterPath(self.prev_root)
        if self.prev_running_service:
            InfoBar.instance.servicelist.setCurrentSelection(self.prev_running_service) #select the service in servicelist
            self.session.nav.playService(self.prev_running_service)
    
    def keyBlue(self):
        self.SaveSettings()
        if j00zekConfig.chlistEnabled.value == True:
            self.session.openWithCallback(self.keyBlueYESNO ,MessageBox,'Pobrać z tunera %s teraz?' % j00zekConfig.chlistServerIP.value, MessageBox.TYPE_YESNO)
        return
        
    def keyBlueYESNO(self, ret):
        if ret is True:
            self.runlist = []
            self.runlist=[("%s/components/CHlistSynchro.sh %s %s %s" % (PluginPath,
                                                            j00zekConfig.chlistServerIP.value,
                                                              j00zekConfig.chlistServerLogin.value,
                                                                  j00zekConfig.chlistServerPass.value))]
            self.session.openWithCallback(self.j00zekConsoleEndRun ,j00zekConsole, title = "Channels list synchronization", cmdlist = self.runlist)
        return

    def keyRed(self):
        self.session.openWithCallback(self.keyRedYESNO ,MessageBox,"Załadować nową listę z pen-a teraz?", MessageBox.TYPE_YESNO)
        return
        
    def keyRedYESNO(self, ret):
        def SetDirPathCallBack(newPath):
            if None != newPath:
                confPath = resolveFilename(SCOPE_CONFIG, '')
                self.runlist = [('cd /'),
                                ('echo "Rozpakowywanie archiwum %s..."' % newPath),
                                ('tar -xzvf %s' % newPath)
                                ]
                self.session.openWithCallback(self.j00zekConsoleEndRun ,j00zekConsole, title = "Rozpakowywanie archiwum...", cmdlist = self.runlist, endText = '\nNowa lista zainstalowana, naciśnij OK')
            return
        if ret is True:
            self.session.openWithCallback(boundFunction(SetDirPathCallBack), DirectorySelectorWidget, currDir='/', title='Wybierz archiwum listy kanałów', FileMode=True, searchpattern="^.*\.(tgz|tar\.gz)")
        return
      
    def keyGreen(self):
        def SetDirPathCallBack(newPath):
            if None != newPath:
                if newPath.endswith('/'):
                    newPath = newPath[0:-1]
                confPath = resolveFilename(SCOPE_CONFIG, '')
                if confPath.endswith('/'):
                    confPath = confPath[0:-1]
                self.runlist = [('cd /'),
                                ('echo "Tworzenie archiwum %s/%s..."' % (newPath,BackupFile)),
                                ('tar -czvf %s/%s %s/lamedb* %s/*.tv %s/*.radio' % (newPath,BackupFile,confPath,confPath,confPath))
                                ]
                self.session.openWithCallback(self.doNothing ,j00zekConsole, title = "Tworzenie archiwum %s..." % BackupFile, cmdlist = self.runlist, endText = '\nKopia wykonana, naciśnij OK')
            return
        self.session.openWithCallback(boundFunction(SetDirPathCallBack), DirectorySelectorWidget, currDir='/', title='Wybierz katalog do zapisu archiwum listy kanałów')
        return
        
    def j00zekConsoleEndRun(self, ret =0):
        if ret == 0:
            #self.session.openWithCallback(self.j00zekConsoleEndRunClear ,MessageBox,"Clear channels list before updating?", MessageBox.TYPE_YESNO)
            if j00zekConfig.BouquetsClearLameDB.value != "norefresh":
                self.j00zekConsoleEndRunClear(True)
            else:
                self.j00zekConsoleEndRunClear(False)
        return

    def doNothing(self, ret = None):
        pass
        
    def j00zekConsoleEndRunClear(self, ret):
        if ret is True:
            self.ClearLameDB()
            self.BuildLameDB()
        self.reloadLAMEDB()
      
    def SaveSettings(self):
        for x in self["config"].list:
            x[1].save()
        configfile.save()
    
    def keyOK(self): #openpliPC - F2 emuluje green
        curIndex = self["config"].getCurrentIndex()
        currItem = self["config"].list[curIndex][1]
        if isinstance(currItem, ConfigDirectory):
            def SetDirPathCallBack(curIndex, newPath):
                if None != newPath:
                    self["config"].list[curIndex][1].value = newPath
                    self.runSetup()
            if os_path.isdir(j00zekConfig.BouquetsOscamConfig.value):
                self.session.openWithCallback(boundFunction(SetDirPathCallBack, curIndex), DirectorySelectorWidget, currDir=j00zekConfig.BouquetsOscamConfig.value, title='Wybierz katalog z konfiguracją OsCam-a')
            else:
                self.session.openWithCallback(boundFunction(SetDirPathCallBack, curIndex), DirectorySelectorWidget, currDir='/', title='Wybierz katalog z konfiguracją OsCam-a')

    def keyCancel(self):
        for x in self["config"].list:
            x[1].cancel()
        self.close()
        
    def keyLeft(self):
        ConfigListScreen.keyLeft(self)
        self.keyRightLeftActions()

    def keyRight(self):
        ConfigListScreen.keyRight(self)
        self.keyRightLeftActions()
            
    def keyRightLeftActions(self):
        if (self["config"].getCurrent()[1] == j00zekConfig.chlistEnabled or 
              self["config"].getCurrent()[1] == j00zekConfig.BouquetsEnabled or
              self["config"].getCurrent()[1] == j00zekConfig.Bouquets_caid or
              self["config"].getCurrent()[1] == j00zekConfig.Bouquets_Packet or
              self["config"].getCurrent()[1] == j00zekConfig.BouquetsNC or
              self["config"].getCurrent()[1] == j00zekConfig.BouquetsCP or
              self["config"].getCurrent()[1] == j00zekConfig.BouquetsClearLameDB or
              self["config"].getCurrent()[1] == j00zekConfig.BouquetsAction or
              self["config"].getCurrent()[1] == j00zekConfig.BouquetsOscam
              ):
            self.runSetup()
#### ####################################################################################################################################################
class DirectorySelectorWidget(Screen):
    skin = """
    <screen name="DirectorySelectorWidget" position="center,center" size="620,440" title="">
            <widget name="key_red"      position="10,10"  zPosition="2"  size="600,35" valign="center"  halign="left"   font="Regular;22" transparent="1" foregroundColor="red" />
            <widget name="key_blue"     position="10,10"  zPosition="2"  size="600,35" valign="center"  halign="center" font="Regular;22" transparent="1" foregroundColor="blue" />
            <widget name="key_green"    position="10,10"  zPosition="2"  size="600,35" valign="center"  halign="right"  font="Regular;22" transparent="1" foregroundColor="green" />
            <widget name="key_yellow"   position="10,10"  zPosition="2"  size="600,35" valign="center"  halign="center"  font="Regular;22" transparent="1" foregroundColor="yellow" />
            <widget name="curr_dir"     position="10,50"  zPosition="2"  size="600,35" valign="center"  halign="left"   font="Regular;18" transparent="1" foregroundColor="white" />
            <widget name="filelist"     position="10,85"  zPosition="1"  size="580,335" transparent="1" scrollbarMode="showOnDemand" />
    </screen>"""
    def __init__(self, session, currDir, title="Select directory", FileMode=False, searchpattern=""):
        print("DirectorySelectorWidget.__init__ -------------------------------")
        Screen.__init__(self, session)
        # for the skin: first try MediaPlayerDirectoryBrowser, then FileBrowser, this allows individual skinning
        #self.skinName = ["MediaPlayerDirectoryBrowser", "FileBrowser" ]
        self["key_red"]    = Label(_("Cancel"))
        self["key_yellow"] = Label(_("Refresh"))
        #self["key_blue"]   = Label(_("New directory"))
        self["key_green"]  = Label(_("Select"))
        self["curr_dir"]   = Label(_(" "))
        self.filelist      = FileList(directory=currDir, matchingPattern=searchpattern, showFiles=FileMode)
        self.FileMode      = FileMode
        self["filelist"]   = self.filelist
        self["FilelistActions"] = ActionMap(["SetupActions", "ColorActions"],
            {
                "green" : self.use,
                "red"   : self.exit,
                "yellow": self.refresh,
                "ok"    : self.ok,
                "cancel": self.exit
            })
        self.title = title
        self.onLayoutFinish.append(self.layoutFinished)
        self.onClose.append(self.__onClose)

    def __del__(self):
        print("DirectorySelectorWidget.__del__ -------------------------------")

    def __onClose(self):
        print("DirectorySelectorWidget.__onClose -----------------------------")
        self.onClose.remove(self.__onClose)
        self.onLayoutFinish.remove(self.layoutFinished)

    def layoutFinished(self):
        print("DirectorySelectorWidget.layoutFinished -------------------------------")
        self.setTitle(_(self.title))
        self.currDirChanged()

    def currDirChanged(self):
        self["curr_dir"].setText(self.getCurrentDirectory())
        
    def getCurrentDirectory(self):
        currDir = self["filelist"].getCurrentDirectory()
        if currDir and os_path.isdir( currDir ):
            return currDir
        else:
            return "/"

    def use(self):
        if self.FileMode:
          selection = self["filelist"].getSelection()
          self.close( "%s/%s" % (self.filelist.getCurrentDirectory(),selection[0]) )
        else:
          self.close( self.getCurrentDirectory() )

    def exit(self):
        self.close(None)

    def ok(self):
        if self.filelist.canDescent():
            self.filelist.descent()
        self.currDirChanged()

    def refresh(self):
        self["filelist"].refresh()
