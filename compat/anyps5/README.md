# AnyPS5 compatibility

[AnyPS5](https://github.com/boykopovar/AnyPS5) is an independent project. Its
relinker can produce native Linux executables and desktop shortcuts. AnyPC OS
can register and launch these outputs from the library.

1. Use the [official release and documentation](https://github.com/boykopovar/AnyPS5/releases/tag/v0.1.5)
   with applications you have permission to use.
2. Place the exported Linux folder under `~/Games/AnyPS5/<name>/` for the
   account running the AnyPC session. On an installed AnyPC system, that is
   `/var/home/player/Games/AnyPS5/<name>/`. Keep the executable, its matching
   shortcut (for example `app.elf` and `app.elf.desktop`), and its adjacent
   libraries and application data together.
3. Open **Settings → Compatibility** and enable the AnyPS5 module. The title
   appears in the library. AnyPC runs the detected Linux executable in its
   own directory when you select Play.

The registered programs run with the console account's permissions. Check each
title's CPU, Vulkan and compatibility requirements upstream. The AnyPS5 code
and license stay with the upstream release. AnyPC OS ships no console firmware,
keys or game files and is an independent project.
