import re
import urllib.request
import json

CODON_TABLE = {
    'UUU': 'Phe', 'UUC': 'Phe', 'UUA': 'Leu', 'UUG': 'Leu',
    'CUU': 'Leu', 'CUC': 'Leu', 'CUA': 'Leu', 'CUG': 'Leu',
    'AUU': 'Ile', 'AUC': 'Ile', 'AUA': 'Ile', 'AUG': 'Met',
    'GUU': 'Val', 'GUC': 'Val', 'GUA': 'Val', 'GUG': 'Val',
    'UCU': 'Ser', 'UCC': 'Ser', 'UCA': 'Ser', 'UCG': 'Ser',
    'CCU': 'Pro', 'CCC': 'Pro', 'CCA': 'Pro', 'CCG': 'Pro',
    'ACU': 'Thr', 'ACC': 'Thr', 'ACA': 'Thr', 'ACG': 'Thr',
    'GCU': 'Ala', 'GCC': 'Ala', 'GCA': 'Ala', 'GCG': 'Ala',
    'UAU': 'Tyr', 'UAC': 'Tyr', 'UAA': 'STOP', 'UAG': 'STOP',
    'CAU': 'His', 'CAC': 'His', 'CAA': 'Gln', 'CAG': 'Gln',
    'AAU': 'Asn', 'AAC': 'Asn', 'AAA': 'Lys', 'AAG': 'Lys',
    'GAU': 'Asp', 'GAC': 'Asp', 'GAA': 'Glu', 'GAG': 'Glu',
    'UGU': 'Cys', 'UGC': 'Cys', 'UGA': 'STOP', 'UGG': 'Trp',
    'CGU': 'Arg', 'CGC': 'Arg', 'CGA': 'Arg', 'CGG': 'Arg',
    'AGU': 'Ser', 'AGC': 'Ser', 'AGA': 'Arg', 'AGG': 'Arg',
    'GGU': 'Gly', 'GGC': 'Gly', 'GGA': 'Gly', 'GGG': 'Gly'
}

def clean_sequence(seq: str) -> str:
    """Force UPPERCASE and strip all non-nucleotide characters — always the first step."""
    return re.sub(r'[^ACGTUacgtu]', '', seq.upper())

def get_mrna(sequence: str, seq_type: str) -> str:
    """Convert a sequence to mRNA based on its type."""
    seq = clean_sequence(sequence)
    if not seq:
        return ""

    if seq_type == 'rna':
        # Already mRNA; just ensure it uses U not T
        return seq.replace('T', 'U')

    elif seq_type == 'dna_coding':
        # Non-Template / Coding strand: same sequence as mRNA, just swap T → U
        return seq.replace('T', 'U')

    elif seq_type == 'dna_template':
        # Template strand given 5'→3': reverse first, then complement each base to get mRNA 5'→3'
        rev = seq[::-1]
        transcription_map = str.maketrans('ATCG', 'UAGC')
        return rev.translate(transcription_map)

    return ""

def reverse_transcribe(rna_seq: str) -> str:
    """Reverse Transcription: convert an RNA sequence back to its complementary DNA (cDNA).
    Replaces U→T, then takes the reverse complement to produce the cDNA coding strand.
    """
    seq = clean_sequence(rna_seq)
    # Replace U with T to get the equivalent DNA sequence (cDNA sense strand)
    return seq.replace('U', 'T')

def analyze_composition(sequence: str) -> dict:
    """Count nucleotides, calculate percentages, and compute GC content."""
    seq = clean_sequence(sequence)
    total_len = len(seq)

    if total_len == 0:
        return {'total': 0, 'counts': {}, 'percentages': {}, 'gc_content': 0.0}

    counts = {'A': 0, 'C': 0, 'G': 0, 'T': 0, 'U': 0}
    for nuc in seq:
        if nuc in counts:
            counts[nuc] += 1

    filtered_counts = {k: v for k, v in counts.items() if v > 0}
    percentages = {k: round((v / total_len) * 100, 2) for k, v in filtered_counts.items()}
    gc_count = counts.get('G', 0) + counts.get('C', 0)
    gc_content = round((gc_count / total_len) * 100, 2)

    return {
        'total': total_len,
        'counts': filtered_counts,
        'percentages': percentages,
        'gc_content': gc_content,
    }

def translate_to_protein(mrna: str) -> dict:
    """Scan mRNA for the AUG start codon, then translate into amino acids.
    Translation only begins after the first AUG is found.
    """
    seq = clean_sequence(mrna).replace('T', 'U')  # normalise to RNA alphabet

    start_idx = seq.find('AUG')
    if start_idx == -1:
        return {
            'codons_spaced': '(No AUG start codon found in sequence)',
            'protein_chain': 'N/A — No start codon detected',
        }

    coding_seq = seq[start_idx:]
    codons = []
    amino_acids = []

    for i in range(0, len(coding_seq) - (len(coding_seq) % 3), 3):
        codon = coding_seq[i:i + 3]
        if len(codon) == 3:
            codons.append(codon)
            aa = CODON_TABLE.get(codon, '?')
            amino_acids.append(aa)
            if aa == 'STOP':
                break

    return {
        'codons_spaced': ' - '.join(codons),
        'protein_chain': ' - '.join(amino_acids),
    }

def fetch_ensembl_sequence(ensembl_id: str) -> dict:
    """Fetch a nucleotide sequence from the Ensembl REST API by Ensembl ID.
    Works with gene IDs (ENSG…), transcript IDs (ENST…), and exon IDs (ENSE…).
    """
    ensembl_id = ensembl_id.strip()
    url = f"https://rest.ensembl.org/sequence/id/{ensembl_id}?content-type=application/json"
    try:
        req = urllib.request.Request(
            url,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'BioSequenceHub/1.0',
            }
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
            return {
                'success': True,
                'sequence': data.get('seq', ''),
                'molecule': data.get('molecule', 'unknown'),
                'desc': data.get('desc', ensembl_id),
            }
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='ignore')
        try:
            msg = json.loads(body).get('error', str(e))
        except Exception:
            msg = f"HTTP {e.code} — ID not found or invalid."
        return {'success': False, 'error': msg}
    except Exception as e:
        return {'success': False, 'error': str(e)}
