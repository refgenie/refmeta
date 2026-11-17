-- schema of https://annotationhub.bioconductor.org/metadata/annotationhub.sqlite3 (database_timestamp 2026-11-13 18:57:25), retrieved 2026-11-17
CREATE TABLE `biocversions`(`id` integer DEFAULT (NULL) NOT NULL PRIMARY KEY , `biocversion` varchar(255) DEFAULT (NULL) NULL, `resource_id` integer DEFAULT (NULL) NULL, CONSTRAINT `biocversions_ibfk_1` FOREIGN KEY (`resource_id`) REFERENCES `resources`(`id`));
CREATE TABLE `input_sources`(`id` integer DEFAULT (NULL) NOT NULL PRIMARY KEY , `sourcesize` varchar(255) DEFAULT (NULL) NULL, `sourceurl` varchar(255) DEFAULT (NULL) NULL, `sourceversion` varchar(255) DEFAULT (NULL) NULL, `sourcemd5` varchar(255) DEFAULT (NULL) NULL, `sourcelastmodifieddate` date DEFAULT (NULL) NULL, `resource_id` integer DEFAULT (NULL) NULL, `sourcetype` varchar(255) DEFAULT (NULL) NULL, CONSTRAINT `input_sources_ibfk_1` FOREIGN KEY (`resource_id`) REFERENCES `resources`(`id`));
CREATE TABLE `location_prefixes` (`id` integer NOT NULL PRIMARY KEY , `location_prefix` varchar(255));
CREATE TABLE `rdatapaths`(`id` integer DEFAULT (NULL) NOT NULL PRIMARY KEY , `rdatapath` varchar(255) DEFAULT (NULL) NULL, `rdataclass` varchar(255) DEFAULT (NULL) NULL, `resource_id` integer DEFAULT (NULL) NULL, `dispatchclass` varchar(255) DEFAULT (NULL) NULL, CONSTRAINT `rdatapaths_ibfk_1` FOREIGN KEY (`resource_id`) REFERENCES `resources`(`id`));
CREATE TABLE `recipes` (`id` integer NOT NULL PRIMARY KEY , `recipe` varchar(255), `package` varchar(255));
CREATE TABLE `resources` (`id` integer NOT NULL PRIMARY KEY , `ah_id` varchar(255) NOT NULL, `title` varchar(255), `dataprovider` text, `species` varchar(255), `taxonomyid` integer, `genome` varchar(255), `description` text, `coordinate_1_based` boolean, `maintainer` varchar(255), `status_id` integer, `location_prefix_id` integer, `recipe_id` integer, `rdatadateadded` date, `rdatadateremoved` date, `record_id` integer, `preparerclass` varchar(255));
CREATE TABLE `schema_info` (`version` integer DEFAULT (0) NOT NULL);
CREATE TABLE `statuses` (`id` integer NOT NULL PRIMARY KEY , `status` varchar(255));
CREATE TABLE `tags`(`tag` varchar(400) DEFAULT (NULL) NULL, `resource_id` integer DEFAULT (NULL) NULL, CONSTRAINT `tags_ibfk_1` FOREIGN KEY (`resource_id`) REFERENCES `resources`(`id`));
CREATE TABLE `test` (`id` integer NOT NULL PRIMARY KEY , `name` varchar(255) NOT NULL);
CREATE TABLE `timestamp` (`timestamp` timestamp DEFAULT (datetime(CURRENT_TIMESTAMP, 'localtime')) NOT NULL);
CREATE INDEX `biocversions_resource_id` ON `biocversions` (`resource_id`);
CREATE INDEX `input_sources_resource_id` ON `input_sources` (`resource_id`);
CREATE INDEX `rdatapaths_resource_id` ON `rdatapaths` (`resource_id`);
CREATE INDEX `tags_resource_id` ON `tags` (`resource_id`);

-- statuses table contents
-- (1, 'Unreviewed')
-- (2, 'Public')
-- (3, 'Private')
-- (4, 'Removed from original web location')
-- (5, 'Removed by author request')
-- (6, 'Moved from AnnotationHub to ExperimentHub')
-- (7, 'Replaced by more current version')
-- (8, 'Invalid metadata')
-- (9, 'Did not make review deadline for biocversion')
-- (10, 'Defunct')
