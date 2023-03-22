=====
khalti_kfields
=====

khalti_fields is a collection Django Fields to fullfill certain customizations needs.
Detailed documentation is in the "docs" directory.

Quick start
-----------


	pip3 install --index-url http://<IP>:<PORT> khalti_kfields --trusted-host <IP>


	Examples:
		pip3 install --index-url http://172.26.0.1:8123/simple/ --extra-index-url https://pypi.org/simple khalti_kfields==0.0.1 --trusted-host 172.26.0.1



Contents:
-----------


	1: KIdxField
	-----------

		
		- This field overrride Django Default CharField and creats ShortUUID with configurable Prefix
		
		- Always unique and unblank able
		
		- Created field will have only specific characters 23456789ABCDEFGHJKMNPQRSTUVWXYZ
		  This is to reduce confusions between zero (0) and O (Alphabet), 1 and l and so on.
		
		- default max length is 15 but can be reconfigured with max_length parameter.
		
		- default lenght is 9 but can be reconfigured with length parameter.
		  Format: <PREFIX:2><YEAR:2><ShortUUID:8>
		  prefix is configurable with KIDX_MODEL_MAP varaible from settings
		
		
		example: 
			
			settings.py:
				KIDX_MODEL_MAP = {
					"appname_modelname": "TR"
				}

			generate KIDX = TR235TSH45TD

		usage:
			from django.db import models
			class DJANGOModel(models.Model):
				idx = KIdxField()


	2: CreatedDateField
	-----------

		
		- This field overrride Django Default DateField and creats date as per local timezone
		  Word run on AD (Anno Domini) and nepal runs on BS (Bikram Samvat)
		
		- This field stores auto BS date
		
		- By default it db_index = True
		
		- By default converst created_on field to BS, if not found convert timezone.now() to bs and store
	
		usage:
			from django.db import models
			class DJANGOModel(models.Model):
				created_on_bs = CreatedDateField()
	
	3: InforcedKeyJSONField
	-----------

		- This field overrride Django Default JSONField and help control over possibel keys and schema
		
		- Have 3 possible models:
		
			a: Full 
				- Here developer can specify full valid schema
				example:
					meta = InforcedKeyJSONField(full=True, schema='schemas/jsonschema.example.json')
				
				Note: if full=True, schema parameter is must		

				read_time_validate paramter is by default false
					this flag controls if developer need readtime validaiton on stored data
					
				This helps on conditions when some places invalid json (Not as per schema) directly from database 
				(If someone try from django environment Django Field validation would not allow against schema but this flag will 					 provide necessary precautions if someone temper directly from database)
				
				Schema Samples (To learn deeper follow https://json-schema.org/learn/getting-started-step-by-step):
					
					Sample 1:
					-----------

						{
						"title" : "work experience",
						"type" : "object",
						"additionalProperties": false,
						"properties":{
							"data": {"type": "array",
							"items": {
								"properties" : {
									"job_title": {"type": "string"},
									"speciality": {"type": "string"},
									"company": {"type": "string"},
									"address": {"type": "string"},
									"date_from": {"type": "string", "format": "date"},
									"date_to": {"type": "string", "format": "date"}
								}
							}
							}
						}
						}			

					Sample 2: 
					-----------

						{   
						"title": "Product",
						"description": "A product from Acme's catalog",
						"type": "object",
						"properties": {
							"productId": {
							"description": "The unique identifier for a product",
							"type": "integer"
							},
							"productName": {
							"description": "Name of the product",
							"type": "string"
							},
							"price": {
							"description": "The price of the product",
							"type": "number",
							"exclusiveMinimum": 0
							},
							"tags": {
							"description": "Tags for the product",
							"type": "array",
							"items": {
								"type": "string"
							},
							"minItems": 1,
							"uniqueItems": true
							}
						},
						"required": [ "productId", "productName", "price" ]
						}

			b: partial 
			-----------

				- Here developer can specify allowed keys unconcerned about their values
		
				- This will inforce keys as must
				
				example:
				
					meta = InforcedKeyJSONField(partial=True, allowed_keys={"key1", "key2"})
				
				Note: if partial=True, allowed_keys parameter is must		

			c: None 
			-----------

				- Normal JSONField
				
				example:
					meta = InforcedKeyJSONField()

