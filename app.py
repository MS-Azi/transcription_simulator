from flask import Flask, render_template, request, jsonify
from bio_logic import (
    clean_sequence, get_mrna, translate_to_protein,
    analyze_composition, reverse_transcribe, fetch_ensembl_sequence,
)

app = Flask(__name__)
app.secret_key = 'biological-animations'


@app.route('/', methods=['GET', 'POST'])
def index():
    context = {}
    if request.method == 'POST':
        raw_sequence = ''

        file = request.files.get('file')
        if file and file.filename.endswith('.csv'):
            try:
                content = file.read().decode('utf-8')
                lines = content.split('\n')
                raw_sequence = ''.join(lines[1:] if len(lines) > 1 else lines)
            except Exception as e:
                context['error'] = f"Could not read CSV file: {e}"
        else:
            raw_sequence = request.form.get('sequence', '')

        seq_type = request.form.get('seq_type', 'rna')

        if raw_sequence.strip():
            # Step 1: always force uppercase and strip whitespace first
            clean_original = clean_sequence(raw_sequence)
            context['original_sequence'] = clean_original
            context['seq_type'] = seq_type

            # Step 2: Composition analysis (GC content included)
            composition = analyze_composition(clean_original)
            context['composition'] = composition

            # Step 3: Transcription / Reverse Transcription pathway
            if seq_type == 'reverse_transcription':
                cdna = reverse_transcribe(clean_original)
                context['cdna_sequence'] = cdna
                context['is_reverse_transcription'] = True
                # Translation uses the original RNA as the mRNA source
                translation_input = clean_original
            else:
                mrna_result = get_mrna(clean_original, seq_type)
                context['mrna_sequence'] = mrna_result
                translation_input = mrna_result

            # Step 4: Translate — scans for AUG start codon first
            translation_results = translate_to_protein(translation_input)
            context['codons_spaced'] = translation_results['codons_spaced']
            context['protein_chain'] = translation_results['protein_chain']

            context['show_results'] = True

    return render_template('index.html', **context)


@app.route('/fetch_ensembl', methods=['POST'])
def fetch_ensembl():
    """API endpoint: fetch a sequence from Ensembl by ID."""
    data = request.get_json(silent=True) or {}
    ensembl_id = data.get('ensembl_id', '').strip()
    if not ensembl_id:
        return jsonify({'success': False, 'error': 'No Ensembl ID provided.'})
    result = fetch_ensembl_sequence(ensembl_id)
    return jsonify(result)


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=False, host='0.0.0.0', port=port)
