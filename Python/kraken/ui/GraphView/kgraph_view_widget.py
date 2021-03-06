import json, difflib
import os
import traceback

from PySide import QtGui, QtCore

from contextual_node_list import ContextualNodeList
from graph_view.graph_view_widget import GraphViewWidget
from kgraph_view import KGraphView
from kraken.ui.undoredo.undo_redo_manager import UndoRedoManager
import graph_commands

from kraken.core.objects.rig import Rig
from kraken import plugins


def GetKrakenPath():
    if 'KRAKEN_PATH' in os.environ:
        return os.environ['KRAKEN_PATH']
    return os.path.expanduser("~")


class KGraphViewWidget(GraphViewWidget):

    rigNameChanged = QtCore.Signal()

    def __init__(self, parent=None):

        # constructors of base classes
        super(KGraphViewWidget, self).__init__(parent)


        graphView = KGraphView(parent=self)
        graphView.nodeAdded.connect(self.__onNodeAdded)
        graphView.nodeRemoved.connect(self.__onNodeRemoved)
        graphView.beginConnectionManipulation.connect(self.__onBeginConnectionManipulation)
        graphView.endConnectionManipulation.connect(self.__onEndConnectionManipulationSignal)
        graphView.connectionAdded.connect(self.__onConnectionAdded)
        graphView.connectionRemoved.connect(self.__onConnectionRemoved)

        graphView.selectionChanged.connect(self.__onSelectionChanged)
        graphView.endSelectionMoved.connect(self.__onSelectionMoved)

        graphView.beginDeleteSelection.connect(self.__onBeginDeleteSelection)
        graphView.endDeleteSelection.connect(self.__onEndDeleteSelection)

        self.setGraphView(graphView)

        #########################
        ## Setup hotkeys for the following actions.

        undoShortcut = QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_Z), self)
        undoShortcut.activated.connect(self.undo)

        redoShortcut = QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_Y), self)
        redoShortcut.activated.connect(self.redo)

        openContextualNodeListShortcut = QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_QuoteLeft), self)
        openContextualNodeListShortcut.activated.connect(self.openContextualNodeList)

        self.newRigPreset()


    def editRigName(self):
        dialog = QtGui.QInputDialog(self)
        dialog.setObjectName('RigNameDialog')
        text, ok = dialog.getText(self, 'Edit Rig Name', 'New Rig Name', text=self.guideRig.getName())

        if ok is True:
            self.setRigName(text)


    def setRigName(self, text):
        self.guideRig.setName(text)
        self.rigNameChanged.emit()


    def newRigPreset(self):
        # TODO: clean the rig from the scene if it has been built.
        self.guideRig = Rig()
        self.getGraphView().displayGraph(self.guideRig)
        self.setRigName('MyRig')


    def saveRigPreset(self):
        settings = self.window().getSettings()
        settings.beginGroup('Files')
        lastFilePath = settings.value("lastFilePath", os.path.join(GetKrakenPath(), self.guideRig.getName() ))
        settings.endGroup()
        (filePath, filter) = QtGui.QFileDialog.getSaveFileName(self, 'Save Rig Preset', lastFilePath, 'Kraken Rig (*.krg)')
        if len(filePath) > 0:
            self.synchGuideRig()
            self.guideRig.writeRigDefinitionFile(filePath)

            settings.beginGroup('Files')
            lastFilePath = settings.setValue("lastFilePath", filePath)
            settings.endGroup()


    def loadRigPreset(self):
        settings = self.window().getSettings()
        settings.beginGroup('Files')
        lastFilePath = settings.value("lastFilePath", os.path.join(GetKrakenPath(), self.guideRig.getName() ))
        settings.endGroup()
        (filePath, filter) = QtGui.QFileDialog.getOpenFileName(self, 'Load Rig Preset', lastFilePath, 'Kraken Rig (*.krg)')
        if len(filePath) > 0:
            self.guideRig = Rig()
            self.guideRig.loadRigDefinitionFile(filePath)
            self.graphView.displayGraph( self.guideRig )
            # self.nameWidget.setText( self.guideRig.getName() )

            settings.beginGroup('Files')
            lastFilePath = settings.setValue("lastFilePath", filePath)
            settings.endGroup()


    def buildGuideRig(self):

        try:
            self.window().statusBar().showMessage('Building Guide')

            builder = plugins.getBuilder()

            if self.guideRig.getName().endswith('_guide') is False:
                self.guideRig.setName(self.guideRig.getName() + '_guide')

            builder.build(self.guideRig)

        except Exception as e:
            print traceback.format_exc()

            statusBar = self.window().statusBar()
            warningLabel = QtGui.QLabel('Error Building: ' + ', '.join([x for x in e.args]))
            warningLabel.setMaximumWidth(200)
            warningLabel.setStyleSheet("QLabel { border-radius: 3px; background-color: #AA0000}")

            def addWarning():
                self.window().statusBar().clearMessage()

                statusBar.addWidget(warningLabel, 1)
                statusBar.repaint()

                timer.start()

            def endWarning():
                timer.stop()
                statusBar.removeWidget(warningLabel)
                statusBar.repaint()

                self.window().statusBar().showMessage('Ready', 2000)

            timer = QtCore.QTimer()
            timer.setInterval(2000)
            timer.timeout.connect(endWarning)

            addWarning()


    def synchGuideRig(self):
        synchronizer = plugins.getSynchronizer()
        synchronizer.setTarget(self.guideRig)
        synchronizer.sync()


    def buildRig(self):

        try:
            self.window().statusBar().showMessage('Building Rig')

            self.synchGuideRig()

            rigBuildData = self.guideRig.getRigBuildData()
            rig = Rig()
            rig.loadRigDefinition(rigBuildData)

            rig.setName(rig.getName().replace('_guide', ''))

            builder = plugins.getBuilder()
            builder.build(rig)

        except Exception as e:
            print traceback.format_exc()

            statusBar = self.window().statusBar()
            warningLabel = QtGui.QLabel('Error Building: ' + ', '.join([x for x in e.args]))
            warningLabel.setMaximumWidth(200)
            warningLabel.setStyleSheet("QLabel { border-radius: 3px; background-color: #AA0000}")

            def addWarning():
                self.window().statusBar().clearMessage()

                statusBar.addWidget(warningLabel, 1)
                statusBar.repaint()

                timer.start()

            def endWarning():
                timer.stop()
                statusBar.removeWidget(warningLabel)
                statusBar.repaint()

                self.window().statusBar().showMessage('Ready', 2000)

            timer = QtCore.QTimer()
            timer.setInterval(2000)
            timer.timeout.connect(endWarning)

            addWarning()

    # =========
    # Shortcuts
    # =========
    def copy(self):
        graphView = self.getGraphView()
        pos = graphView.getSelectedNodesCentroid()
        graphView.copySettings(pos)


    def paste(self):
        graphView = self.getGraphView()
        clipboardData = self.graphView.getClipboardData()

        pos = clipboardData['copyPos'] + QtCore.QPoint(20, 20)
        graphView.pasteSettings(pos, mirrored=False, createConnectionsToExistingNodes=True)


    def pasteUnconnected(self):
        graphView = self.getGraphView()
        clipboardData = self.graphView.getClipboardData()

        pos = clipboardData['copyPos'] + QtCore.QPoint(20, 20)
        graphView.pasteSettings(pos, mirrored=False, createConnectionsToExistingNodes=False)


    def pasteMirrored(self):
        graphView = self.getGraphView()
        clipboardData = self.graphView.getClipboardData()

        pos = clipboardData['copyPos'] + QtCore.QPoint(20, 20)
        graphView.pasteSettings(pos, mirrored=True, createConnectionsToExistingNodes=False)


    def pasteMirroredConnected(self):
        graphView = self.getGraphView()
        clipboardData = self.graphView.getClipboardData()

        pos = clipboardData['copyPos'] + QtCore.QPoint(20, 20)
        graphView.pasteSettings(pos, mirrored=True, createConnectionsToExistingNodes=True)


    def undo(self):
        UndoRedoManager.getInstance().undo()

    def redo(self):
        UndoRedoManager.getInstance().redo()


    def openContextualNodeList(self):
        pos = self.mapFromGlobal(QtGui.QCursor.pos());

        contextualNodeList = ContextualNodeList(self)

        scenepos = self.graphView.mapToScene(pos)
        contextualNodeList.showAtPos(pos, scenepos, self.graphView)

    # ===============
    # Signal Handlers
    # ===============

    def __onNodeAdded(self, node):
        if not UndoRedoManager.getInstance().isUndoingOrRedoing():
            command = graph_commands.AddNodeCommand(self.graphView, self.guideRig, node)
            UndoRedoManager.getInstance().addCommand(command)


    def __onNodeRemoved(self, node):
        node.getComponent().detach()

        if not UndoRedoManager.getInstance().isUndoingOrRedoing():
            command = graph_commands.RemoveNodeCommand(self.graphView, self.guideRig, node)
            UndoRedoManager.getInstance().addCommand(command)


    def __onBeginConnectionManipulation(self):
        UndoRedoManager.getInstance().openBracket('Connect Ports')


    def __onEndConnectionManipulationSignal(self):
        UndoRedoManager.getInstance().closeBracket()


    def __onConnectionAdded(self, connection):
        if not UndoRedoManager.getInstance().isUndoingOrRedoing():
            command = graph_commands.ConnectionAddedCommand(self.graphView, self.guideRig, connection)
            UndoRedoManager.getInstance().addCommand(command)


    def __onConnectionRemoved(self, connection):
        if not UndoRedoManager.getInstance().isUndoingOrRedoing():
            command = graph_commands.ConnectionRemovedCommand(self.graphView, self.guideRig, connection)
            UndoRedoManager.getInstance().addCommand(command)


    def __onSelectionChanged(self, deselectedNodes, selectedNodes):
        if not UndoRedoManager.getInstance().isUndoingOrRedoing():
            command = graph_commands.SelectionChangeCommand(self.graphView, deselectedNodes, selectedNodes)
            UndoRedoManager.getInstance().addCommand(command)


    def __onSelectionMoved(self, nodes, delta):
        for node in nodes:
            node.pushGraphPosToComponent()

        if not UndoRedoManager.getInstance().isUndoingOrRedoing():
            command = graph_commands.NodesMoveCommand(self.graphView, nodes, delta)
            UndoRedoManager.getInstance().addCommand(command)


    def __onBeginDeleteSelection(self):
        UndoRedoManager.getInstance().openBracket('Delete Nodes')


    def __onEndDeleteSelection(self):
        UndoRedoManager.getInstance().closeBracket()