
class Sourcemeter2400(object):
        def __init__(self, device):
                self.__dev = device
               
        def voltage_driven(self, voltage, current_limit=1e-6, nplc=1):
                self.__dev.write('*RST')
                self.__dev.write(':sense:function "current"')
                self.__dev.write(':source:function voltage')
                self.__dev.write(':source:voltage:range:auto on') 
                self.__dev.write(':sense:current:range:auto on') 
                self.__dev.write(':sense:current:protection {0}'.format(current_limit)) 
                self.__dev.write(':sense:current:nplcycles {}'.format(nplc)) 
                self.__dev.write(':sense:average off') 
                self.__dev.write(':output:state 0') 
                self.__dev.write(':source:voltage:level {0}'.format(voltage)) 
                self.__dev.write(":format:elements voltage, current") 
                
        def current_driven(self, current, voltage_limit=1, nplc=1):
                self.__dev.write('*RST')
                self.__dev.write(':sense:function "voltage"')
                self.__dev.write(':source:function current')
                self.__dev.write(':source:current:range:auto on') 
                self.__dev.write(':sense:voltage:range:auto on') 
                self.__dev.write(':sense:voltage:protection {0}'.format(voltage_limit)) 
                self.__dev.write(':sense:voltage:nplcycles {}'.format(nplc)) 
                self.__dev.write(':sense:average off') 
                self.__dev.write(':output:state 0') 
                self.__dev.write(':source:current:level {0}'.format(current))
                self.__dev.write(":format:elements voltage, current")  
 
        def arm(self):
                self.__dev.write(':output:state 1')

        def disarm(self):
                self.__dev.write(':output:state 0')
           
        def set_voltage(self, voltage):
                self.__dev.write(':source:voltage:level {0}'.format(voltage))

        def set_current(self, current):
                self.__dev.write(':source:current:level {0}'.format(current))

        def read(self):
                return self.__dev.ask(':read?')


