# AnyPS5 compatibility

The installer bundles the independent [AnyPS5 v0.1.5](https://github.com/boykopovar/AnyPS5/tree/v0.1.5) Linux relinker and its upstream Linux runtime libraries. Their SHA-256 digests are pinned in `build/install-compat.sh`. Attribution and the upstream license ship in `/usr/share/licenses/anyps5`. The converter and the AnyPC UI run as separate processes.

Open **AnyPC Store**. For your own unencrypted homebrew, place `eboot.elf` or an ELF-format `eboot.bin` and its resources under `AnyPS5/Title/` on a USB drive. Select **Scan USB drives**, then **Import** next to the title. The internal import location is `~/Games/Import/Title/` for the console player.

The converter runs offline as the player in a temporary sandbox. It can read the source folder and the installed runtime. AnyPC publishes the completed output under `~/Games/AnyPS5/` and refreshes the library. A previously converted Linux export can also be placed there with its matching executable and desktop entry. When playing, the title gets a read-only game folder, a private writable home and access to the console display, audio, and game controllers.

Compatibility varies with each application, CPU, graphics driver and Vulkan implementation. Firmware, game files and cryptographic keys are supplied by neither the installer nor the store. See the [upstream usage guide](https://github.com/boykopovar/AnyPS5/blob/v0.1.5/docs/user/USAGE.md) for supported input layouts.
