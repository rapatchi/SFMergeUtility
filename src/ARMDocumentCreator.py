import json
from PropertyNames import PropertyNames
from Constants import Constants
from Schema import Schema
from ArmParameter import ArmParameter, MetaData
from collections import OrderedDict 

class ArmDocumentGenerator:

    @staticmethod
    def generate(sf_json_resources, region, output_file_name):
        with open(output_file_name, 'w') as fp:
            arm_dict = OrderedDict()
            parameter_info = OrderedDict()
            property_value_map = OrderedDict()
            arm_dict = ArmDocumentGenerator.begin_write_arm_document(arm_dict)
            parameter_info[PropertyNames.Location] = ArmDocumentGenerator.get_location_parameter(region)
            property_value_map[PropertyNames.Location] = "[" + PropertyNames.Parameters + "('" + PropertyNames.Location +"')]"
            # print "arm_dict:" + json.dumps(arm_dict)
            # print "property_value_map" + json.dumps(property_value_map)
            arm_dict = ArmDocumentGenerator.write_parameters(arm_dict, parameter_info)
            # print "write parameters arm_dict: \n" + json.dumps(arm_dict)
            arm_dict = ArmDocumentGenerator.write_arm_resources(arm_dict, sf_json_resources, property_value_map)
            arm_doc_string = ArmDocumentGenerator.end_write_arm_document(arm_dict)
            fp.write(arm_doc_string)

    @staticmethod
    def begin_write_arm_document(writer):
        writer[PropertyNames.Schema] = Constants.ArmSchemaVersion
        writer[PropertyNames.ContentVersion] = Constants.ContentVersion
        return writer

    @staticmethod
    def end_write_arm_document(writer):
        return json.dumps(writer, indent=4)

    @staticmethod
    def write_parameters(writer, parameters_info):
        if not PropertyNames.Parameters in writer:
            writer[PropertyNames.Parameters] = OrderedDict()
        for parameter in parameters_info.keys():
            writer[PropertyNames.Parameters][parameter] = parameters_info[parameter].to_dict()
        return writer

    @staticmethod
    def write_arm_resources(writer, sf_json_resources, property_value_map):
        dependencies = ArmDocumentGenerator.get_dependencies(sf_json_resources)
        for sf_json_resource in sf_json_resources:
            with open(sf_json_resource, 'r') as sf_json_resource_fp:
                sf_resource = json.load(sf_json_resource_fp, object_pairs_hook=OrderedDict)
                kind, description = ArmDocumentGenerator.get_resource_kind_and_description(sf_resource)
                if kind == Constants.Application:
                    writer = ArmDocumentGenerator.process_application(writer, description, dependencies, property_value_map)
                else:
                    writer = ArmDocumentGenerator.process_sf_resource(writer, description, kind, dependencies, property_value_map)
        return writer
        
    @staticmethod
    def get_location_parameter(region):
        return ArmParameter(region, "string", "Location of Resources")
    
    @staticmethod
    def get_dependencies(sf_json_resources):
        dependencies = OrderedDict()
        resource_types = OrderedDict()
        for sf_json_resource in sf_json_resources:
            name = ""
            kind = ""
            with open(sf_json_resource, 'r') as sf_json_resource_fp:
                resource = json.load(sf_json_resource_fp, object_pairs_hook=OrderedDict)
                kind, description = ArmDocumentGenerator.get_resource_kind_and_description(resource)
                schemaversion = Constants.DefaultSchemaVersion
                for prop, value in description.items():
                    if prop == PropertyNames.SchemaVersion:
                        schemaversion = value
                    elif prop == PropertyNames.Name:
                        name = value

                # print "name:" + name + "\nkind:" + kind
                if name == "" or kind == "":
                    raise ValueError("Required properties name or kind missing")

                if kind in resource_types:
                    resource_types[kind].append(ArmDocumentGenerator.get_sbz_resource_name(ArmDocumentGenerator.get_sbz_resource_type(kind, schemaversion), name))
                else:
                    resource_types[kind] = [ArmDocumentGenerator.get_sbz_resource_name(ArmDocumentGenerator.get_sbz_resource_type(kind, schemaversion), name)]
        # print "resource_types: \n" + str(resource_types)
        applications = resource_types.get(Constants.Application, [])
        networks = resource_types.get(Constants.Network, [])
        secrets = resource_types.get(Constants.Secret, [])
        secret_values = resource_types.get(Constants.SecretValue, [])
        volumes = resource_types.get(Constants.Volume, [])

        if not applications == []:
            for application in applications:
                dependencies[application] = []
                if not networks == []:
                    dependencies[application] += networks
                if not secret_values == []:
                    dependencies[application] += secret_values
                if not volumes == []:
                    dependencies[application] += volumes
        
        if not volumes == []:
            for volume in volumes:
                dependencies[volume] = []
                if not secret_values == []:
                    dependencies[volume] += secret_values

        if not secret_values == []:
            for secret_value in secret_values:
                dependencies[secret_value] = []
                if not secrets == []:
                    dependencies[secret_value] += secrets

        # print "dependencies: \n" + str(dependencies)
        return dependencies


    @staticmethod
    def process_application(writer, application, dependencies, property_value_map):
        sf_application_writer = OrderedDict()
        if not PropertyNames.Name in  application:
            raise ValueError("name is not specified in description")
        
        name = application.get(PropertyNames.Name)

        # apiVersion
        schema_version = Constants.DefaultSchemaVersion
        if PropertyNames.SchemaVersion in application:
            schema_version = application[PropertyNames.SchemaVersion]
            # schemaVersion is not needed by RP, so remove it.
            del application[PropertyNames.SchemaVersion]

        sf_application_writer[PropertyNames.ApiVersion] = Schema.SchemaVersionRpApiVersionMap[schema_version]

        # name
        sf_application_writer[PropertyNames.Name] = name
        del application[PropertyNames.Name]

        # type: Microsoft.Seabreeze/applications
        sf_application_writer[PropertyNames.Type] = Schema.SchemaVersionSupportedResourcesTypeMap[schema_version][Constants.Applications]

        # location
        sf_application_writer[PropertyNames.Location] = property_value_map[PropertyNames.Location]

        # dependsOn
        sf_application_writer[PropertyNames.DependsOn] = dependencies.get(ArmDocumentGenerator.get_sbz_resource_name(ArmDocumentGenerator.get_sbz_resource_type(Constants.Application, schema_version), name), [])

        if PropertyNames.Kind in application:
            del application[PropertyNames.Kind]
        
        # Get all JsonProperties for application, handle the "properties" JsonProperty, write others as is.
        for app_property in application.keys():
            if app_property == PropertyNames.Properties:
                sf_application_writer[app_property] = OrderedDict()
                properties = application[app_property]
                for prop in properties.keys():
                    if prop == Constants.Services:
                        sf_services_writer = ArmDocumentGenerator.process_services(properties[prop], schema_version)
                        sf_application_writer[app_property][prop] = sf_services_writer
                    else:
                        sf_application_writer[app_property][prop] = properties[prop]
            else:
                sf_application_writer[app_property] = application[app_property]
        if PropertyNames.Resources in writer:
            writer[PropertyNames.Resources].append(sf_application_writer)
        else:
            writer[PropertyNames.Resources] = [sf_application_writer]
        return writer



    @staticmethod
    def process_services(services, schema_version):
        sf_services_writer = []
        for service in services:
            sf_services_writer.append(ArmDocumentGenerator.process_service(service, schema_version))
        return sf_services_writer

    @staticmethod
    def process_service(service, schema_version):
        service_writer=OrderedDict()
        if not PropertyNames.Name in  service:
            raise ValueError("name is not specified in description")

        name = service.get(PropertyNames.Name)

        # apiVersion
        schema_version = Constants.DefaultSchemaVersion
        if PropertyNames.SchemaVersion in service:
            schema_version = service[PropertyNames.SchemaVersion]
            # schemaVersion is not needed by RP, so remove it.
            del service[PropertyNames.SchemaVersion]

        # name
        service_writer[PropertyNames.Name] = name
        del service[PropertyNames.Name]

        # Get all JsonProperties for service, handle the "properties" JsonProperty, write others as is.
        for service_property in service.keys():
            if service_property == PropertyNames.Properties:
                properties = service[service_property]
                properties = ArmDocumentGenerator.process_resource_refs(properties, schema_version)
                service_writer[service_property] = properties

            else:
                service_writer[service_property] = service[service_property]
        return service_writer
        
    @staticmethod
    def process_resource_refs(properties, schema_version):
        # fix refs for ARM
        # print "process_resource_refs:" + str(properties)
        for resource_kind in Schema.SchemaVersionSupportedResourcesKindMap[schema_version]:
            resource_refs = properties.get(resource_kind +"Refs", [])
            if not resource_refs == []:
                for index in range(0, len(resource_refs)):
                    resource_ref = resource_refs[index]
                    ref_value = resource_ref[PropertyNames.Name]
                    properties[resource_kind +"Refs"][index][PropertyNames.Name] = "[resourceId('{0}','{1}')]".format(ArmDocumentGenerator.get_sbz_resource_type(resource_kind, schema_version), ref_value)
        
        # Recursively calling ref resolve for subnodes, as resource refs can be present in the subnodes as well
        for prop in properties:
            if isinstance(prop, list):
                properties[prop] = ArmDocumentGenerator.process_resource_refs(prop, schema_version)
        return properties

    @staticmethod
    def process_sf_resource(writer, sf_resource, resource_kind, dependencies, property_value_map):
        sf_resource_writer = OrderedDict()
        if not PropertyNames.Name in  sf_resource:
            raise ValueError("name is not specified for %s resource" % resource_kind)
        
        name = sf_resource.get(PropertyNames.Name)
        # apiVersion
        schema_version = Constants.DefaultSchemaVersion
        if PropertyNames.SchemaVersion in sf_resource:
            schema_version = sf_resource[PropertyNames.SchemaVersion]
            # schemaVersion is not needed by RP, so remove it.
            del sf_resource[PropertyNames.SchemaVersion]

        sf_resource_writer[PropertyNames.ApiVersion] = Schema.SchemaVersionRpApiVersionMap[schema_version]
        # print "apiVersion:" + Schema.SchemaVersionRpApiVersionMap[schema_version]

        # name
        sf_resource_writer[PropertyNames.Name] = name
        del sf_resource[PropertyNames.Name]
        # print "name:" + name

        # "type" : "Microsoft.Seabreeze/<resource name>"
        sf_resource_writer[PropertyNames.Type] = ArmDocumentGenerator.get_sbz_resource_type(resource_kind, schema_version)
        # print "resource type" + ArmDocumentGenerator.get_sbz_resource_type(resource_kind, schema_version)

        # location
        sf_resource_writer[PropertyNames.Location] = property_value_map[PropertyNames.Location]
        # print "location" + property_value_map[PropertyNames.Location]

        # dependsOn
        sf_resource_writer[PropertyNames.DependsOn] = dependencies.get(ArmDocumentGenerator.get_sbz_resource_name(ArmDocumentGenerator.get_sbz_resource_type(resource_kind, schema_version), name), [])
        # print "depends on" + str(dependencies.get(ArmDocumentGenerator.get_sbz_resource_name(ArmDocumentGenerator.get_sbz_resource_type(resource_kind, schema_version), name), []))

        # Get all JsonProperties for resource, handle the "properties" JsonProperty, write others as is.
        # print "properties"
        for prop in sf_resource.keys():
            if prop == PropertyNames.Properties:
                properties = sf_resource.get(prop)
                properties = ArmDocumentGenerator.process_resource_refs(properties, schema_version)
                sf_resource_writer[prop] = properties
                # print properties
            else:
                sf_resource_writer[prop] = sf_resource.get(prop)
                # print sf_resource.get(prop)
        if PropertyNames.Resources in writer:
            writer[PropertyNames.Resources].append(sf_resource_writer)
        else:
            writer[PropertyNames.Resources] = [sf_resource_writer]
        return writer

    
    @staticmethod
    def get_resource_kind_and_description(resource):
        if len(resource) != 1:
            raise ValueError("More than one resource found - %s" %resource)
        name = resource.keys()[0]
        if not isinstance(name, basestring): 
            raise ValueError("Unknown format - %s for %s" %(type(name), name))
        description = resource[name]
        # print "kind:" + str(name) + "\ndescription:" + str(description)
        return name, description

    @staticmethod
    def get_sbz_resource_type(resource_type, schema_version):
        # print "resource_type:\n" + resource_type
        if resource_type == Constants.Secret:
            return Schema.SchemaVersionSupportedResourcesTypeMap[schema_version][Constants.Secrets]
        elif resource_type == Constants.SecretValue:
            return Schema.SchemaVersionSupportedResourcesTypeMap[schema_version][Constants.SecretValues]
        elif resource_type ==  Constants.Network:
            return Schema.SchemaVersionSupportedResourcesTypeMap[schema_version][Constants.Networks]

        elif resource_type == Constants.Volume:
            return Schema.SchemaVersionSupportedResourcesTypeMap[schema_version][Constants.Volumes]
        elif resource_type == Constants.Application:
            return Schema.SchemaVersionSupportedResourcesTypeMap[schema_version][Constants.Applications]
        else:
            raise ValueError("Unknown SF resource %s" %(resource_type))
        

    @staticmethod
    def get_sbz_resource_name(resource_type, name):
        if resource_type in Schema.HierarchichalSbzResourceNameBuilderMap:
            resource_format_string = Schema.HierarchichalSbzResourceNameBuilderMap[resource_type]
            name = name.split('/')
            return resource_format_string.format(name[0], name[1])
        else:
            return "{0}/{1}".format(resource_type, name)



if __name__ == '__main__':
    ArmDocumentGenerator.generate(["D:\SFMergeUtility\samples\IntermediateJSON\merged-0003_volume_counterVolumeWindows.json",
                                    "D:\SFMergeUtility\samples\IntermediateJSON\merged-0002_secretValue_azurefilesecret_v1.json",
                                    "D:\SFMergeUtility\samples\IntermediateJSON\merged-0001_secret_azurefilesecret.json",
                                    "D:\SFMergeUtility\samples\IntermediateJSON\merged-0004_application_counterApp.json"
                                    ], "eastus", "merged-arm_rp.json")

    ''' ArmDocumentGenerator.get_dependencies(
        ["D:\SFMergeUtility\samples\IntermediateJSON\merged-0003_volume_counterVolumeWindows.json",
     "D:\SFMergeUtility\samples\IntermediateJSON\merged-0002_secretValue_azurefilesecret_v1.json",
     "D:\SFMergeUtility\samples\IntermediateJSON\merged-0001_secret_azurefilesecret.json",
     "D:\SFMergeUtility\samples\IntermediateJSON\merged-0004_application_counterApp.json"]
     )'''