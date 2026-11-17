<!-- Source: https://rest.ensembl.org/documentation/info/info_genomes_assembly (retrieved 2026-11-17; HTML converted to text, client code samples removed) -->
# GET info/genomes/assembly/:assembly_id

Find information about a genome with a specified assembly

## Parameters

### Required

| Name | Type | Description | Default | Example Values

|  assembly_id   | String  | INSDC assembly ID (optionally versioned)  |  -   |  GCA_902167145.1

### Optional

| Name | Type | Description | Default | Example Values

|  callback   | String  | Name of the callback subroutine to be returned by the requested JSONP response. Required ONLY when using JSONP as the serialisation method. Please see the user guide.  |  -   |  randomlygeneratedname

|  expand   | Boolean(0,1)  | Expands the information to include details of sequences. Can be very large.  |  NULL   |  -


### Resource Information

| Methods | GET

| Response formats | json
xml
jsonp
