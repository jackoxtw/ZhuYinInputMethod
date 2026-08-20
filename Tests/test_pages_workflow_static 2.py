from pathlib import Path


workflow = (Path(__file__).resolve().parents[1] / '.github/workflows/deploy-html-demo.yml').read_text()

assert 'uses: actions/configure-pages@v5' in workflow
assert 'enablement: true' in workflow

print('pages workflow enablement: OK')
