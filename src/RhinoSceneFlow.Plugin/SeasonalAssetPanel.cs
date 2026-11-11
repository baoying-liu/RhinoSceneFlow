using Eto.Forms;
using RhinoSceneFlow.Core;
namespace RhinoSceneFlow.Plugin;

internal sealed class SeasonalAssetPanel:Panel
{
    private string descriptionLanguage="";
    private readonly bool plant;private Guid? id,job;private bool binding;private MaterialAsset? asset;
    private readonly UiCheckBox follow=new(){Text="跟随季节变化",Checked=true};private readonly DropDown season=new(){Width=100};private readonly UiLabel status=ToolUi.Note("选择素材后可补齐季节版本。");private readonly UITimer timer=new(){Interval=.5};
    private MaterialLibrary Library=>plant?PlantService.Library:MaterialService.Library;
    internal SeasonalAssetPanel(bool plant)
    {
        this.plant=plant;foreach(string s in Seasons.All)season.Items.Add(new UiListItem{Key=s,Text=Seasons.Name(s)+"季"});season.SelectedKey="summer";
        var l=Ui.Layout();l.AddRow(follow);l.AddRow(season);if(plant)l.AddRow(Ui.Button("补齐夏季立面／平面",()=>Start(false)));l.AddRow(Ui.Button("生成／补齐四季",()=>Start(true)));l.AddRow(Ui.Button("取消季节任务",()=>{if(job.HasValue)SeasonalGeneration.Cancel(job.Value);}));l.AddRow(status);Content=new UiExpander{Header="季节版本",Content=l};
        follow.CheckedChanged+=(_,_)=>Save();season.SelectedValueChanged+=(_,_)=>Save();timer.Elapsed+=(_,_)=>{if(job.HasValue){var j=SeasonalGeneration.Status(job.Value);status.Text=WorkspaceAppearance.Text(j.Stage)+" · "+WorkspaceAppearance.Text("已就绪")+" "+j.Completed;if(j.Status!="running"){job=null;if(id.HasValue)Bind(id.Value);if(j.Status!="completed")status.Text=j.Stage;}}};timer.Start();Enabled=false;
    }
    internal void Bind(Guid value)
    {
        id=value;asset=Library.Get(value);binding=true;try{follow.Checked=asset.Seasonal.FollowSeason;season.SelectedKey=asset.Seasonal.FixedSeason;season.Enabled=!asset.Seasonal.FollowSeason;Enabled=true;
        if(!job.HasValue)Describe();}finally{binding=false;}
    }
    internal void RefreshLanguage(string language){if(asset!=null&&!job.HasValue&&descriptionLanguage!=language)Describe();}
    private void Describe()
    {
        if(asset==null)return;descriptionLanguage=PluginPreferences.Load().ResolvedLanguage;
        status.Text=(plant?WorkspaceAppearance.Text($"参考高度 {asset.HeightMeters:G4} m · "):"")+
            string.Join(" / ",Seasons.All.Select(s=>WorkspaceAppearance.Text(Seasons.Name(s))+":"+
                WorkspaceAppearance.Text(Seasons.Has(asset,s)?plant?Seasons.Has(asset,s,true)?"立面＋平面":"仅立面":"已有":"夏季回退")));
    }
    private void Save(){if(binding||asset==null)return;try{asset.Seasonal.FollowSeason=follow.Checked==true;asset.Seasonal.FixedSeason=season.SelectedKey??"summer";asset=Library.Update(asset);season.Enabled=!asset.Seasonal.FollowSeason;PlantService.RefreshSeasons();}catch(Exception e){status.Text=e.Message;}}
    private void Start(bool four){if(id==null)return;try{job=SeasonalGeneration.Start(id.Value,plant,four).Id;status.Text="季节任务已启动；已有版本会复用。";}catch(Exception e){status.Text=e.Message;}}
    protected override void Dispose(bool disposing){if(disposing){timer.Stop();timer.Dispose();}base.Dispose(disposing);}
}
