# Leonida native diagnostics

AnyPC OS includes the native CPU diagnostics from the independent
[ItsNotRexed/Leonida](https://github.com/ItsNotRexed/Leonida) project. This is an
experimental diagnostic module, not a game loader or a compatibility guarantee.
It does not make console games playable, install Wine/Proton, or demonstrate
improved graphics performance.

## Included checks

The pinned revision and archive checksum are in manifest.json. The image build
verifies that checksum, compiles the eleven selected targets with assertions
enabled, and runs CTest. Only their binaries are copied into the final image;
compilers and development headers remain in the separate build stage.

The checks cover pipeline cache files, XDXR descriptions, command lists, resource
tiling, descriptor tables, typeless render targets, cache snapshots, clear
colors, resource state mapping, GFX10 descriptors and descriptor decoding.
The descriptor benchmark is invoked only with --self-test. No GPU benchmarks or
tests that can silently skip are used to report success.

The Windows loader and the separately licensed rpf9 component are not bundled.
No game data, console firmware, keys or game executables are supplied.

## Using the module

Open Settings → Compatibility → Leonida and choose Run checks. The local service
runs the fixed tools without privileges in a private temporary directory.
Only one check job can run at a time. Each tool has a five-second limit and the
whole job has a thirty-second execution budget. The page polls while the job
runs and reports pass/fail counts, completion time and localized errors.
Results are held in memory for the current service session.

Wine and Proton labels report discovered executables, not game validation.
Proton detection includes standard Steam, Flatpak Steam and custom compatibility
tool directories. External Steam library folders are not searched yet.

Both demo backends simulate eleven successful checks and label the result as
simulated. They do not run tools or inspect the machine.

## API

GET /api/modules preserves anyps5 and adds leonida with installed, version,
experimental status, runtime presence and a checks object. The checks object
contains state, passed, failed, total, error, checked, results and simulated.

POST /api/modules/leonida/check accepts an empty JSON object only and returns
202 with the modules object. The existing local Host and X-AnyPC protections
apply. Concurrent jobs return 409; a missing or incomplete module returns 422.
Clients cannot select executable paths, arguments or a working directory.

## License and source

The selected code is GPL-3.0-or-later. The image retains the upstream license
and revision under /usr/share/licenses/leonida and the native corresponding
source under /usr/share/anypc/sources. The main project's build instructions
and pinned acquisition script are build/install-leonida.sh and build/Containerfile.
The tools can be rebuilt with CMake, a C++20 compiler, Ninja and Vulkan headers.
