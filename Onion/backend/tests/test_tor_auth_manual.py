"""Standalone check: can stem authenticate to the running tor.exe control port?"""

from stem.control import Controller

controller = Controller.from_port(address="127.0.0.1", port=9051)
controller.authenticate()
print("AUTH OK. Tor version:", controller.get_version())
print("Bootstrap status:", controller.get_info("status/bootstrap-phase"))
controller.close()
print("TOR AUTH TEST PASSED")
