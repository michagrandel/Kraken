"""Kraken - objects.components.component_input input module.

Classes:
ComponentInput -- Component input representation.

"""

from kraken.core.objects.scene_item import SceneItem


class ComponentInput(SceneItem):
    """Component Input Object."""

    def __init__(self, name, parent, dataType):
        super(ComponentInput, self).__init__(name, parent=parent)
        self.dataType = None
        self.connection = None
        self.target = None
        self.index = 0

        self.setDataType(dataType)


    # =================
    # DataType Methods
    # =================
    def setDataType(self, dataType):
        """Sets the data type for this input.

        Arguments:
        dataType -- String, type of input source.

        Return:
        True if successful.

        """

        self.dataType = dataType

        return True


    def getDataType(self):
        """Returns the data type for this input.

        Return:
        String, data type of this input.

        """

        return self.dataType


    # ====================
    # Connections Methods
    # ====================
    def isConnected(self):
        """Checks if there is a connection.

        Return:
        Boolean, whether it is connected or not.

        """

        return self.connection is not None


    def getConnection(self):
        """Gets the connection of this input.

        Return:
        Connection object or None if not set.

        """

        return self.connection


    def setConnection(self, connectionObj):
        """Sets the connection to the component output.

        Arguments:
        connectionObj -- ComponentOutput, output object to connect to.

        Return:
        True if successful.

        """

        if connectionObj.getDataType() != self.getDataType() and connectionObj.getDataType()[:-2] != self.getDataType():
            raise Exception("Data Type mismatch! Cannot connect '" +
                connectionObj.getDataType() + "' to '" + self.getDataType())

        if connectionObj is self.getConnection():
            raise Exception("'connectionObj' is already set as the connection.")

        self.connection = connectionObj

        connectionObj._addConnection(self)

        return True


    # ===============
    # Target Methods
    # ===============
    def setTarget(self, target):
        """Sets the taret for this input.

        Arguments:
        target -- Object, kraken object that is the target of this input.

        Return:
        True if successful.

        """

        self.target = target


    def getTarget(self):
        """Returns the target of the input.

        Return:
        Object, the target of the input.

        """

        return self.target


    # ==============
    # Index Methods
    # ==============
    def getIndex(self):
        """Gets the index of the connection.

        Return:
        Integer, the index of the connection.

        """

        return self.index


    def setIndex(self, index):
        """Sets the index of the connection.

        Arguments:
        Index -- Integer, the index to set this to.

        Return:
        True if successful.

        """

        self.index = index

        return True