using System.Collections.Concurrent;
using System.Diagnostics;

namespace RhinoSceneFlow.Core;

/// <summary>Reentrant within a thread; the OS releases the cross-process lease on exit.</summary>
internal static class LibraryFileLock
{
    private static readonly ConcurrentDictionary<string,object> gates=new(OperatingSystem.IsWindows()?StringComparer.OrdinalIgnoreCase:StringComparer.Ordinal);
    [ThreadStatic] private static Dictionary<string,int>? depths;
    internal static IDisposable Enter(string root)
    {
        string path=Path.Combine(root,".sceneflow-library.lock");var gate=gates.GetOrAdd(path,_=>new());
        if(!Monitor.TryEnter(gate,TimeSpan.FromSeconds(3)))throw new IOException("材质库正在更新，请稍后重试。");
        depths??=new(gates.Comparer);
        if(depths.TryGetValue(path,out int depth)){depths[path]=depth+1;return new Lease(path,gate,null);}
        try
        {
            Directory.CreateDirectory(root);var clock=Stopwatch.StartNew();
            while(true)
            {
                try{var file=new FileStream(path,FileMode.OpenOrCreate,FileAccess.ReadWrite,FileShare.None);depths[path]=1;return new Lease(path,gate,file);}
                catch(IOException e){if(clock.Elapsed>=TimeSpan.FromSeconds(3))throw new IOException("无法取得材质库锁，请稍后重试。",e);Thread.Sleep(20);}
            }
        }
        catch{Monitor.Exit(gate);throw;}
    }
    private sealed class Lease(string path,object gate,FileStream? file):IDisposable
    {
        private bool disposed;
        public void Dispose(){if(disposed)return;disposed=true;int depth=--depths![path];if(depth==0)depths.Remove(path);file?.Dispose();Monitor.Exit(gate);}
    }
}
