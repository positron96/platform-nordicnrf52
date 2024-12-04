import sys
from os.path import isdir, join
from os import listdir
import re

from SCons.Script import DefaultEnvironment

env = DefaultEnvironment()
platform = env.PioPlatform()
board = env.BoardConfig()

FRAMEWORK_DIR = platform.get_package_dir("framework-nrf5sdk")
assert isdir(FRAMEWORK_DIR)

sdk_dir = join(FRAMEWORK_DIR, 'sdk')
components_dir = join(sdk_dir, 'components')
sdk_lib_dir = join(components_dir, 'libraries')
nrfx_dir = join(sdk_dir, 'modules', 'nrfx')

sdk_files = env.GetProjectConfig().parse_multi_values(env.GetProjectOption('custom_sdk_files', ''))
sdk_includes = env.GetProjectConfig().parse_multi_values(env.GetProjectOption('custom_sdk_includes', ''))

softdevice = env.GetProjectOption('custom_sdk_softdevice', '').lower()

mcu_long = board.get("build.mcu", "")  # e.g. nrf52832_xxaa
mcu_short = mcu_long.split('_', maxsplit=1)[0]  # e.g. nrf52832

env.Replace(SDK_DIR=sdk_dir)

if sdk_includes:
    env.Append(CPPPATH=[join(sdk_dir, s) for s in sdk_includes])

env.Append(
    ASFLAGS=["-x", "assembler-with-cpp"],

    CFLAGS=["-std=gnu17"],

    CCFLAGS=[
        "-Os",  # optimize for size
        "-ffunction-sections",  # place each function in its own section
        "-fdata-sections",
        "-Wall",
        "-mthumb",
        "-nostdlib",
        "--param",  "max-inline-insns-single=500"
    ],

    CXXFLAGS=[
        "-fno-rtti",
        "-fno-exceptions",
        "-std=gnu++17",
        "-fno-threadsafe-statics"
    ],

    CPPDEFINES=[
        ("F_CPU", board.get("build.f_cpu")),
        "NRF5",
        "NRF52_SERIES" if "NRF52" in mcu_long.upper() else "NRF51",
        mcu_long.upper(),
    ],

    # LIBPATH=[
    # ],

    # includes
    CPPPATH=[
        nrfx_dir,
        join(nrfx_dir, 'hal'),
        join(nrfx_dir, 'mdk'),
        join(nrfx_dir, 'drivers', 'include'),
        join(sdk_dir, 'integration', 'nrfx'),
        join(sdk_dir, 'integration', 'nrfx', 'legacy'),
        join(nrfx_dir, 'templates'),  # nrfx_log.h stub is here;
        # join(nrfx_dir, 'templates', mcu_short),  # nrfx_config.h examples are here
        # join(sdk_dir, 'config', mcu_short, 'config'),
        join(components_dir, 'boards'),
        join(sdk_lib_dir, 'bsp'),
        join(sdk_lib_dir, 'cli'),
        join(sdk_lib_dir, 'timer'),
        join(sdk_lib_dir, 'log'),
        join(sdk_lib_dir, 'button'),
        join(sdk_lib_dir, 'util'),
        join(sdk_lib_dir, 'delay'),
        join(components_dir, 'toolchain', 'cmsis', 'include'),
        join(env.subst("${PROJECT_INCLUDE_DIR}")),  # sdk_config.h should be here
    ],

    LINKFLAGS=[
        "-Os",
        "-Wl,--gc-sections",
        "-mthumb",
        "--specs=nano.specs",
        "--specs=nosys.specs",
        "-Wl,--check-sections",
        "-Wl,--unresolved-symbols=report-all",
        "-Wl,--warn-common",
        #"-Wl,--warn-section-align",
        '-L{}'.format(join(nrfx_dir, 'mdk')),  # nrf_common.ld
    ],

    LIBSOURCE_DIRS=[join(FRAMEWORK_DIR, 'libraries')],

    LIBS=["m"]
)

if softdevice:
    softdevice_dir = join(components_dir, 'softdevice', softdevice)
    env.Append(
        CPPPATH=[
            join(softdevice_dir, 'headers'),
            join(components_dir, 'softdevice', 'common'),
        ],
        CPPDEFINES=[
            softdevice.upper(),
            'SOFTDEVICE_PRESENT',
        ],
    )
    hex_dir = join(softdevice_dir, 'hex')
    hex_files = [f for f in listdir(hex_dir) if '.hex' in f]
    assert len(hex_files) > 0
    env.Replace(SOFTDEVICEHEX=join(hex_dir, hex_files[0]))
else:
    env.Append(
        CPPPATH=[
            join(components_dir, 'drivers_nrf', 'nrf_soc_nosd'),
        ],
    )


if "BOARD" in env:
    env.Append(
        CCFLAGS=[
            "-mcpu=%s" % env.BoardConfig().get("build.cpu")
        ],
        LINKFLAGS=[
            "-mcpu=%s" % env.BoardConfig().get("build.cpu")
        ]
    )

# only nRF5283x and nRF52840 have FPUs
if any(mcu in board.get("build.mcu") for mcu in {'5283', '52840'}):
    env.Append(
        ASFLAGS=[
            "-mfloat-abi=hard",
            "-mfpu=fpv4-sp-d16",
        ],
        CCFLAGS=[
            "-mfloat-abi=hard",
            "-mfpu=fpv4-sp-d16"
        ],
        LINKFLAGS=[
            "-mfloat-abi=hard",
            "-mfpu=fpv4-sp-d16",
        ]
    )

env.Append(
    ASFLAGS=env.get("CCFLAGS", [])[:]
)

def get_linker_sizes(ld_file: str):
    """Very hacky way to read flash/ram size from ld file. """
    try:
        with open(ld_file, 'r') as f:
            all = f.read()
            flash = re.findall('FLASH.*ORIGIN\s*=\s*(\w*),\s*LENGTH\s*=\s*(\w*)', all)[0]
            ram = re.findall('RAM.*ORIGIN\s*=\s*(\w*),\s*LENGTH\s*=\s*(\w*)', all)[0]
            return int(flash[1], 0), int(ram[1], 0)
    except IndexError:
        return None
    return None


ldscript = board.get('build.ldscript', '')
if ldscript:
    pass
else:
    # sdk_ldscript = join(components_dir, 'softdevice', softdevice, 'toolchain', 'armgcc')
    sdk_ldscript = join(sdk_dir, 'config', mcu_short, 'armgcc')
    scripts = listdir(sdk_ldscript)
    if scripts:
        ldscript = join(sdk_ldscript, scripts[0])
        env.Replace(LDSCRIPT_PATH=ldscript)

sizes = get_linker_sizes(ldscript)
board.update("upload.maximum_size", str(sizes[0]))
board.update("upload.maximum_ram_size", str(sizes[1]))


bootloader_opts = board.get("bootloaders", "")
bootloader_sel = env.GetProjectOption("board_bootloader", "")
ldscript = board.get("build.arduino.ldscript", "")

if bootloader_opts:
    if not bootloader_sel:
        sys.stderr.write("Error. Board type requires board_bootloader to be specified\n")
        env.Exit(1)

    if bootloader_sel not in bootloader_opts and bootloader_sel != "none":
        sys.stderr.write(
            "Error. Invalid board_bootloader selection. Options are: %s or none\n" %
            " ".join(k for k in bootloader_opts.keys()))
        env.Exit(1)

    if bootloader_sel == "adafruit":
        env.Replace(BOOTLOADERHEX=join(FRAMEWORK_DIR, "variants", board.get("build.variant", ""), "ada_bootloader.hex"))
        # Update the linker file for bootloader use and set a flag for the build.
        env.Append(CPPDEFINES=["USE_ADA_BL"])
        env.Replace(LDSCRIPT_PATH=ldscript[:-3] + "_adabl" + ldscript[-3:])
        board.update("upload.maximum_size", board.get("upload.maximum_size") - 53248)
        board.update("upload.maximum_ram_size", board.get("upload.maximum_ram_size") - 8)


if sdk_files:
    env.BuildSources(
        join("$BUILD_DIR", "sdk_files"),
        sdk_dir,
        ['+<{}>'.format(s) for s in sdk_files]
    )

# env.Prepend(LIBS=libs)
