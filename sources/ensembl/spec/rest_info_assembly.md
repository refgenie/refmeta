<!-- Source: https://rest.ensembl.org/documentation/info/assembly_info (retrieved 2026-11-17; HTML converted to text, client code samples removed) -->
# GET info/assembly/:species

List the currently available assemblies for a species, along with toplevel sequences, chromosomes and cytogenetic bands.

## Parameters

### Required

| Name | Type | Description | Default | Example Values

|  species   | String  | Species name/alias  |  -   |  homo_sapiens
human

### Optional

| Name | Type | Description | Default | Example Values

|  bands   | Boolean(0,1)  | If set to 1, include karyotype band information. Only display if band information is available  |  0   |  -

|  callback   | String  | Name of the callback subroutine to be returned by the requested JSONP response. Required ONLY when using JSONP as the serialisation method. Please see the user guide.  |  -   |  randomlygeneratedname

|  synonyms   | Boolean(0,1)  | If set to 1, include information about known synonyms.  |  0   |  -


### Resource Information

| Methods | GET

| Response formats | json
xml
jsonp
