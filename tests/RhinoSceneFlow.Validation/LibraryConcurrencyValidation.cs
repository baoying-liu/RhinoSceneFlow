using System.Diagnostics;
using System.Text.Json;
using RhinoSceneFlow.Core;

internal static class LibraryConcurrencyValidation
{
    private static Process Spawn(string root,string mode,string token)
    {
        var info=new ProcessStartInfo(Environment.ProcessPath!){UseShellExecute=false,CreateNoWindow=true,RedirectStandardOutput=true,RedirectStandardError=true};
        if(Path.GetFileNameWithoutExtension(Environment.ProcessPath!).Equals("dotnet",StringComparison.OrdinalIgnoreCase))info.ArgumentList.Add(typeof(LibraryConcurrencyValidation).Assembly.Location);
        foreach(var arg in new[]{"--library-worker",root,mode,token})info.ArgumentList.Add(arg);
        return Process.Start(info)!;
    }
    private static void Finish(Process child)
    {
        if(!child.WaitForExit(45000)){child.Kill(true);throw new Exception("Owned library test worker timed out.");}
        if(child.ExitCode!=0)throw new Exception(child.StandardError.ReadToEnd()+child.StandardOutput.ReadToEnd());
        child.Dispose();
    }
    private static void Reject(Action action)
    {try{action();}catch(InvalidOperationException){return;}throw new Exception("Stale metadata was accepted.");}
    internal static void Run(string output)
    {
        string root=Path.GetFullPath(Path.Combine(output,"library-concurrency-"+Guid.NewGuid().ToString("N")));Directory.CreateDirectory(root);
        File.WriteAllBytes(Path.Combine(root,"base.png"),[1,2,3]);var lib=new MaterialLibrary(root);
        var seed=lib.Import(new(){Name="Shared",Category="Shared",Tags=["shared"]},new Dictionary<string,string>{{"baseColor",Path.Combine(root,"base.png")}});
        File.WriteAllText(Path.Combine(root,"seed.id"),seed.Id.ToString());
        var children=Enumerable.Range(0,4).Select(i=>Spawn(root,"mutate",i.ToString())).Append(Spawn(root,"read","reader")).ToArray();
        File.WriteAllText(Path.Combine(root,"start"),"go");try{foreach(var child in children)Finish(child);}finally{foreach(var child in children){try{if(!child.HasExited)child.Kill(true);}catch(InvalidOperationException){}}}
        var assets=lib.List();var current=lib.Get(seed.Id);
        if(assets.Length!=33||assets.Select(a=>a.Id).Distinct().Count()!=33||current.Revision!=81||current.CatalogRevision!=161||Math.Abs(current.WidthMeters-1.08)>1e-9)throw new Exception("Concurrent import/update lost a change.");
        foreach(var a in assets)lib.Verify(a);
        Reject(()=>lib.Update(seed));Reject(()=>lib.UpdateLabels(seed.Id,"stale","Shared",["shared"],seed.CatalogRevision));
        var organizer=Spawn(root,"organize","writer");var readers=Enumerable.Range(0,2).Select(i=>Spawn(root,"catalog-read",i.ToString())).ToArray();Finish(organizer);foreach(var reader in readers)Finish(reader);
        var snapshot=lib.List();lib.Import(new(){Name="Extra",Category="Shared",Tags=["shared"]},new Dictionary<string,string>{{"baseColor",Path.Combine(root,"base.png")}});
        Reject(()=>MaterialCatalog.Apply(lib,snapshot,snapshot.Select(a=>new CatalogLabel(a.Id,a.Name,"Stale",["shared"])).ToArray()));
        var before=lib.List().ToDictionary(a=>a.Id,a=>JsonSerializer.Serialize(a,MaterialLibrary.Json));
        using(var crash=Spawn(root,"crash","owned-test-worker"))
        {
            try
            {
                var watch=Stopwatch.StartNew();while(!File.Exists(Path.Combine(root,"crash-ready"))){if(crash.HasExited||watch.Elapsed.TotalSeconds>15)throw new Exception("Crash fixture failed to start.");Thread.Sleep(20);}
                try{lib.List();throw new Exception("Read escaped the process lock.");}catch(IOException){}
            }
            finally{if(!crash.HasExited)crash.Kill(true);crash.WaitForExit();}
        }
        var recovered=lib.List();if(recovered.Length!=before.Count||recovered.Any(a=>JsonSerializer.Serialize(a,MaterialLibrary.Json)!=before[a.Id])||File.Exists(Path.Combine(root,".sceneflow-catalog-rollback.json")))throw new Exception("Interrupted catalog transaction did not recover.");
        File.WriteAllText(Path.Combine(root,"verified.json"),JsonSerializer.Serialize(new{processWriters=4,parallelImports=32,appearanceUpdates=80,labelUpdates=80,consistentCatalogReaders=2,staleRejected=true,interruptedWriterRecovered=true},MaterialLibrary.Json));
        Console.WriteLine("PASS: shared library across real processes, lossless imports/updates, stale rejection, atomic catalog reads, bounded lock wait and killed-writer recovery.");
    }
    internal static void Worker(string[] args)
    {
        string root=args[1],mode=args[2],token=args[3];var lib=new MaterialLibrary(root);
        while(!File.Exists(Path.Combine(root,"start")))Thread.Sleep(10);
        Guid id=Guid.Parse(File.ReadAllText(Path.Combine(root,"seed.id")));
        if(mode=="mutate")
        {
            for(int i=0;i<8;i++)lib.Import(new(){Name=token+"-"+i,Category="Shared",Tags=["shared"]},new Dictionary<string,string>{{"baseColor",Path.Combine(root,"base.png")}});
            for(int i=0;i<20;i++)
            {
                for(int retry=0;;retry++){var a=lib.Get(id);a.WidthMeters+=.001;try{lib.Update(a);break;}catch(InvalidOperationException) when(retry<300){}}
                lib.UpdateLabels(id,"Shared-"+token+"-"+i,"Shared",["shared"]);
            }
        }
        else if(mode=="read")for(int i=0;i<120;i++){var assets=lib.List();foreach(var a in assets)lib.Verify(a);Thread.Sleep(2);}
        else if(mode=="organize")for(int i=0;i<12;i++){var snapshot=lib.List();MaterialCatalog.Apply(lib,snapshot,snapshot.Select(a=>new CatalogLabel(a.Id,a.Name,"Epoch-"+i,["shared"])).ToArray());Thread.Sleep(5);}
        else if(mode=="catalog-read")for(int i=0;i<120;i++){if(lib.List().Select(a=>a.Category).Distinct().Count()!=1)throw new Exception("Reader observed partial catalog commit.");Thread.Sleep(2);}
        else if(mode=="crash")
        {
            var backup=lib.List().Take(2).ToDictionary(a=>a.Id,a=>File.ReadAllText(Path.Combine(lib.AssetDirectory(a.Id),"asset.json")));
            using var lease=new FileStream(Path.Combine(root,".sceneflow-library.lock"),FileMode.Open,FileAccess.ReadWrite,FileShare.None);
            File.WriteAllText(Path.Combine(root,".sceneflow-catalog-rollback.json"),JsonSerializer.Serialize(backup,MaterialLibrary.Json));
            var first=JsonSerializer.Deserialize<MaterialAsset>(backup.First().Value,MaterialLibrary.Json)!;first.Category="Interrupted";
            File.WriteAllText(Path.Combine(lib.AssetDirectory(first.Id),"asset.json"),JsonSerializer.Serialize(first,MaterialLibrary.Json));
            File.WriteAllText(Path.Combine(root,"crash-ready"),"partial write");Thread.Sleep(Timeout.Infinite);
        }
        else throw new ArgumentException("Unknown library worker mode.");
    }
}
