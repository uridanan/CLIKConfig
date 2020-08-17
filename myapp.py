import sys
import os
import zipfile
import json
import six
import platform
from PySide2.QtWidgets import (QLabel, QLineEdit, QPushButton, QApplication, QVBoxLayout, QHBoxLayout, QDialog,
                               QMessageBox, QFileDialog, QFormLayout)

# TODO: GP - Add hockeyApp key
# TODO: GP - Add level to first popup and first popup at session
# TODO: GP - Add privacy settings
# TODO: GP - AppsFlyer does not need general app ID
# TODO: MacOS - control the output folder?
# TODO: MacOS - why can't the noconsole option write the files?
# TODO: Separate fields into sections
# TODO: Use Int field
# TODO: add to CL HC Product github
# TODO: create 2 button toggle
# TODO: GP - Add toggle iOS / Android


print 'Number of arguments:', len(sys.argv), 'arguments.'
print 'Argument List:', str(sys.argv)
class ApplicationFolder:
    MACOS = 'Darwin'

    @staticmethod
    def get_path():
        debug_mode = False
        if len(sys.argv) > 1 and sys.argv[1] == "debug":
            debug_mode = True

        if platform.system() == ApplicationFolder.MACOS and not debug_mode:
            return os.getcwd() + '/Desktop/CLIK Configurator'
        return os.getcwd()

    @staticmethod
    def get_full_path(file_name):
        return '/'.join([ApplicationFolder.get_path(), file_name])


class Logger:
    SILENT = 0
    INFO = 1
    DEBUG = 2

    def __init__(self, name, level):
        self.file_name = ApplicationFolder.get_full_path(name)
        self.log_level = level
        self.log_event(Logger.INFO, '------------------Start New Session------------------')
        self.log_event(Logger.INFO, 'Running on OS' + platform.system())
        self.log_event(Logger.INFO, 'Running in folder: ' + os.getcwd())

    def log_event(self, level, msg):
        if self.log_level >= level:
            with open(self.file_name, 'a') as log_file:
                log_file.write(msg + '\n')
                log_file.close()


logger = Logger('log.txt', Logger.DEBUG)


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
                ziph.write(os.path.join(root, file), file)
        ziph.close()

    def unzip(self, archive):
        dir_name = os.path.splitext(archive)[0]
        with zipfile.ZipFile(archive, 'r') as zip_ref:
            zip_ref.extractall(dir_name)
        return dir_name


class ConfigFile:

    def __init__(self, params):
        self.params = params

    def getConfig(self):
        return ""

    def getFileName(self):
        return ""

    def extract(self, data):
        pass

    def getArchiveName(self):
        suffix = self.params.general.bundleId
        if self.params.general.appId is not None and len(self.params.general.appId) > 0:
            suffix = self.params.general.appId
        return "CLIKConfig-" + suffix

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
        output = '/'.join([self.getTargetDir(), self.getFileName()])
        logger.log_event(Logger.DEBUG, 'save file: ' + output)
        with open(output, 'w') as jsonFile:
            json.dump(self.getConfig(), jsonFile, indent=2)

    def load(self):
        input_path = '/'.join([self.params.path, self.getFileName()])
        with open(input_path) as json_file:
            data = json.load(json_file)
            self.extract(data)


class Global(ConfigFile):

    def getConfig(self):
        mode = ""
        if self.params.general.useTestKeys:
            mode = "test"

        store = "google"
        if self.params.general.appId is not None and len(self.params.general.appId) > 0:
            store = "apple"

        cfg = {
                "bundleId": self.params.general.bundleId,
                "mode": mode,
                "store": store,
                "gameEngine": "unity",
                "appId": self.params.general.appId,
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
        self.params.general.bundleId = data["bundleId"]
        self.params.general.useTestKeys = data["mode"] == "test"


class AppsFlyer(ConfigFile):

    def getConfig(self):
        return {
                "appsFlyerKey": "8MAzUC3B2BHYVi2uYVHaSd",
                "appsFlyerAppId": self.params.general.appId
            }

    def getFileName(self):
        return "appsflyer.json"

    def extract(self, data):
        self.params.general.appId = data.get("appsFlyerAppId", "")


class Analytics(ConfigFile):

    def getConfig(self):
        cfg = {
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
        value = self.params.firebase.clientId.split('-')[0]
        return value

    def getStorageBucket(self):
        value = '.'.join([self.params.firebase.projectId, 'appspot.com'])
        return value

    def getDatabaseUrl(self):
        value = "https://"+self.params.firebase.projectId+".firebaseio.com"
        return value

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
        cfg = {"interstitialsAdMobKey": self.params.admob.interstitials}
        return cfg

    def getFileName(self):
        return "interstitials.json"

    def extract(self, data):
        self.params.admob.interstitials = data["interstitialsAdMobKey"]


class RewardedAds(ConfigFile):

    def getConfig(self):
        cfg = {"rewardedAdsAdMobKey": self.params.admob.rewardedAds}
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
        self.params.popups.resetOnRV = data["resetPopupTimerOnRVBySession"] is True


class Params:
    def __init__(self):
        self.path = None
        self.general = General()
        self.admob = Admob()
        self.firebase = Firebase()
        self.popups = Popups()


class General:
    def __init__(self):
        self.appId = ""
        self.bundleId = ""
        self.useTestKeys = False


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

    def setTimeBetween(self, value):
        self.timeBetween = {"1": [int(value)]}

    def setGameTime(self, value):
        self.gameTime = {"1": int(value)}

    def setSessionTime(self, value):
        self.sessionTime = {"1": int(value)}

    def setResetOnRV(self, toggle):
        value = toggle is True
        self.resetOnRV = {"1": value}


# Could have used PySide.QtGui.QFormLayout.addRow() or QGridLayout
# layout = QFormLayout()
# layout.addRow("Toggle: ", Toggle(ToggleState("green", "ON"), ToggleState("red", "OFF"), True).getWidget())
# layout.addRow(self.appleId.getLabel(), self.appleId.getLayout())

class LabelledWidget:
    def __init__(self, label, widget):
        self.label = QLabel(label)
        self.widget = widget
        self.layout = QHBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.widget)

    def getLabel(self):
        return self.label

    def getLayout(self):
        return self.layout

    def getWidget(self):
        return self.widget


# TODO: inherit from LabelledWidget
class LabelledInput:
    def __init__(self, label, default=""):
        self.label = QLabel(label)
        self.value = QLineEdit(default)
        self.layout = QHBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.value)

    def getLabel(self):
        return self.label

    def getLayout(self):
        return self.layout

    def getValue(self):
        return self.value.text()

    def setValue(self, value):
        if isinstance(value, six.string_types):
            self.value.setText(value)

class ToggleState:
    def __init__(self, color, text):
        self.color = color
        self.text = text

class Toggle:
    def __init__(self, checked_state, unchecked_state, is_default_checked):

        self.checked_state = checked_state
        self.unchecked_state = unchecked_state

        # Select default state
        self.default_state = unchecked_state
        if is_default_checked:
            self.default_state = checked_state

        self.widget = QPushButton(self.default_state.text)
        self.widget.setFixedWidth(50)
        self.widget.setFixedHeight(20)
        self.widget.setCheckable(True)
        self.widget.setStyleSheet("QPushButton{background-color: " + unchecked_state.color + ";} \
               QPushButton{background-color: " + unchecked_state.color + ";} \
               QPushButton{font-weight: bold;} \
               QPushButton{border: none;} \
               QPushButton:checked{background-color: " + checked_state.color + ";} \
               QPushButton:focus{border:none; }")
        self.widget.setChecked(is_default_checked)
        self.widget.toggled.connect(lambda:self.onToggle(self.widget))
        self.widget.isChecked()

    def getWidget(self):
        return self.widget

    def onToggle(self, instance):
        text = self.unchecked_state.text
        if instance.isChecked():
            text = self.checked_state.text
        instance.setText(text)


class Form(QDialog):

    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        self.setWindowTitle("CLIK Config")

        # Create widgets
        self.load = QPushButton("Load")
        self.bundleId = LabelledInput("Bundle Id")
        self.useTestKeys = LabelledWidget("Use Test Keys",
                        Toggle(ToggleState("blue", "YES"), ToggleState("green", "NO"), False).getWidget())
        self.appleId = LabelledInput("Apple App Id")
        self.testMode = LabelledInput("Using Test Keys")
        self.firebaseId = LabelledInput("Firebase App Id")
        self.firebaseClientId = LabelledInput("Firebase Client Id")
        self.firebaseProjectId = LabelledInput("Firebase Project Id")
        self.firebaseAPIKey = LabelledInput("Firebase API Key")
        self.admobId = LabelledInput("Admob App Id")
        self.admobBanners = LabelledInput("Admob Banners")
        self.admobInterstitials = LabelledInput("Admob Interstitials")
        self.admobRewardedAds = LabelledInput("Admob Rewarded Ads")
        self.popupsInterval = LabelledInput("Time Between Popups (sec)", "25")
        self.popupsGameTime = LabelledInput("Game time to first popup (sec)", "25")
        self.popupsSessionTime = LabelledInput("Session time to first popup (sec)", "15")
        self.popupsResetOnRV = LabelledWidget("Reset on RV", Toggle(ToggleState("blue", "YES"), ToggleState("green", "NO"), False).getWidget())
        self.save = QPushButton("Save")

        # Set dialog layout
        layout = QVBoxLayout()

        # Load Button
        layout.addWidget(self.load)

        # General
        layout.addLayout(self.bundleId.getLayout())
        layout.addLayout(self.useTestKeys.getLayout())
        layout.addLayout(self.appleId.getLayout())

        # Firebase
        layout.addLayout(self.firebaseId.getLayout())
        layout.addLayout(self.firebaseClientId.getLayout())
        layout.addLayout(self.firebaseProjectId.getLayout())
        layout.addLayout(self.firebaseAPIKey.getLayout())

        # Admob
        layout.addLayout(self.admobId.getLayout())
        layout.addLayout(self.admobBanners.getLayout())
        layout.addLayout(self.admobInterstitials.getLayout())
        layout.addLayout(self.admobRewardedAds.getLayout())

        # Popups
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
        config_data = self.loadConfig(zip_name)
        self.showConfig(config_data)

    def onSave(self):
        self.saveConfig(self.collectInput())
        msgBox = QMessageBox()
        msgBox.setText("Configuration saved")
        msgBox.exec_()

    def loadConfig(self, archive):
        params = Params()

        # Unzip
        params.path = Zipper("").unzip(archive[0])

        # Load files
        Global(params).load()
        AppsFlyer(params).load()
        Analytics(params).load()
        Banners(params).load()
        Interstitials(params).load()
        RewardedAds(params).load()
        PopupsMgr(params).load()

        return params

    def showConfig(self, params):
        self.bundleId.setValue(params.general.bundleId)
        self.useTestKeys.getWidget().setChecked(params.general.useTestKeys)
        self.appleId.setValue(params.general.appId)
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
        self.popupsResetOnRV.getWidget().setChecked(params.popups.resetOnRV)

    def collectInput(self):
        p = Params()
        p.general.bundleId = self.bundleId.getValue()
        p.general.useTestKeys = self.useTestKeys.getWidget().isChecked()
        p.general.appId = self.appleId.getValue()
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
        p.popups.setResetOnRV(self.popupsResetOnRV.getWidget().isChecked())
        return p

    def saveConfig(self, params):
        # params = self.collectInput()
        Global(params).save()
        AppsFlyer(params).save()
        Analytics(params).save()
        Banners(params).save()
        Interstitials(params).save()
        RewardedAds(params).save()
        PopupsMgr(params).save()
        Zipper(params.general.appId).zipdir()


if __name__ == '__main__':
    # Create the Qt Application
    app = QApplication(sys.argv)
    # Create and show the form
    form = Form()
    form.show()
    # Run the main Qt loop
    sys.exit(app.exec_())
