import sys
import os
import zipfile
import json
import six
import platform
from PySide2.QtWidgets import (QLabel, QLineEdit, QPushButton, QApplication, QVBoxLayout, QHBoxLayout, QDialog, QMessageBox, QFileDialog)

#TODO: GP - AppsFlyer does not need apple app ID
#TODO: GP - Add toggle iOS / Android
#TODO: GP - Add bundle ID
#TODO: GP - Add test: True/False
#TODO: GP - Add hockeyApp key
#TODO: GP - Add level to first popup and first popup at session
#TODO: GP - Add privacy settings
#TODO: MacOS - control the output folder?
#TODO: MacOS - why can't the noconsole option write the files?
#TODO: Separate fields into sections
#TODO: Use Int field and bool toggles
#TODO: add to CL HC Product github

class ApplicationFolder:
    MACOS = 'Darwin'

    @staticmethod
    def get_path():
        if platform.system() == ApplicationFolder.MACOS:
            return os.getcwd() + '/Desktop/CLIK Configurator'
        return os.getcwd()

    @staticmethod
    def get_full_path(file_name):
        return '/'.join([ApplicationFolder.get_path(),file_name])


class Logger:
    SILENT = 0
    INFO = 1
    DEBUG = 2

    def __init__(self, name, level):
        self.file_name = ApplicationFolder.get_full_path(name)
        self.log_level = level
        self.log_event(Logger.INFO, '------------------Start New Session------------------')
        self.log_event(Logger.INFO,'Running on OS' + platform.system())
        self.log_event(Logger.INFO, 'Running in folder: ' + os.getcwd())

    def log_event(self,level,msg):
        if(self.log_level >= level):
            with open(self.file_name, 'a') as log_file:
                log_file.write(msg + '\n')
                log_file.close()

logger = Logger('log.txt',Logger.SILENT)


class Zipper:
    def __init__(self, app_id):
        self.appId = app_id
        self.archive = "CLIKConfig-" + self.appId
        self.zip_name = self.archive + '.zip'

    def pathName(self):
        return ApplicationFolder.get_full_path(self.archive)

    def zipName(self):
        return self.zip_name

    def zipdir(self):
        ziph = zipfile.ZipFile(ApplicationFolder.get_full_path(self.zipName()), 'w', zipfile.ZIP_DEFLATED)
        # ziph is zipfile handle
        for root, dirs, files in os.walk(self.pathName()):
            for file in files:
                ziph.write(os.path.join(root, file),file)
        ziph.close()

    def unzip(self, archive):
        dir_name = os.path.splitext(archive)[0]
        with zipfile.ZipFile(archive, 'r') as zip_ref:
            zip_ref.extractall(dir_name)
        return dir_name

class ConfigFile():

    def __init__(self, params):
        self.params = params

    def getConfig(self):
        return ""

    def getFileName(self):
        return ""

    def extract(self):
        pass

    def getArchiveName(self):
        return "CLIKConfig-" + self.params.apple.appId

    def getTargetDir(self):
        path = ApplicationFolder.get_full_path(self.getArchiveName())
        if not os.path.isdir(path):
            logger.log_event(Logger.DEBUG, 'create target dir: ' + path)
            self.createTargetDir(path)
        return path

    def createTargetDir(self, path):
        try:
            os.mkdir(path)
        except OSError as error:
            logger.log_event(Logger.DEBUG, 'FAILED create target dir: ' + path)
            print(error)

    def save(self):
        output = '/'.join([self.getTargetDir(),self.getFileName()])
        logger.log_event(Logger.DEBUG, 'save file: ' + output)
        with open(output, 'w') as jsonFile:
            json.dump(self.getConfig(), jsonFile, indent=2)

    def load(self):
        input = '/'.join([self.params.path,self.getFileName()])
        with open(input) as json_file:
            data = json.load(json_file)
            self.extract(data)



class Global(ConfigFile):

    def getConfig(self):
        cfg = {
                "store": "apple",
                "gameEngine": "unity",
                "appId": self.params.apple.appId,
                "audienceModeBuildOnly": "non-children",
                "orientation": "portrait",
                "appBuildConfig": {
                "admob": {
                  "application": self.params.admob.appId
                },
                "google": {}
                }
              }
        return cfg

    def getFileName(self):
        return "global.json"

    def extract(self, data):
        self.params.admob.appId = data["appBuildConfig"]["admob"]["application"]



class AppsFlyer(ConfigFile):

    def getConfig(self):
        return {
                "appsFlyerKey":"8MAzUC3B2BHYVi2uYVHaSd",
                "appsFlyerAppId":self.params.apple.appId
            }

    def getFileName(self):
        return "apsflyer.json"

    def extract(self, data):
        self.params.apple.appId = data["appsFlyerAppId"]


class Analytics(ConfigFile):

    def getConfig(self):
        cfg =  {
                  "geoLocationServer": "ttplugins.ttpsdk.info",
                  "firebase": {
                    "googleAppId": self.params.firebase.appId,
                    "senderId": self.getSenderId(),
                    "clientId": self.params.firebase.clientId,
                    "databaseURL": self.getDatabaseUrl(),
                    "storageBucket": self.getStorageBucket(),
                    "apiKey": self.params.firebase.apiKey,
                    "projectId": self.params.firebase.projectId
                  }
                }
        return cfg

    def getSenderId(self):
        id = self.params.firebase.clientId.split('-')[0]
        return id

    def getStorageBucket(self):
        id = '.'.join([self.params.firebase.projectId,'appspot.com'])
        return id

    def getDatabaseUrl(self):
        id = "https://"+self.params.firebase.projectId+".firebaseio.com"
        return id

    def getFileName(self):
        return "analytics.json"

    def extract(self, data):
        self.params.firebase.appId = data["firebase"]["googleAppId"]
        self.params.firebase.clientId = data["firebase"]["clientId"]
        self.params.firebase.projectId = data["firebase"]["projectId"]
        self.params.firebase.apiKey = data["firebase"]["apiKey"]


class Banners(ConfigFile):

    def getConfig(self):
        cfg = {
                  "alignToTop": False,
                  "adDisplayTime": 30,
                  "bannersAdMobKey": self.params.admob.banners,
                  "houseAdsServerDomain": "ttplugins.ttpsdk.info"
              }
        return cfg

    def getFileName(self):
        return "banners.json"

    def extract(self, data):
        self.params.admob.banners = data["bannersAdMobKey"]


class Interstitials(ConfigFile):

    def getConfig(self):
        cfg = {"interstitialsAdMobKey":self.params.admob.interstitials}
        return cfg

    def getFileName(self):
        return "interstitials.json"

    def extract(self, data):
        self.params.admob.interstitials = data["interstitialsAdMobKey"]



class RewardedAds(ConfigFile):

    def getConfig(self):
        cfg = {"rewardedAdsAdMobKey":self.params.admob.rewardedAds}
        return cfg

    def getFileName(self):
        return "rewardedads.json"

    def extract(self, data):
        self.params.admob.rewardedAds = data["rewardedAdsAdMobKey"]


class PopupsMgr(ConfigFile):

    def getConfig(self):
        cfg = {
                  "popupsIntervalsBySession": self.params.popups.timeBetween,
                  "gameTimeToFirstPopupBySession": self.params.popups.gameTime,
                  "sessionTimeToFirstPopupBySession": self.params.popups.sessionTime,
                  "resetPopupTimerOnRVBySession": self.params.popups.resetOnRV,
                  "levelToFirstPopup": 0,
                  "firstPopupAtSession": 1
              }
        return cfg

    def getFileName(self):
        return "popupsmgr.json"

    def extract(self, data):
        self.params.popups.gameTime = data["gameTimeToFirstPopupBySession"]
        self.params.popups.sessionTime = data["sessionTimeToFirstPopupBySession"]
        self.params.popups.timeBetween = data["popupsIntervalsBySession"]
        self.params.popups.resetOnRV = data["resetPopupTimerOnRVBySession"]


class Params:
    def __init__(self):
        self.path = None
        self.apple = Apple()
        self.admob = Admob()
        self.firebase = Firebase()
        self.popups = Popups()

class Apple:
    def __init__(self):
        self.appId = ""

class Admob:
    def __init__(self):
        self.appId = ""
        self.banners = ""
        self.interstitials = ""
        self.rewardedAds = ""

class Firebase:
    def __init__(self):
        self.appId = ""
        self.clientId = ""
        self.projectId = ""
        self.apiKey = ""

class Popups:
    def __init__(self):
        self.timeBetween = {"1": [25]}
        self.gameTime = {"1": 25}
        self.sessionTime = {"1": 15}
        self.resetOnRV = {"1": False}

    def setTimeBetween(self,str):
        self.timeBetween = {"1": [int(str)]}

    def setGameTime(self,str):
        self.gameTime = {"1": int(str)}

    def setSessionTime(self,str):
        self.sessionTime = {"1": int(str)}

    def setResetOnRV(self,str):
        value = str == True
        self.resetOnRV = {"1": value}


#Could have used PySide.QtGui.QFormLayout.addRow() or QGridLayout
class LabelledInput():
    def __init__(self,label,default=""):
        self.label = QLabel(label)
        self.value = QLineEdit(default)
        self.layout = QHBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.value)

    def getLayout(self):
        return self.layout

    def getValue(self):
        return self.value.text()

    def setValue(self,input):
        if isinstance(input, six.string_types):
            self.value.setText(input)


class Form(QDialog):

    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        self.setWindowTitle("CLIK Config")

        # Create widgets
        self.load = QPushButton("Load")
        self.appleId = LabelledInput("Apple App Id")
        self.firebaseId = LabelledInput("Firebase App Id")
        self.firebaseClientId = LabelledInput("Firebase Client Id")
        self.firebaseProjectId = LabelledInput("Firebase Project Id")
        self.firebaseAPIKey = LabelledInput("Firebase API Key")
        self.admobId = LabelledInput("Admob App Id")
        self.admobBanners = LabelledInput("Admob Banners")
        self.admobInterstitials = LabelledInput("Admob Interstitials")
        self.admobRewardedAds = LabelledInput("Admob Rewarded Ads")
        self.popupsInterval = LabelledInput("Time Between Popups (sec)","25")
        self.popupsGameTime = LabelledInput("Game time to first popup (sec)","25")
        self.popupsSessionTime = LabelledInput("Session time to first popup (sec)","15")
        self.popupsResetOnRV = LabelledInput("Reset on RV","False")
        self.save = QPushButton("Save")


        # Set dialog layout
        layout = QVBoxLayout()

        #Load Button
        layout.addWidget(self.load)

        #Apple
        layout.addLayout(self.appleId.getLayout())

        #Firebase
        layout.addLayout(self.firebaseId.getLayout())
        layout.addLayout(self.firebaseClientId.getLayout())
        layout.addLayout(self.firebaseProjectId.getLayout())
        layout.addLayout(self.firebaseAPIKey.getLayout())

        #Admob
        layout.addLayout(self.admobId.getLayout())
        layout.addLayout(self.admobBanners.getLayout())
        layout.addLayout(self.admobInterstitials.getLayout())
        layout.addLayout(self.admobRewardedAds.getLayout())

        #Popups
        layout.addLayout(self.popupsInterval.getLayout())
        layout.addLayout(self.popupsGameTime.getLayout())
        layout.addLayout(self.popupsSessionTime.getLayout())
        layout.addLayout(self.popupsResetOnRV.getLayout())

        layout.addWidget(self.save)
        self.setLayout(layout)

        self.save.clicked.connect(self.onSave)
        self.load.clicked.connect(self.onLoad)

    def onLoad(self):
        zip_name = QFileDialog.getOpenFileName(self, 'Open file', './', "Zip files (*.zip)")
        input = self.loadConfig(zip_name)
        self.showConfig(input)

    def onSave(self):
        self.saveConfig(self.collectInput())
        msgBox = QMessageBox()
        msgBox.setText("Configuration saved")
        msgBox.exec_()

    def loadConfig(self,input):
        params = Params()

        #Unzip
        params.path = Zipper("").unzip(input[0])

        #Load files
        Global(params).load()
        AppsFlyer(params).load()
        Analytics(params).load()
        Banners(params).load()
        Interstitials(params).load()
        RewardedAds(params).load()
        PopupsMgr(params).load()

        return params

    def showConfig(self,params):
        self.appleId.setValue(params.apple.appId)
        self.firebaseId.setValue(params.firebase.appId)
        self.firebaseClientId.setValue(params.firebase.clientId)
        self.firebaseProjectId.setValue(params.firebase.projectId)
        self.firebaseAPIKey.setValue(params.firebase.apiKey)
        self.admobId.setValue(params.admob.appId)
        self.admobBanners.setValue(params.admob.banners)
        self.admobInterstitials.setValue(params.admob.interstitials)
        self.admobRewardedAds.setValue(params.admob.rewardedAds)
        self.popupsInterval.setValue(params.popups.timeBetween)
        self.popupsGameTime.setValue(params.popups.gameTime)
        self.popupsSessionTime.setValue(params.popups.sessionTime)
        self.popupsResetOnRV.setValue(params.popups.resetOnRV)


    def collectInput(self):
        p = Params()
        p.apple.appId = self.appleId.getValue()
        p.firebase.appId = self.firebaseId.getValue()
        p.firebase.clientId = self.firebaseClientId.getValue()
        p.firebase.projectId = self.firebaseProjectId.getValue()
        p.firebase.apiKey = self.firebaseAPIKey.getValue()
        p.admob.appId = self.admobId.getValue()
        p.admob.banners = self.admobBanners.getValue()
        p.admob.interstitials = self.admobInterstitials.getValue()
        p.admob.rewardedAds = self.admobRewardedAds.getValue()
        p.popups.setTimeBetween(self.popupsInterval.getValue())
        p.popups.setGameTime(self.popupsGameTime.getValue())
        p.popups.setSessionTime(self.popupsSessionTime.getValue())
        p.popups.setResetOnRV(self.popupsResetOnRV.getValue())
        return p

    def saveConfig(self,params):
        #params = self.collectInput()
        Global(params).save()
        AppsFlyer(params).save()
        Analytics(params).save()
        Banners(params).save()
        Interstitials(params).save()
        RewardedAds(params).save()
        PopupsMgr(params).save()
        Zipper(params.apple.appId).zipdir()



if __name__ == '__main__':
    # Create the Qt Application
    app = QApplication(sys.argv)
    # Create and show the form
    form = Form()
    form.show()
    # Run the main Qt loop
    sys.exit(app.exec_())


