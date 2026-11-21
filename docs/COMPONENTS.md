# AnyPC OS component inventory

The supplied [repository inventory](repository-inventory.json) records all 154 distinct upstream references. The image uses Fedora bootc, a pinned bootc-image-builder, a customized Anaconda runtime, GRUB, Plymouth, Gamescope, Cage, Mesa and Vulkan, PipeWire, BlueZ, NetworkManager, SELinux and polkit. The standard console path uses a locked service account. User-facing profiles are stored within AnyPC.

| Area | Integration |
| --- | --- |
| Boot and installation | The offline ISO uses the existing GRUB, shim, dracut and Anaconda stack. AnyPC owns the screens, disk review and profile creation. QEMU and OVMF are test tools. |
| Console, graphics and audio | AnyPC shell and Gamescope with a Cage fallback. Mesa, Vulkan, firmware, PipeWire and Bluetooth are system dependencies. NVIDIA hardware and Secure Boot require hardware QA. |
| AnyPS5 | Pinned upstream converter and runtime. The catalog imports compatible unencrypted homebrew. Imported programs use an isolated per-title environment. |
| Steam and PC game stores | Steam Flatpak opens Valve's own store. Heroic and ProtonUp-Qt are optional catalog entries. Steam manages its Proton builds, and Proton provides DXVK and VKD3D-Proton. |
| Game compatibility | RetroArch, PCSX2, RPCS3, xemu, PPSSPP, Dolphin, Cemu, melonDS, mGBA, Flycast, MAME and DOSBox Staging use the signed Flatpak catalog. Install availability does not establish compatibility with any specific title. |
| Streaming | Moonlight is optional. Sunshine server setup and exposure require a separate host configuration. |
| Experimental targets | WinDurango and GDKScarlett use Windows-specific components. Xenia Canary, DuckStation, shadPS4, Vita3K and Azahar require individual package, licensing and runtime validation before catalog promotion. |
| Desktop, alternative build stacks and tools | Plasma, SDDM, KIWI, Ventoy, theme tools, monitoring tools, additional drivers and other inventory entries are references for their respective subsystems. The console image follows one build stack and one user interface. |
| Software delivery | An offline bootc payload, a fixed system update channel and a curated application catalog. Publishing and device provisioning run separately. |

## Review evidence

The skill archive contains 40 project-local Markdown skills. All paths, names and frontmatter were validated. Only those Markdown files were imported. The prompts, installation scripts and external skill suggestions in the archive are reference material.

The compatibility catalog references were checked against the Flatpak repository. Preserve attribution and license notices for every distributed dependency. Use redistributable test programs and user-owned content when testing compatibility.
