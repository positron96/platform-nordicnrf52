Same blinky, but with linker file that respects softdevice and bootloader


build project with correct ld script (buttonless_dfu for example)

generate dfu package:
https://infocenter.nordicsemi.com/index.jsp?topic=%2Fug_nrfutil%2FUG%2Fnrfutil%2Fnrfutil_pkg.html

```
python nrfutil-cli.py pkg generate --application firmware.hex 
  --hw-version 52
  --sd-req 0x103
  --application-version 1
  --app-boot-validation VALIDATE_GENERATED_CRC
  firmware.zip
```

nrfutil-cli is in `<platformio nrfsdk folder>/tools/nrfutil` dir
 
52 is for nrf52 family
0x103 is id of softdevice S112 7.2.0. retrieve with `nrfutil pkg generate --help`
also: --key-file key.pem