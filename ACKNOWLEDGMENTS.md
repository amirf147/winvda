# Acknowledgments & Prior Art

`winvda` is an independent, clean-room implementation of the Windows Virtual Desktop interface, designed from first principles using a zero-cached-state, transient MTA invocation model.

While the codebase contains no copied source code from prior libraries, we gratefully acknowledge the foundational research, reverse engineering, and open-source tooling contributed by the following individuals and projects:

* **Michael Roberts (`mrob95`)**: Author of [`pyvda`](https://github.com/mrob95/pyvda) and [`talon-pyvda`](https://github.com/mirober/talon-pyvda). Michael pioneered programmatic Python access to Windows virtual desktops for speech accessibility (Talon Voice and Caster). His work proved the viability of Python-driven desktop control and inspired this architectural redesign.
* **Jari Pennanen (`Ciantic`)**: Author of [`VirtualDesktopAccessor`](https://github.com/Ciantic/VirtualDesktopAccessor). In 2015, Jari performed the initial reverse engineering of Windows 10's undocumented `IVirtualDesktopManagerInternal` COM interface, uncovering the private service GUIDs that made third-party virtual desktop management possible.

