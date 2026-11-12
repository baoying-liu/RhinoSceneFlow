import { Composition, Still } from "remotion";
import { Intro } from "./Intro";
import { PromoLayers, PromoOpening, PromoPossibilities } from "./PromoKeyframes";
import { PromoSample } from "./PromoSample";
import { WorkflowMaterial, WorkflowPlantRules, WorkflowCamera, WorkflowSeasons, WorkflowPsdDock, WorkflowAiWorlds, WorkflowLocalEdit } from "./PromoWorkflowKeyframes";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Still id="Workflow-01-Material-Chat" component={WorkflowMaterial} width={1920} height={1080}/>
      <Still id="Workflow-02-Plant-Rules" component={WorkflowPlantRules} width={1920} height={1080}/>
      <Still id="Workflow-03-Camera" component={WorkflowCamera} width={1920} height={1080}/>
      <Still id="Workflow-04-Seasons" component={WorkflowSeasons} width={1920} height={1080}/>
      <Still id="Workflow-05-PSD-Dock" component={WorkflowPsdDock} width={1920} height={1080}/>
      <Still id="Workflow-06-AI-Worlds" component={WorkflowAiWorlds} width={1920} height={1080}/>
      <Still id="Workflow-07-Local-Edit" component={WorkflowLocalEdit} width={1920} height={1080}/>
      <Composition id="SceneFlow-Promo-Sample-v01" component={PromoSample} durationInFrames={600} fps={30} width={1920} height={1080}/>
      <Still id="Promo-01-Opening" component={PromoOpening} width={1920} height={1080}/>
      <Still id="Promo-02-PSD" component={PromoLayers} width={1920} height={1080}/>
      <Still id="Promo-03-Possibilities" component={PromoPossibilities} width={1920} height={1080}/>
      <Composition id="SceneFlow-Style-Preview" component={Intro}
        durationInFrames={2160} fps={30} width={1920} height={1080}
        defaultProps={{showDraftLabel:true}} />
    </>
  );
};
