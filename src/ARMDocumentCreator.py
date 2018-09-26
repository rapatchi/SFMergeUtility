import json
from PropertyNames import PropertyNames
from Constants import Constants
from Schema import Schema
from ArmParameter import ArmParameter, MetaData

class ArmDocumentGenerator:

    @staticmethod
    def generate(sf_json_resources, region, output_file_name):
        with open(output_file_name, 'w') as fp:
            arm_dict = {}
            parameter_info = {}
            property_value_map = {}
            arm_dict = ArmDocumentGenerator.begin_write_arm_document(arm_dict)
            parameter_info[PropertyNames.Location] = ArmDocumentGenerator.get_location_parameter(region)
            property_value_map[PropertyNames.Location] = "[" + PropertyNames.Parameters + "('" + PropertyNames.Location +"')]"
            # print "arm_dict:" + json.dumps(arm_dict)
            # print "property_value_map" + json.dumps(property_value_map)
            arm_dict = ArmDocumentGenerator.write_parameters(arm_dict, parameter_info)
            print "write parametersarm_dict: \n" + json.dumps(arm_dict)
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
        return json.dumps(writer)

    @staticmethod
    def write_parameters(writer, parameters_info):
        if not PropertyNames.Parameters in writer:
            writer[PropertyNames.Parameters] = {}
        for parameter in parameters_info.keys():
            writer[PropertyNames.Parameters][parameter] = parameters_info[parameter].to_dict()
        return writer

    @staticmethod
    def write_arm_resources(writer, sf_json_resources, property_value_map):
        dependencies = ArmDocumentGenerator.get_dependencies(sf_json_resources)
        for sf_json_resource in sf_json_resources:
            sf_resource = json.loads(sf_json_resource)
            kind, description = ArmDocumentGenerator.get_resource_kind_and_description(sf_resource)
            print "kind:" + kind + "description:" + description
            exit()
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
        dependencies = {}
        resource_types = {}
        for sf_json_resource in sf_json_resources:
            name = ""
            kind = ""
            resource = json.load(sf_json_resource)
            kind, description = ArmDocumentGenerator.get_resource_kind_and_description(resource)
            schemaversion = Constants.DefaultSchemaVersion
            for prop, value in description.items():
                if prop == PropertyNames.SchemaVersion:
                    schemaversion = value
                elif prop == PropertyNames.Name:
                    name = value

            if name == "" or kind == "":
                raise ValueError("Required properties name or kind missing")

            if kind in resource_types:
                resource_types[kind] = ArmDocumentGenerator.get_sbz_resource_name(ArmDocumentGenerator.get_sbz_resource_type(kind, schemaversion), name)
            else:
                resource_types[kind].append(ArmDocumentGenerator.get_sbz_resource_name(ArmDocumentGenerator.get_sbz_resource_type(kind, schemaversion), name))

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

        return dependencies    


    @staticmethod
    def process_application(writer, application, dependencies, property_value_map):
        if not PropertyNames.Name in  application:
            raise ValueError("name is not specified in description")
        
        name = application.get(PropertyNames.Name)

        # apiVersion
        schema_version = Constants.DefaultSchemaVersion
        if PropertyNames.SchemaVersion in application:
            schema_version = application[PropertyNames.SchemaVersion]
            # schemaVersion is not needed by RP, so remove it.
            del application[PropertyNames.SchemaVersion]

        writer[PropertyNames.ApiVersion] = Schema.SchemaVersionSupportedResourcesTypeMap[schema_version]

        # name
        writer[PropertyNames.Name] = name
        del application[PropertyNames.Name]

        # type: Microsoft.Seabreeze/applications
        writer[PropertyNames.Type] = Schema.SchemaVersionSupportedResourcesTypeMap[schema_version][Constants.Applications]

        # location
        writer[PropertyNames.Location] = property_value_map[PropertyNames.Location]

        # dependsOn
        writer[PropertyNames.DependsOn] = dependencies.get(ArmDocumentGenerator.get_sbz_resource_name(ArmDocumentGenerator.get_sbz_resource_type(Constants.Application, schema_version), name))

        del application[PropertyNames.Kind]
        
        # Get all JsonProperties for application, handle the "properties" JsonProperty, write others as is.
        for app_property in application.keys():
            if app_property == PropertyNames.Properties:
                properties = app_property.get(app_property)
                for prop in properties.keys():
                    if prop == Constants.Services:
                        writer = ArmDocumentGenerator.process_services(writer, prop[app_property][prop], schema_version)
                    else:
                        writer[app_property][prop] = properties[prop]
            else:
                writer[app_property] = application.get(app_property)
        return writer



    @staticmethod
    def process_services(writer, services, schema_version):
        for service in services:
            writer = ArmDocumentGenerator.process_service(writer, service, schema_version)
        return writer

    @staticmethod
    def process_service(writer, service, schema_version):
        service_writer={}
        if not PropertyNames.Name in  service:
            raise ValueError("name is not specified in description")

        name = service.get(PropertyNames.Name)

        # apiVersion
        schema_version = Constants.DefaultSchemaVersion
        if PropertyNames.SchemaVersion in service:
            schema_version = service[PropertyNames.SchemaVersion]
            # schemaVersion is not needed by RP, so remove it.
            del service[PropertyNames.SchemaVersion]

        service_writer[PropertyNames.ApiVersion] = Schema.SchemaVersionSupportedResourcesTypeMap[schema_version]

        # name
        service_writer[PropertyNames.Name] = name
        del service[PropertyNames.Name]

        # Get all JsonProperties for service, handle the "properties" JsonProperty, write others as is.
        for service_property in service.keys():
            if service_property == PropertyNames.Properties:
                properties = service.get(service_property)
                properties = ArmDocumentGenerator.process_resource_refs(properties, schema_version)
                service_writer[service_property] = properties

            else:
                service_writer[service_property] = service.get(service_property)

        writer[PropertyNames.Properties][Constants.Services].append(service_writer)
        return writer
        
    @staticmethod
    def process_resource_refs(properties, schema_version):
        # Todo process resource refs
        return properties

    @staticmethod
    def process_sf_resource(writer, sf_resource, resource_kind, dependencies, property_value_map):
        if not PropertyNames.Name in  sf_resource:
            raise ValueError("name is not specified for %s resource" % resource_kind)
        
        name = sf_resource.get(PropertyNames.Name)

        # apiVersion
        schema_version = Constants.DefaultSchemaVersion
        if PropertyNames.SchemaVersion in sf_resource:
            schema_version = sf_resource[PropertyNames.SchemaVersion]
            # schemaVersion is not needed by RP, so remove it.
            del sf_resource[PropertyNames.SchemaVersion]

        writer[PropertyNames.ApiVersion] = Schema.SchemaVersionSupportedResourcesTypeMap[schema_version]

        # name
        writer[PropertyNames.Name] = name
        del writer[PropertyNames.Name]

        # "type" : "Microsoft.Seabreeze/<resource name>"
        writer[PropertyNames.Name] = ArmDocumentGenerator.get_sbz_resource_type(resource_kind, schema_version)

        # location
        writer[PropertyNames.Location] = property_value_map[PropertyNames.Location]

        # dependsOn
        writer[PropertyNames.DependsOn] = dependencies.get(ArmDocumentGenerator.get_sbz_resource_name(ArmDocumentGenerator.get_sbz_resource_type(resource_kind, schema_version), name))

        # Get all JsonProperties for resource, handle the "properties" JsonProperty, write others as is.
        for prop in sf_resource.keys():
            if prop == PropertyNames.Properties:
                properties = sf_resource.get(prop)
                properties = ArmDocumentGenerator.process_resource_refs(properties, schema_version)
                writer[prop] = properties

            else:
                writer[prop] = sf_resource.get(prop)

        return writer

    
    @staticmethod
    def get_resource_kind_and_description(resource):
        if len(resource) != 1:
            raise ValueError("More than one resource found - %s" %resource)
        name = resource.keys()[0]
        if not isinstance(name, str): 
            raise ValueError("Unknown format - %s" % name)
        description = resource[name]
        return name, description

    @staticmethod
    def get_sbz_resource_type(resource_type, schema_version):
        if resource_type == Constants.Secret:
            return Schema.SchemaVersionSupportedResourcesTypeMap[schema_version][Constants.Secrets]
        elif resource_type == Constants.SecretValue:
            return 
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
            return resource_format_string.format(name.split('/'))
        else:
            return "{0}/{1}".format(resource_type, name)



if __name__ == '__main__':
    ArmDocumentGenerator.generate(["D:\SFMergeUtility\samples\OutputYAML\merged-0003_volume_counterVolumeWindows.yaml"], "eastus", "merged_rp_json.json")