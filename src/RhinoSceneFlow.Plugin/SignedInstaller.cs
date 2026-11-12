using System.Runtime.InteropServices;
using System.Security.Cryptography.X509Certificates;

namespace RhinoSceneFlow.Plugin;

// Shared with the out-of-process updater. Validate trust AND the pinned publisher.
internal static class SignedInstaller
{
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct FileInfo { public uint Size; public string Path; public IntPtr File; public IntPtr Subject; }
    [StructLayout(LayoutKind.Sequential)]
    private struct TrustData
    {
        public uint Size; public IntPtr Policy, Sip; public uint Ui, Revocation, UnionChoice; public IntPtr File;
        public uint StateAction; public IntPtr StateData, Url; public uint Flags, Context;
    }
    [DllImport("wintrust.dll", ExactSpelling = true)] private static extern int WinVerifyTrust(IntPtr hwnd, ref Guid action, ref TrustData data);
    internal static void Verify(string path, string thumbprint)
    {
        if (thumbprint.Length != 40 || !thumbprint.All(Uri.IsHexDigit)) throw new InvalidDataException("Publisher signing certificate is not configured.");
        var file = new FileInfo { Size = (uint)Marshal.SizeOf<FileInfo>(), Path = System.IO.Path.GetFullPath(path) };
        IntPtr memory = Marshal.AllocCoTaskMem(Marshal.SizeOf<FileInfo>());
        Marshal.StructureToPtr(file, memory, false);
        var data = new TrustData { Size = (uint)Marshal.SizeOf<TrustData>(), Ui = 2, UnionChoice = 1, File = memory, StateAction = 1, Revocation = 1, Flags = 0x80 };
        var action = new Guid("00AAC56B-CD44-11d0-8CC2-00C04FC295EE");
        try
        {
            if (WinVerifyTrust(new IntPtr(-1), ref action, ref data) != 0) throw new InvalidDataException("Installer signature is not trusted.");
#pragma warning disable SYSLIB0057
            using var certificate = new X509Certificate2(X509Certificate.CreateFromSignedFile(path));
#pragma warning restore SYSLIB0057
            if (!certificate.Thumbprint.Equals(thumbprint, StringComparison.OrdinalIgnoreCase)) throw new InvalidDataException("Installer publisher does not match SceneFlow.");
        }
        finally { data.StateAction = 2; WinVerifyTrust(new IntPtr(-1), ref action, ref data); Marshal.DestroyStructure<FileInfo>(memory); Marshal.FreeCoTaskMem(memory); }
    }
}
