# Third-party components

geometry3Sharp 1.0.324, by gradientspace / Ryan Schmidt and contributors.

- Package: https://www.nuget.org/packages/geometry3Sharp/1.0.324
- Source: https://github.com/gradientspace/geometry3Sharp
- License: Boost Software License 1.0; see geometry3Sharp-LICENSE.txt.
- Used for DMesh3, DMeshAABBTree3 and triangle/ray intersections in the shadow backend.
- Version is pinned to the released netstandard2.0 package. The newer upstream dotnet8 branch is not used.

The plugin build copies geometry3Sharp.dll beside the RHP; no native runtime or separate service is needed.
