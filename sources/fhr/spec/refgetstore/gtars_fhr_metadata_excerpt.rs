// EXCERPT (lines 1-178) of gtars-refget/src/store/fhr_metadata.rs
// Repo: https://github.com/databio/gtars  local clone repos/gtars, commit bffa41fa1126c41edf0fb9cea2a842bd5092765c (branch feat/fasta-export)
// Copied 2026-11-17. Types, serde attributes and the sidecar file extension only.

//! FAIR Headers Reference genome (FHR) metadata for sequence collections.
//!
//! This module contains the FHR data types, sidecar JSON I/O functions,
//! and RefgetStore bridge methods for managing FHR metadata.
//!
//! See: https://github.com/FAIR-bioHeaders/FHR-Specification

use super::*;
use super::readonly::ReadonlyRefgetStore;
use super::core::RefgetStore;

use std::collections::HashMap;
use std::fs;
use std::path::Path;

use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};

use crate::hashkeyable::{DigestKey, HashKeyable, key_to_digest_string};

// ============================================================================
// Types
// ============================================================================

/// FAIR Headers Reference genome (FHR) metadata for a sequence collection.
///
/// All fields are optional to allow partial metadata. RefgetStore does not
/// enforce FHR schema compliance -- that's the user's responsibility.
#[derive(Clone, Debug, Serialize, Deserialize, Default)]
#[serde(rename_all = "camelCase")]
pub struct FhrMetadata {
    /// URL to the FHR JSON schema
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub schema: Option<String>,

    /// FHR schema version (numeric per spec, e.g. 1 or 1.0)
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub schema_version: Option<serde_json::Number>,

    /// Genome name (e.g., "Homo sapiens")
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub genome: Option<String>,

    /// Taxonomy information
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub taxon: Option<FhrTaxon>,

    /// Genome version (e.g., "GRCh38.p14")
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub version: Option<String>,

    /// Who created the metadata (ORCID URIs)
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub metadata_author: Option<Vec<FhrAuthor>>,

    /// Who assembled the genome
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub assembly_author: Option<Vec<FhrAuthor>>,

    /// Assembly creation date (ISO 8601)
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub date_created: Option<String>,

    /// Description of the physical sample
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub voucher_specimen: Option<String>,

    /// Masking type
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub masking: Option<String>,

    /// File-level checksum (SHA2-512/256 per FHR spec)
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub checksum: Option<String>,

    /// Alternative common names for this genome
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub genome_synonym: Option<Vec<String>>,

    /// Database accession identifier (single object per spec)
    #[serde(
        default,
        skip_serializing_if = "Option::is_none",
        rename = "accessionID"
    )]
    pub accession_id: Option<FhrIdentifier>,

    /// Sequencing instruments used
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub instrument: Option<Vec<String>>,

    /// DOI or scholarly article reference (single string per spec)
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub scholarly_article: Option<String>,

    /// Documentation about the genome
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub documentation: Option<String>,

    /// Identifiers of the genome (namespace:value format)
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub identifier: Option<Vec<String>>,

    /// License information
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub license: Option<String>,

    /// Related URLs
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub related_link: Option<Vec<String>>,

    /// Funding information (single string per spec)
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub funding: Option<String>,

    /// General statistics about the genome assembly
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub vital_stats: Option<FhrVitalStats>,

    /// Seqcol digest (added by RefgetStore, not part of FHR 1.0)
    #[serde(skip)]
    pub seqcol_digest: Option<String>,

    /// Catch-all for any other FHR fields or custom extensions
    #[serde(flatten)]
    pub extra: HashMap<String, serde_json::Value>,
}

/// General statistics about a genome assembly.
#[derive(Clone, Debug, Serialize, Deserialize, Default)]
#[serde(rename_all = "camelCase")]
pub struct FhrVitalStats {
    #[serde(default, skip_serializing_if = "Option::is_none", rename = "L50")]
    pub l50: Option<i64>,
    #[serde(default, skip_serializing_if = "Option::is_none", rename = "N50")]
    pub n50: Option<i64>,
    #[serde(default, skip_serializing_if = "Option::is_none", rename = "L90")]
    pub l90: Option<i64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub total_base_pairs: Option<i64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub number_contigs: Option<i64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub number_scaffolds: Option<i64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub read_technology: Option<String>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct FhrTaxon {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub name: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub uri: Option<String>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct FhrAuthor {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub name: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub uri: Option<String>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct FhrIdentifier {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub name: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub url: Option<String>,
}

// ============================================================================
// Disk I/O helpers -- called by RefgetStore, no dependency on it
// ============================================================================

pub(crate) const SIDECAR_EXTENSION: &str = ".fhr.json";

