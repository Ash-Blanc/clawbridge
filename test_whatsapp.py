import inspect
from agno.os.interfaces.whatsapp import Whatsapp
print(inspect.signature(Whatsapp.__init__))
