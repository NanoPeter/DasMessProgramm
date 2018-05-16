from PyQt5 import QtCore, QtWidgets, QtGui
from measurement.measurement import FloatValue, IntegerValue, StringValue


def delete_children(layout):
    """Delete all child layouts and widgets of a layout.
    
    This must be done before removing this layout from its parent.
    """
    while layout.count() > 0:
        child = layout.takeAt(0)
        if child.widget() is not None:
            child.widget().deleteLater()
        elif child.layout() is not None:
            delete_children(child.layout())


class DynamicInputLayout(QtWidgets.QVBoxLayout):

    # Qt-internal checks for different input widget types
    input_validators = {IntegerValue: QtGui.QIntValidator,
                        FloatValue: QtGui.QDoubleValidator,
                        StringValue: None}
    # TODO: Implement BooleanValue and DatetimeValue

    FIXED_WIDTH = 200
    
    def __init__(self, inputs):
        """
        Arguments:
            inputs: Dict[str, AbstractInput]: A dictionary of inputs as defined in SMU2Probe.inputs
        """
        super().__init__()

        self.__dynamic_inputs = dict()  # type: Dict[str, QLineEdit]

        self.__load_widgets(inputs)

    def __load_widgets(self, inputs):
        """Load widgets into this layout dynamically.

        Arguments:
            inputs: Dict[str, AbstractInput]: A dictionary of inputs as defined in SMU2Probe.inputs
        """
        for element in list(inputs.keys()):
            element_layout = QtWidgets.QVBoxLayout()
            element_layout.setSpacing(0)
            self.addLayout(element_layout)

            element_name = inputs[element].fullname
            element_layout.addWidget(QtWidgets.QLabel(element_name))  # Header text

            element_input_field = QtWidgets.QLineEdit()
            element_input_field.setFixedWidth(self.FIXED_WIDTH)
            self.__dynamic_inputs[element] = element_input_field
            element_layout.addWidget(element_input_field)

            # Validate the input field if it is numerical:
            element_type = type(inputs[element])
            element_input_validator = self.input_validators[element_type]
            if element_input_validator is not None:
                element_input_field.setValidator(element_input_validator())

            element_default = inputs[element].default
            element_input_field.setText(str(element_default))

    def get_inputs(self):
        """Return a dictionary of input names with their user-set values.

        Names are not the full names of an input but their dictionary index.
        """
        input_values = dict()
        for name in self.__dynamic_inputs:
            input_values[name] = self.__dynamic_inputs[name].text()

        return input_values
