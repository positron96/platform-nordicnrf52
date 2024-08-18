from os.path import join

from SCons.Script import COMMAND_LINE_TARGETS, DefaultEnvironment, SConscript


env = DefaultEnvironment()
platform = env.PioPlatform()

if "nobuild" not in COMMAND_LINE_TARGETS:
    SConscript(
        join(platform.get_package_dir(
            "framework-nrf5sdk"), "tools", "platformio-build.py"))
