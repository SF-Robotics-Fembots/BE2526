"""A module for controlling peristaltic pumps using the Aqueduct framework.

This demo program initializes a PeristalticPump device, sets the pump to run
continuously at a specific flow rate, and then reverses the direction of the
pump's rotation after a certain amount of time has passed. The program continuously
checks the flow rate of the pump and sends new start commands to reverse
the direction if the flow rate reaches 0.
"""
from aqueduct.core.aq import Aqueduct
from aqueduct.core.aq import InitParams
from aqueduct.devices.pump import PeristalticPump

# parse initialization parameters and create Aqueduct instance
params = InitParams.parse()
aq = Aqueduct(params.user_id, params.ip_address, params.port)

# initialize the devices and set a command delay
aq.initialize(params.init)
aq.set_command_delay(0.05)

# get the peristaltic pump device and create a command object
pump: PeristalticPump = aq.devices.get("peristaltic_pump_000001")
commands = pump.make_commands()
c = pump.make_start_command(
    mode=pump.MODE.Continuous,
    rate_units=pump.RATE_UNITS.MlMin,
    rate_value=2,
    direction=pump.STATUS.Clockwise,
)

# set the command for each channel and start the pump
for i in range(0, pump.len):
    pump.set_command(commands, i, c)

pump.start(commands)

# set the maximum speed and speed increment for the pump
MAX_SPEED: float = 50
INCREMENT: float = 0.1

# calculate the number of steps based on the maximum speed and increment
STEPS = int(MAX_SPEED / INCREMENT)

# loop through the speed increment steps
while True:
    for i in range(0, STEPS):
        commands = pump.make_commands()

        # create a command to change the pump speed
        c = pump.make_change_speed_command(
            rate_value=i * INCREMENT, rate_units=pump.RATE_UNITS.MlMin
        )

        # set the command for each channel and change the pump speed
        for i in range(0, pump.len):
            pump.set_command(commands, i, c)

        pump.change_speed(commands)

    # loop through the speed decrement steps
    for i in range(STEPS, 0, -1):
        commands = pump.make_commands()

        # create a command to change the pump speed
        c = pump.make_change_speed_command(
            rate_value=i * INCREMENT, rate_units=pump.RATE_UNITS.MlMin
        )

        # set the command for each channel and change the pump speed
        for i in range(0, pump.len):
            pump.set_command(commands, i, c)

        pump.change_speed(commands)