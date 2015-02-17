#Embedded file name: eve/client/script/ui/shared\canNotStartTrainingWindow.py
import carbonui.const as uiconst
import uiprimitives
import uicontrols
from eve.client.script.ui.control.buttons import BigButton
import localization
import uthread

class CanNotStartTrainingClass(uicontrols.ContainerAutoSize):
    __guid__ = 'uicls.CanNotStartTrainingClass'

    def ApplyAttributes(self, attributes):
        uicontrols.ContainerAutoSize.ApplyAttributes(self, attributes)
        charactersTrainingCount = attributes.messageData['charactersTrainingCount']
        if charactersTrainingCount == 1:
            mainText = localization.GetByLabel('UI/DualTraining/TrainingOnAnotherCharacter', characterName=attributes.messageData['charName1'], loggedInCharacterName=cfg.eveowners.Get(session.charid).ownerName)
        else:
            mainText = localization.GetByLabel('UI/DualTraining/TrainingOnThirdCharacter', characterName=attributes.messageData['charName1'], characterName2=attributes.messageData['charName2'], loggedInCharacterName=cfg.eveowners.Get(session.charid).ownerName)
        uicontrols.Label(parent=self, align=uiconst.TOTOP, text=mainText, padLeft=10, padRight=10)
        text = '<center>' + localization.GetByLabel('UI/DualTraining/ToAcquirePLEX')
        uicontrols.EveCaptionMedium(parent=self, align=uiconst.TOTOP, text=text, padTop=10)
        cont = uiprimitives.Container(parent=self, align=uiconst.TOTOP, height=40, padTop=15)
        btn = BigButton(parent=cont, width=180, height=40, align=uiconst.CENTER)
        btn.SetSmallCaption(localization.GetByLabel('UI/DualTraining/BuyOnEveMarket'), inside=1)
        btn.OnClick = self.OpenMarketWindow
        btn.Startup(180, 40, 0)
        cont2 = uiprimitives.Container(parent=self, align=uiconst.TOTOP, height=40, padTop=15)
        btn2 = BigButton(parent=cont2, width=180, height=40, align=uiconst.CENTER)
        btn2.SetSmallCaption(localization.GetByLabel('UI/DualTraining/BuyOnline'), inside=1)
        btn2.OnClick = uicore.cmd.BuyPlexOnline
        btn2.Startup(180, 40, 0)

    def OpenMarketWindow(self, *args):
        uthread.new(sm.GetService('marketutils').ShowMarketDetails, const.typePilotLicence, None)

    def GetContentHeight(self):
        _, h = self.GetAbsoluteSize()
        return h
