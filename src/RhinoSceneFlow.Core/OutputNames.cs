namespace RhinoSceneFlow.Core;

public enum FileCollision { Overwrite, Number, Cancel }
public sealed record OutputTarget(string Path,bool Overwrite);

public static class OutputNames
{
    public static string SafeStem(string name)
    {
        var invalid=Path.GetInvalidFileNameChars().Concat("<>:\"/\\|?*").ToHashSet();
        string stem=new(name.Select(c=>invalid.Contains(c)||char.IsControl(c)?'_':c).ToArray());
        stem=stem.Trim().TrimEnd('.',' ');
        if(stem.Length==0)stem="View";
        if(stem.Length>120)stem=stem[..120].TrimEnd('.',' ');
        string device=stem.Split('.')[0].ToUpperInvariant();
        if(device is "CON" or "PRN" or "AUX" or "NUL" ||
            (device.Length==4 && (device.StartsWith("COM")||device.StartsWith("LPT")) && device[3] is >= '1' and <= '9'))stem="_"+stem;
        return stem;
    }
    public static OutputTarget Reserve(string directory,string name,ISet<string> reserved,Func<string,FileCollision> resolve)
    {
        string stem=SafeStem(name),path=Path.Combine(directory,stem+".psd");
        // Distinct views in the same batch must never overwrite one another after sanitizing.
        if(!reserved.Contains(path) && File.Exists(path))
        {
            switch(resolve(path))
            {
                case FileCollision.Cancel:throw new OperationCanceledException("Export cancelled before writing files.");
                case FileCollision.Overwrite:reserved.Add(path);return new(path,true);
            }
        }
        if(reserved.Contains(path)||File.Exists(path)||Directory.Exists(path))
        {
            int number=1;
            do {path=Path.Combine(directory,stem+(number++).ToString("D3")+".psd");}
            while(reserved.Contains(path)||File.Exists(path)||Directory.Exists(path));
        }
        reserved.Add(path);return new(path,false);
    }
}
