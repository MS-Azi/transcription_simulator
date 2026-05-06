#!/usr/bin/env python3
"""
bio_cli.py — Bio Sequence Hub Command-Line Interface
=====================================================
Standalone CLI for core bioinformatics operations.
Completely independent of the Flask web application.

Usage (argparse mode):
    python bio_cli.py transcribe       -s ATGCGT -t dna_coding
    python bio_cli.py translate        -s AUGCGUUAA
    python bio_cli.py analyze          -s ATGCGTCAC
    python bio_cli.py reverse-transcribe -s AUGCGU
    python bio_cli.py fetch-ensembl    -i ENST00000380152

Usage (interactive mode — no arguments):
    python bio_cli.py
"""

import argparse
import sys

# Import core biology functions — no Flask required
from bio_logic import (
    clean_sequence,
    get_mrna,
    translate_to_protein,
    analyze_composition,
    reverse_transcribe,
    fetch_ensembl_sequence,
)

# ── ANSI colour helpers ───────────────────────────────────────────────────────

RESET  = '\033[0m'
BOLD   = '\033[1m'
CYAN   = '\033[96m'
GREEN  = '\033[92m'
YELLOW = '\033[93m'
RED    = '\033[91m'
DIM    = '\033[2m'

def _h(label: str) -> str:
    return f"{BOLD}{CYAN}{label}{RESET}"

def _ok(val: str) -> str:
    return f"{GREEN}{val}{RESET}"

def _warn(val: str) -> str:
    return f"{YELLOW}{val}{RESET}"

def _err(val: str) -> str:
    return f"{RED}{val}{RESET}"


# ── Sub-command handlers ──────────────────────────────────────────────────────

def cmd_transcribe(args):
    seq = clean_sequence(args.sequence)
    if not seq:
        print(_err("Error: sequence is empty after cleaning."), file=sys.stderr)
        sys.exit(1)
    mrna = get_mrna(seq, args.type)
    print(f"{_h('Input  (' + args.type + '):')} {seq}")
    print(f"{_h('mRNA output:             ')} {_ok(mrna)}")


def cmd_translate(args):
    seq = clean_sequence(args.sequence)
    if not seq:
        print(_err("Error: sequence is empty after cleaning."), file=sys.stderr)
        sys.exit(1)
    result = translate_to_protein(seq)
    print(f"{_h('Codons (from AUG):')}")
    print(f"  {result['codons_spaced']}")
    print(f"{_h('Protein chain:')}")
    print(f"  {_ok(result['protein_chain'])}")


def cmd_analyze(args):
    seq = clean_sequence(args.sequence)
    if not seq:
        print(_err("Error: sequence is empty after cleaning."), file=sys.stderr)
        sys.exit(1)
    comp = analyze_composition(seq)
    print(f"{_h('Sequence length:')} {comp['total']} nt")
    print(f"{_h('GC Content:    ')} {_ok(str(comp['gc_content']) + '%')}")
    print(f"{_h('Nucleotide breakdown:')}")
    bar_max = max(comp['counts'].values()) if comp['counts'] else 1
    for nuc, count in comp['counts'].items():
        pct   = comp['percentages'][nuc]
        bar   = '█' * int((count / bar_max) * 30)
        print(f"  {BOLD}{nuc}{RESET}  {bar:<30} {count:>4}  ({pct}%)")


def cmd_reverse_transcribe(args):
    seq = clean_sequence(args.sequence)
    if not seq:
        print(_err("Error: sequence is empty after cleaning."), file=sys.stderr)
        sys.exit(1)
    cdna = reverse_transcribe(seq)
    print(f"{_h('Input RNA:          ')} {seq}")
    print(f"{_h('cDNA (sense strand):')} {_ok(cdna)}")


def cmd_fetch_ensembl(args):
    eid = args.id.strip()
    print(f"{DIM}Fetching {eid} from Ensembl REST API…{RESET}")
    result = fetch_ensembl_sequence(eid)
    if result['success']:
        seq = result['sequence']
        print(f"{_h('ID:      ')} {eid}")
        print(f"{_h('Type:    ')} {result.get('molecule', 'unknown')}")
        print(f"{_h('Desc:    ')} {result.get('desc', '')}")
        print(f"{_h('Length:  ')} {len(seq)} nt")
        preview = seq[:80] + ('…' if len(seq) > 80 else '')
        print(f"{_h('Sequence:')} {_ok(preview)}")
        if args.output:
            with open(args.output, 'w') as f:
                f.write(seq)
            print(f"{DIM}Full sequence saved to {args.output}{RESET}")
    else:
        print(_err(f"Error: {result['error']}"), file=sys.stderr)
        sys.exit(1)


# ── Interactive (REPL) mode ───────────────────────────────────────────────────

COMMANDS_HELP = """
Commands:
  transcribe        — DNA or RNA → mRNA
  translate         — mRNA → amino acid protein chain
  analyze           — nucleotide composition & GC content
  reverse-transcribe — RNA → cDNA
  fetch-ensembl     — download sequence from Ensembl by ID
  help              — show this message
  quit / exit       — exit
"""

def interactive_mode():
    print(f"\n{BOLD}{CYAN}╔══════════════════════════════════════╗{RESET}")
    print(f"{BOLD}{CYAN}║    Bio Sequence Hub  — CLI Mode      ║{RESET}")
    print(f"{BOLD}{CYAN}╚══════════════════════════════════════╝{RESET}")
    print(COMMANDS_HELP)

    while True:
        try:
            cmd = input(f"{CYAN}bio>{RESET} ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not cmd:
            continue

        if cmd in ('quit', 'exit', 'q'):
            print("Bye!")
            break

        elif cmd == 'help':
            print(COMMANDS_HELP)

        elif cmd == 'transcribe':
            seq   = input("  Sequence (DNA or RNA): ").strip()
            stype = input("  Type [rna / dna_coding / dna_template] (default: rna): ").strip() or 'rna'
            if stype not in ('rna', 'dna_coding', 'dna_template'):
                print(_warn("  Unknown type — defaulting to 'rna'"))
                stype = 'rna'
            clean = clean_sequence(seq)
            mrna  = get_mrna(clean, stype)
            print(f"  {_h('mRNA:')} {_ok(mrna)}\n")

        elif cmd == 'translate':
            seq    = input("  mRNA sequence: ").strip()
            clean  = clean_sequence(seq)
            result = translate_to_protein(clean)
            print(f"  {_h('Codons:  ')} {result['codons_spaced']}")
            print(f"  {_h('Protein: ')} {_ok(result['protein_chain'])}\n")

        elif cmd == 'analyze':
            seq  = input("  Sequence: ").strip()
            clean = clean_sequence(seq)
            comp = analyze_composition(clean)
            print(f"  Length: {comp['total']} nt   GC: {_ok(str(comp['gc_content']) + '%')}")
            for nuc, count in comp['counts'].items():
                print(f"    {BOLD}{nuc}{RESET}: {count}  ({comp['percentages'][nuc]}%)")
            print()

        elif cmd == 'reverse-transcribe':
            seq  = input("  RNA sequence: ").strip()
            clean = clean_sequence(seq)
            cdna = reverse_transcribe(clean)
            print(f"  {_h('cDNA:')} {_ok(cdna)}\n")

        elif cmd == 'fetch-ensembl':
            eid    = input("  Ensembl ID (e.g. ENST00000380152): ").strip()
            print(f"  {DIM}Fetching…{RESET}")
            result = fetch_ensembl_sequence(eid)
            if result['success']:
                seq = result['sequence']
                print(f"  {_h('Type:    ')} {result.get('molecule', '?')}")
                print(f"  {_h('Length:  ')} {len(seq)} nt")
                preview = seq[:80] + ('…' if len(seq) > 80 else '')
                print(f"  {_h('Sequence:')} {_ok(preview)}")
                save = input("  Save full sequence to file? (filename or Enter to skip): ").strip()
                if save:
                    with open(save, 'w') as f:
                        f.write(seq)
                    print(f"  {DIM}Saved to {save}{RESET}")
            else:
                print(f"  {_err('Error: ' + result['error'])}")
            print()

        else:
            print(_warn(f"  Unknown command '{cmd}'. Type 'help' for a list.\n"))


# ── Argument parser setup ─────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='bio_cli',
        description='Bio Sequence Hub — Command-Line Interface',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python bio_cli.py transcribe -s ATGCGT -t dna_coding\n"
            "  python bio_cli.py translate -s AUGCGUUAA\n"
            "  python bio_cli.py analyze -s ATGCGTCAC\n"
            "  python bio_cli.py reverse-transcribe -s AUGCGU\n"
            "  python bio_cli.py fetch-ensembl -i ENST00000380152 -o seq.txt\n"
            "\nRun with no arguments to enter interactive mode."
        ),
    )
    sub = parser.add_subparsers(dest='command', metavar='<command>')

    # transcribe
    p = sub.add_parser('transcribe', help='Transcribe DNA/RNA sequence to mRNA')
    p.add_argument('-s', '--sequence', required=True, help='Input nucleotide sequence')
    p.add_argument('-t', '--type', default='rna',
                   choices=['rna', 'dna_coding', 'dna_template'],
                   help='Sequence type (default: rna)')
    p.set_defaults(func=cmd_transcribe)

    # translate
    p = sub.add_parser('translate', help='Translate mRNA → amino acid protein chain (AUG-first)')
    p.add_argument('-s', '--sequence', required=True, help='mRNA (or DNA) sequence')
    p.set_defaults(func=cmd_translate)

    # analyze
    p = sub.add_parser('analyze', help='Nucleotide composition + GC content + sequence length')
    p.add_argument('-s', '--sequence', required=True, help='Nucleotide sequence')
    p.set_defaults(func=cmd_analyze)

    # reverse-transcribe
    p = sub.add_parser('reverse-transcribe', help='Reverse transcribe RNA → cDNA')
    p.add_argument('-s', '--sequence', required=True, help='RNA sequence')
    p.set_defaults(func=cmd_reverse_transcribe)

    # fetch-ensembl
    p = sub.add_parser('fetch-ensembl', help='Download sequence from Ensembl REST API by ID')
    p.add_argument('-i', '--id', required=True, help='Ensembl ID (ENSG…, ENST…, ENSE…)')
    p.add_argument('-o', '--output', default=None, metavar='FILE',
                   help='Save full sequence to this file (optional)')
    p.set_defaults(func=cmd_fetch_ensembl)

    return parser


def main():
    parser = build_parser()
    args   = parser.parse_args()

    if args.command is None:
        # No subcommand given — drop into interactive REPL
        interactive_mode()
    else:
        args.func(args)


if __name__ == '__main__':
    main()
