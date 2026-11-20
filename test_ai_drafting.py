import pytest
from ai_drafting import validate_draft
from extras import marker,tiled_pdf

def fixture():
    return dict(design='Example only',assumptions=['Hidden details unknown'],sewing=['Review seams'],pieces=[dict(name='Cuff',quantity=2,fold=False,grain='horizontal',points=[[0,0],[30,0],[30,6],[0,6]],edges=['seam']*4),dict(name='Front panel',quantity=2,fold=False,grain='vertical',points=[[0,0],[20,0],[35,80],[0,80]],edges=['seam','seam','hem','seam'])])

def test_dynamic():
    d=validate_draft(fixture(),1.5); assert len(d['pieces'])==2 and d['pieces'][0]['name']=='Cuff'; assert 'utilisation' in marker(d['pieces']); assert tiled_pdf(d['pieces']).startswith(b'%PDF')

def test_crossing():
    f=fixture();f['pieces'][0]['points']=[[0,0],[30,6],[30,0],[0,6]]
    with pytest.raises(ValueError):validate_draft(f,1.5)

def test_nan():
    f=fixture();f['pieces'][0]['points'][0][0]=float('nan')
    with pytest.raises(ValueError):validate_draft(f,1.5)
