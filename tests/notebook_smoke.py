from pathlib import Path
import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager
root=Path(__file__).resolve().parents[1]
for name in ['training.ipynb','exam.ipynb']:
    nb=nbformat.read(root/name,as_version=4)
    nbformat.validate(nb)
    km=KernelManager(kernel_name='python3')
    km.kernel_spec.argv=[str(root/'.venv/bin/python'),'-m','ipykernel_launcher','-f','{connection_file}']
    client=NotebookClient(nb,km=km,timeout=30,resources={'metadata':{'path':str(root)}},allow_errors=False)
    try:
        client.execute()
        errors=[o for c in nb.cells if c.cell_type=='code' for o in c.outputs if o.output_type=='error']
        assert not errors, errors
        assert any('PostgreSQL подключен' in o.get('text','') for c in nb.cells if c.cell_type=='code' for o in c.outputs) if name=='training.ipynb' else True
        print('PASS: executed',name,len(nb.cells),'cells without errors')
    finally:
        if km.has_kernel: km.shutdown_kernel(now=True)
print('NOTEBOOK SMOKE PASSED')
