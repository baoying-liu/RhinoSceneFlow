import {RevisionSingleMaterialBefore,RevisionSingleMaterialAfter,RevisionSinglePlantBefore,RevisionSinglePlantAfter} from './PromoRevisionKeyframes';
import {RevisionMaterial,RevisionPlant,RevisionCamera,RevisionLayers,RevisionPrepare,RevisionCompare,RevisionCanvas,RevisionHd} from './PromoRevisionKeyframes';
import { Composition, Still } from "remotion";
import { Intro } from "./Intro";
import {PromoFilm} from './PromoFilm';
import { PromoLayers, PromoOpening, PromoPossibilities } from "./PromoKeyframes";
import { PromoSample } from "./PromoSample";
import { WorkflowMaterial, WorkflowPlantRules, WorkflowCamera, WorkflowSeasons, WorkflowPsdDock, WorkflowAiWorlds, WorkflowLocalEdit } from "./PromoWorkflowKeyframes";

export const RemotionRoot: React.FC = () => {
  return (
    <>
<Still id="Revision-Single-MaterialBefore" component={RevisionSingleMaterialBefore} width={1920} height={1080}/>
<Still id="Revision-Single-MaterialAfter" component={RevisionSingleMaterialAfter} width={1920} height={1080}/>
<Still id="Revision-Single-PlantBefore" component={RevisionSinglePlantBefore} width={1920} height={1080}/>
<Still id="Revision-Single-PlantAfter" component={RevisionSinglePlantAfter} width={1920} height={1080}/>
      <Still id="Revision-01-Material" component={RevisionMaterial} width={1920} height={1080}/>
      <Still id="Revision-02-Plant" component={RevisionPlant} width={1920} height={1080}/>
      <Still id="Revision-03-Camera" component={RevisionCamera} width={1920} height={1080}/>
      <Still id="Revision-04-Layers" component={RevisionLayers} width={1920} height={1080}/>
      <Still id="Revision-05-Prepare" component={RevisionPrepare} width={1920} height={1080}/>
      <Still id="Revision-06-Compare" component={RevisionCompare} width={1920} height={1080}/>
      <Still id="Revision-07-Canvas" component={RevisionCanvas} width={1920} height={1080}/>
      <Still id="Revision-08-Hd" component={RevisionHd} width={1920} height={1080}/>
      <Composition id="SceneFlow-Promo-Film-v02" component={PromoFilm} durationInFrames={3600} fps={30} width={1920} height={1080}/>
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
