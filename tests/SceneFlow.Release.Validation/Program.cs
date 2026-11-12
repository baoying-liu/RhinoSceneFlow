using System.Security.Cryptography.X509Certificates;
using RhinoSceneFlow.Plugin;

if (args.Length != 2) throw new ArgumentException("Pass the original Microsoft bootstrapper and our installer. No executable is run.");
#pragma warning disable SYSLIB0057
using var certificate = new X509Certificate2(X509Certificate.CreateFromSignedFile(args[0]));
#pragma warning restore SYSLIB0057
SignedInstaller.Verify(args[0], certificate.Thumbprint);
void Reject(string file, string publisher)
{
    try { SignedInstaller.Verify(file, publisher); } catch (InvalidDataException) { return; }
    throw new Exception("Accepted an untrusted installer or mismatched publisher.");
}
Reject(args[0], new string('0', 40));
Reject(args[1], certificate.Thumbprint);
Reject(args[0], "");
Console.WriteLine("PASS: real Windows Authenticode trust, pinned-publisher mismatch, unsigned/foreign executable rejection and missing-pin rejection. No installation.");
