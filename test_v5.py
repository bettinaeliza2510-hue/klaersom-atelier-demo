import pytest
from modular import build
from config import PRESETS,DEFAULT_OPTIONS
from unittest.mock import patch
import gemini
M={**PRESETS['medium'],**DEFAULT_OPTIONS}
S=dict(neckline='v',collar='notched',closure='front_buttons',sleeve='puff',cuffs=True,skirt='flared',sash=False,unsupported='')
def test_shirt():
 d=build(S,M); names=[p['name'] for p in d['pieces']]; assert 'Cuff prototype' in names and 'Centre-front placket' in names and 'Sash' not in names

def test_sleeveless():
 d=build(dict(S,neckline='square',collar='none',closure='back_zip',sleeve='none',cuffs=False),M); assert len(d['pieces'])==4

def test_unsupported():
 with pytest.raises(ValueError):build(dict(S,unsupported='corset'),M)

def test_discovery():
 with patch.object(gemini,'call',return_value={'models':[{'name':'models/gemini-demo-flash','supportedGenerationMethods':['generateContent']},{'name':'models/gemini-demo-flash-image','supportedGenerationMethods':['generateContent']}]}):assert gemini.models()==['gemini-demo-flash']
