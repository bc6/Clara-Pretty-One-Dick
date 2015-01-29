#Embedded file name: reprocessing/ui\factory.py
from reprocessing.ui.containerCreator import ContainerCreator, Containers
from reprocessing.ui.controller import Controller
from reprocessing.ui.grouper import GetCategoryGrouper, GetGroupGrouper
from reprocessing.ui.inputGroups import InputGroups
from reprocessing.ui.inputItemAdder import InputItemAdder
from reprocessing.ui.itemContainers import InputItemContainerInterface, ItemContainerInterface
from reprocessing.ui.itemReprocessor import ItemReprocessor
from reprocessing.ui.outputItemAdder import MaterialFetcher, OutputItemAdder
from reprocessing.ui.quotes import Quotes
from reprocessing.ui.reprocessingWnd import CreateInputItemContainer, CreateOutputItemContainer, AskToContinue
from reprocessing.ui.states import States

def CreateReprocessingWindowController(wnd, inputInfoCont, outputInfoCont, invCache, reprocessing, GetActiveShip):
    quotes = Quotes(reprocessing)
    materialFetcher = MaterialFetcher(quotes)
    inputItemContainer = inputInfoCont
    inputItemContainer = InputItemContainerInterface(inputItemContainer)
    outputItemContainer = outputInfoCont
    outputItemContainer = ItemContainerInterface(outputItemContainer)
    inputGrouper = GetCategoryGrouper()
    inputGroups = InputGroups(inputItemContainer, inputGrouper)
    containerCreator = ContainerCreator(Containers(CreateInputItemContainer), Containers(CreateOutputItemContainer), quotes)
    inputItemAdder = InputItemAdder(inputItemContainer, containerCreator, quotes, States(quotes), inputGrouper, GetActiveShip)
    outputItemAdder = OutputItemAdder(materialFetcher, outputItemContainer, containerCreator, GetGroupGrouper())
    reprocessor = ItemReprocessor(reprocessing, invCache, AskToContinue)
    controller = Controller(wnd, inputItemAdder, inputGroups, quotes, outputItemAdder, reprocessor, GetActiveShip)
