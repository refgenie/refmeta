<!-- Source: https://rest.ensembl.org/documentation/info/info_genome (retrieved 2026-11-17; HTML converted to text, client code samples removed) -->
# GET info/genomes/:genome_name

Find information about a given genome

## Parameters

### Required

| Name | Type | Description | Default | Example Values

|  name   | String  | The production name of the genome.  |  -   |  arabidopsis_thaliana

### Optional

| Name | Type | Description | Default | Example Values

|  callback   | String  | Name of the callback subroutine to be returned by the requested JSONP response. Required ONLY when using JSONP as the serialisation method. Please see the user guide.  |  -   |  randomlygeneratedname

|  expand   | Boolean(0,1)  | Expands the information to include details of sequences. Can be very large.  |  NULL   |  -


### Resource Information

| Methods | GET

| Response formats | json
xml
jsonp
