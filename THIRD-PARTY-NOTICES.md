# Third-party components

SceneFlow is an independent project. It is not made, endorsed or supported by
McNeel, OpenAI, Microsoft or the PhotoCraft authors. Product names belong to their
respective owners. Third-party components retain their own licenses and notices;
public availability of this repository does not change those terms.

| Component | Source and notices |
|---|---|
| Original Rhino MCP Platform 0.3.0 | [McNeel RhinoAI](https://github.com/mcneel/RhinoAI/tree/plugin-v0.3.0), MIT; installer includes `RhinoAI-LICENSE.txt` |
| geometry3Sharp | `third-party/geometry3Sharp-LICENSE.txt` (Boost Software License) |
| xatlas | `third-party/xatlas/LICENSE` (MIT); worker source in this repository |
| FastNoiseLite | `third-party/FastNoiseLite/LICENSE` (MIT) |
| Lucide / Feather-derived icons | `src/RhinoSceneFlow.Plugin/Resources/InterfaceIcons/LICENSE.txt` |
| React, Konva and browser dependencies | `src/RhinoSceneFlow.Plugin/PostProduction/board-LICENSES.txt`; pinned `web/postproduction/package-lock.json` |
| PhotoCraft v0.21.0 | `src/RhinoSceneFlow.Plugin/PostProduction/vendor/photocraft/`: original `LICENSE-MIT`, `LICENSE-APACHE`, `NOTICE`, `ATTRIBUTION.md`, individual `licenses/`, and `SCENEFLOW-SOURCE.json` provenance |
| WebView2 | Microsoft's original redistributable and `WebView2-LICENSE.txt` / `WebView2-NOTICE.txt` in the installed application |
| CPython 3.14.10 | `Runtime/Scripts/LICENSE.txt`; Python Software Foundation license and included third-party notices |
| Python packages | Installed `Runtime/Scripts/Lib/site-packages/*.dist-info` license/metadata files, `Runtime/requirements-lock.txt`, `Runtime/wheel-provenance.json` |
| libvips / pyvips-binary 8.18.7 | LGPL-3.0-or-later and upstream dependency licenses; see `third-party/libvips/` for notices and source/build provenance |
| .NET runtime | Microsoft .NET MIT license and third-party notices, included under `Notices/dotnet/` |

The preview contains unmodified third-party runtime binaries, except the documented
PhotoCraft embedding integration. SceneFlow does not restrict the rights granted
by third-party licenses, including debugging modifications to LGPL libraries.
Replacement library binaries must be ABI-compatible; use a separate test copy.

No open-source license for SceneFlow's own original code has been selected for
this first public preview. No MIT/Apache license is implicitly applied to the
original project merely by publishing the repository. This does not affect the
explicit licenses on third-party files above.
