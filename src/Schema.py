from Constants import Constants
class Schema:
    HierarchichalSbzResourceNameBuilderMap = { Constants.MicrosoftServiceFabricMesh + "/" + Constants.SecretValues:
                                               Constants.MicrosoftServiceFabricMesh + "/" + Constants.Secrets + "/{0}/" + Constants.Values + "/{1}"}

    SchemaVersionSupportedResourcesTypeMap = {
        Constants.SchemaVersion_2018_07_01_preview:
        { 
            Constants.Networks: Constants.MicrosoftServiceFabricMesh + "/" + Constants.Networks,
            Constants.Applications: Constants.MicrosoftServiceFabricMesh + "/" + Constants.Applications,
            Constants.Volumes: Constants.MicrosoftServiceFabricMesh + "/" + Constants.Volumes 
        },
        Constants.SchemaVersion_1_0_0:
        {
            Constants.Networks: Constants.MicrosoftServiceFabricMesh + "/" + Constants.Networks,
            Constants.Applications: Constants.MicrosoftServiceFabricMesh + "/" + Constants.Applications,
            Constants.Volumes: Constants.MicrosoftServiceFabricMesh + "/" + Constants.Volumes
        },
        Constants.SchemaVersion_1_0_0_preview1:
        {
            Constants.Networks, Constants.MicrosoftServiceFabricMesh + "/" + Constants.Networks,
            Constants.Applications, Constants.MicrosoftServiceFabricMesh + "/" + Constants.Applications,
            Constants.Volumes, Constants.MicrosoftServiceFabricMesh + "/" + Constants.Volumes,
            Constants.Secrets, Constants.MicrosoftServiceFabricMesh + "/" + Constants.Secrets
        },
        Constants.SchemaVersion_1_0_0_preview2:
        {
            Constants.Networks, Constants.MicrosoftServiceFabricMesh + "/" + Constants.Networks,
            Constants.Applications, Constants.MicrosoftServiceFabricMesh + "/" + Constants.Applications,
            Constants.Volumes, Constants.MicrosoftServiceFabricMesh + "/" + Constants.Volumes,
            Constants.Secrets, Constants.MicrosoftServiceFabricMesh + "/" + Constants.Secrets,
            Constants.SecretValues, Constants.MicrosoftServiceFabricMesh + "/" + Constants.SecretValues,
            Constants.Gateways, Constants.MicrosoftServiceFabricMesh + "/" + Constants.Gateways
        }
    }