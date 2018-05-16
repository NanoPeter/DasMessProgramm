from PyQt5 import QtCore, QtWidgets, QtGui
from measurement.measurement import FloatValue, IntegerValue, StringValue


class DynamicInputLayout(QtWidgets.QVBoxLayout):

    # Qt-internal checks for different input widget types
    input_validators = {IntegerValue: QtGui.QIntValidator,
                        FloatValue: QtGui.QDoubleValidator,
                        StringValue: None}
    # TODO: Implement BooleanValue and DatetimeValue
    
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
            self.__dynamic_inputs[element] = element_input_field
            element_layout.addWidget(element_input_field)

            # Validate the input field if it is numerical:
            element_type = type(inputs[element])
            element_input_validator = self.input_validators[element_type]
            if element_input_validator is not None:
                element_input_field.setValidator(element_input_validator())

            element_default = inputs[element].default
            element_input_field.setText(str(element_default))
        
