# libvips source and build provenance

SceneFlow 0.23.1 distributes unmodified pyvips-binary 8.18.7 and pyvips 3.2.0.
The binary is loaded as a separate DLL/Python extension, not linked into the Rhino
plugin. LGPL-covered rights, including modification and debugging replacement
libraries, are not restricted by SceneFlow's own licensing status.

The first public preview Release provides **SceneFlow-ThirdParty-Sources-0.23.1.zip**
next to the installer. It contains source archives for the upstream libvips 8.18.7
dependency versions, upstream build recipes and patches, source URLs and SHA-256
hashes. It is source material, not another installer. Upstream license texts and
copyright notices are retained within those archives. The release also provides
SHA256SUMS.txt for the downloadable assets.

- [pyvips-binary 8.18.7](https://github.com/kleisauke/pyvips-binary/tree/v8.18.7)
- [pyvips 3.2.0](https://github.com/libvips/pyvips/tree/v3.2.0)
- [libvips 8.18.7](https://github.com/libvips/libvips/tree/v8.18.7)
- [binary packaging recipes 8.18.7](https://github.com/kleisauke/libvips-packaging/tree/v8.18.7)
- [Windows MXE recipes 8.18.7](https://github.com/libvips/build-win64-mxe/tree/v8.18.7)

Windows x64 binary chain: pyvips-binary -> libvips-packaging win-x64 ->
build-win64-mxe `vips-dev-x64-web-8.18.7-static.zip`. The upstream Windows recipes
use the `kleisauke/mxe` llvm-mingw-20260924 branch. The supplement records its
resolved snapshot and the source package hashes; it is not a claim that SceneFlow
rebuilt the upstream binaries or achieved bit-for-bit reproducibility.

To rebuild, follow the included upstream Docker/MXE build instructions for x64,
web, static, non-GPL variant. The LGPL libvips DLL and its dependencies are combined
by upstream; all sources and relevant recipes must be retained when rebuilding.
Install ABI-compatible replacement binaries into a separate test copy of the
runtime, then run SceneFlow's raster tests before using them on user projects.

The GNU LGPL/GPL texts included by pyvips-binary are retained in its `.dist-info`
license directory. `LICENSE.txt` here is the LGPL 2.1 text shipped by the original
Windows libvips distribution. The packaging notices document the upstream use of
the LGPL 3 or later option for relevant libraries.
