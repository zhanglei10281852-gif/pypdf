"""Compare default merge semantics with the registered baseline in separate processes."""
import json
import sys
from io import BytesIO
from pathlib import Path

sys.path.insert(0, sys.argv[1])
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ArrayObject, DictionaryObject, Fit, NameObject, RectangleObject, TextStringObject

source = PdfWriter()
for width in (100, 200, 300):
    source.add_blank_page(width, 400)
source.add_named_destination('name', 1, fit=Fit.xyz(10, 20, 2))
source.add_outline_item('title', 1)
source.pages[0][NameObject('/Annots')] = ArrayObject([source._add_object(DictionaryObject({
    NameObject('/Type'): NameObject('/Annot'), NameObject('/Subtype'): NameObject('/Link'),
    NameObject('/Rect'): RectangleObject([0, 0, 10, 10]), NameObject('/Dest'): TextStringObject('name'),
}))])
buffer = BytesIO()
source.write(buffer)
rows = []
for mode in ('omitted', 'None', 'empty'):
    reader = PdfReader(BytesIO(buffer.getvalue()))
    writer = PdfWriter()
    writer.add_blank_page(50, 50)
    kw = {} if len(sys.argv) < 3 or mode == 'omitted' else {'named_destination_prefix': None if mode == 'None' else ''}
    writer.append(reader, None, [0, 1], True, (), **kw)
    writer.merge(0, reader, None, (0, 2), True, (), **kw)
    out = BytesIO()
    writer.write(out)
    pdf = PdfReader(out)
    rows.append({'mode': mode, 'widths': [float(p.mediabox.width) for p in pdf.pages],
                 'names': {str(k): [pdf.get_destination_page_number(d), str(d.typ), list(map(str, d.dest_array[2:]))] for k, d in pdf.named_destinations.items()},
                 'links': [[str(a.get_object().get('/Dest')) for a in p.get('/Annots', [])] for p in pdf.pages],
                 'outlines': [(o.title, pdf.get_destination_page_number(o)) for o in pdf.outline]})
print(json.dumps(rows, ensure_ascii=False, indent=2))
