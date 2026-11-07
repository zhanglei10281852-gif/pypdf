"""Independent review of the single recorded run; does not change production code."""
import hashlib
import json
import sys
from io import BytesIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pypdf import PdfReader, PdfWriter
from pypdf.generic import (
    ArrayObject, DictionaryObject, Fit, FloatObject, NameObject, RectangleObject, TextStringObject,
)


def reopen(pdf):
    stream = BytesIO()
    pdf.write(stream)
    return PdfReader(stream)


def source(legacy=False, indirect=False):
    pdf = PdfWriter()
    for width in (100, 200, 300):
        pdf.add_blank_page(width=width, height=400)
    pdf.add_named_destination('intro', 1, fit=Fit.xyz(10, 250, 1.5))
    pdf.add_named_destination('章节', 1, fit=Fit.fit_horizontally(123))
    pdf.add_named_destination('omitted', 2)
    if legacy:
        destinations = DictionaryObject({NameObject('/' + k): v.dest_array for k, v in pdf.named_destinations.items()})
        pdf.root_object[NameObject('/Dests')] = destinations
        del pdf.root_object['/Names']
    name = '/intro' if legacy else 'intro'
    destination = TextStringObject(name)
    if indirect:
        destination = pdf._add_object(destination)
    action = pdf._add_object(DictionaryObject({NameObject('/S'): NameObject('/GoTo'), NameObject('/D'): destination}))
    def annotation(entries):
        obj = DictionaryObject({NameObject('/Type'): NameObject('/Annot'), NameObject('/Subtype'): NameObject('/Link'), NameObject('/Rect'): RectangleObject([0, 0, 10, 10])})
        obj.update({NameObject(k): v for k, v in entries.items()})
        return pdf._add_object(obj)
    def named(x):
        return TextStringObject('/' + x if legacy else x)
    pdf.pages[0][NameObject('/Annots')] = ArrayObject([
        annotation({'/Dest': named('intro')}),
        annotation({'/A': action}),
        annotation({'/Dest': named('omitted')}),
        annotation({'/Dest': named('shadow')}),
        annotation({'/A': DictionaryObject({NameObject('/S'): NameObject('/GoTo'), NameObject('/D'): named('shadow')})}),
        annotation({'/Dest': ArrayObject([pdf.pages[1].indirect_reference, NameObject('/FitH'), FloatObject(123)])}),
        annotation({'/A': DictionaryObject({NameObject('/S'): NameObject('/URI'), NameObject('/URI'): TextStringObject('https://example.org/')})}),
        annotation({'/A': DictionaryObject({NameObject('/S'): NameObject('/GoToR'), NameObject('/F'): TextStringObject('remote.pdf'), NameObject('/D'): TextStringObject('remote-anchor')})}),
    ])
    parent = pdf.add_outline_item('Visible title', 1)
    parent.get_object()[NameObject('/A')] = action
    pdf.add_outline_item('Nested title', 1, parent=parent, fit=Fit.xyz(5, 6, 2))
    return reopen(pdf)


def links(pdf, index):
    result = []
    for ref in pdf.pages[index].get('/Annots', []):
        annotation = ref.get_object()
        if '/Dest' in annotation:
            d = annotation['/Dest']
            result.append(('/Dest', str(d) if isinstance(d, str) else ('array', pdf.get_page_number(d[0].get_object()))))
        else:
            a = annotation['/A']
            result.append((str(a['/S']), str(a.get('/D', a.get('/URI')))))
    return result


def outlines(pdf):
    def flatten(items, depth=0):
        result = []
        for item in items:
            if isinstance(item, list):
                result.extend(flatten(item, depth + 1))
            else:
                a = item.node.get('/A')
                action_name = str(a.get_object()['/D']) if a is not None else None
                result.append((depth, item.title, pdf.get_destination_page_number(item), str(item.typ), action_name))
        return result
    return flatten(pdf.outline)


def semantic(pdf):
    return {'pages': [float(p.mediabox.width) for p in pdf.pages],
            'names': {str(k): (pdf.get_destination_page_number(v), str(v.typ), list(map(str, v.dest_array[2:]))) for k, v in pdf.named_destinations.items()},
            'links': [links(pdf, n) for n in range(len(pdf.pages))], 'outline': outlines(pdf)}


def merge(pdf, reader, method, prefix, **kwargs):
    args = (reader,) if method == 'append' else (1, reader)
    getattr(pdf, method)(*args, named_destination_prefix=prefix, **kwargs)


def main():
    observations = []
    for method in ('append', 'merge'):
        for legacy in (False, True):
            reader = source(legacy=legacy)
            before = semantic(reader)
            pdf = PdfWriter()
            pdf.add_blank_page(50, 50)
            pdf.add_named_destination('/shadow' if legacy else 'shadow', 0)
            merge(pdf, reader, method, 'P:章节/', pages=[0, 1])
            output = reopen(pdf)
            for original, d in reader.named_destinations.items():
                if 'omitted' in original:
                    assert 'P:章节/' + original not in output.named_destinations
                    continue
                target = output.named_destinations['P:章节/' + original]
                assert output.get_destination_page_number(target) == 2
                assert list(target.dest_array[1:]) == list(d.dest_array[1:])
            intro = 'P:章节/' + ('/intro' if legacy else 'intro')
            assert links(output, 1)[:2] == [('/Dest', intro), ('/GoTo', intro)]
            assert len(links(output, 1)) == 5
            assert outlines(output)[0] == (0, 'Visible title', 2, '/XYZ', intro)
            assert outlines(output)[1][:3] == (1, 'Nested title', 2)
            assert semantic(reader) == before
            observations.append({'case': method + (' legacy' if legacy else ' name-tree'), 'names': list(output.named_destinations), 'links': links(output, 1), 'outline': outlines(output)})

    for method in ('append', 'merge'):
        reader = source()
        source_before = semantic(reader)
        pdf = PdfWriter()
        pdf.add_blank_page(50, 50)
        merge(pdf, reader, method, 'a-', pages=[0, 1])
        first = semantic(pdf)
        # Force the named collision after one successful import and before any
        # page clone of the rejected import. Retry on the same writer/reader.
        objects_before = len(pdf._objects)
        try:
            merge(pdf, reader, method, 'a-', pages=[0, 1])
        except ValueError as exc:
            assert 'a-intro' in str(exc)
            conflict = str(exc)
        else:
            raise AssertionError('conflict was not rejected')
        assert semantic(pdf) == first
        assert len(pdf._objects) == objects_before
        merge(pdf, reader, method, 'b-', pages=[0, 1])
        out = reopen(pdf)
        assert semantic(reader) == source_before
        expected = {'a-intro': 2, 'b-intro': 4} if method == 'append' else {'a-intro': 4, 'b-intro': 2}
        for key, target in expected.items():
            assert out.get_destination_page_number(out.named_destinations[key]) == target
        assert all(row[2] is not None for row in outlines(out))
        assert len(out.pages) == 5
        observations.append({'case': method + ' conflict-retry-and-isolation', 'conflict': conflict, 'state_unchanged': True, 'source_unchanged': True, 'names': semantic(out)['names'], 'outline': outlines(out)})

    # Preserve non-named navigation, and honor exclusion switches.
    for method in ('append', 'merge'):
        for exclusion in ('none', 'annotations', 'outline'):
            pdf = PdfWriter()
            pdf.add_blank_page(50, 50)
            kwargs = {'excluded_fields': ['/Annots']} if exclusion == 'annotations' else {'import_outline': False} if exclusion == 'outline' else {}
            merge(pdf, source(), method, 'x-', pages=[0, 1], **kwargs)
            out = reopen(pdf)
            if exclusion == 'annotations':
                assert not out.pages[1].get('/Annots')
            else:
                nav = links(out, 1)
                assert ('/Dest', ('array', 2)) in nav
                assert ('/URI', 'https://example.org/') in nav
                assert ('/GoToR', 'remote-anchor') in nav
            if exclusion == 'outline':
                assert not out.outline
            observations.append({'case': method + ' compatibility ' + exclusion, 'passed': True})

    # Source is a real serialized PDF whose shared action points via an indirect
    # text string. Reader and default merge resolve the source name correctly.
    for method in ('append', 'merge'):
        reader = source(indirect=True)
        before = semantic(reader)
        legacy = PdfWriter()
        legacy.append(reader, pages=[0, 1])
        default_output = reopen(legacy)
        assert default_output.get_destination_page_number(default_output.outline[0]) == 1
        pdf = PdfWriter()
        pdf.add_blank_page(50, 50)
        merge(pdf, reader, method, 'a-', pages=[0, 1])
        merge(pdf, reader, method, 'b-', pages=[0, 1])
        out = reopen(pdf)
        rows = outlines(out)
        named_actions = [x for x in rows if x[1] == 'Visible title']
        assert [x[4] for x in named_actions] == ['intro', 'intro']
        assert [x[2] for x in named_actions] == [None, None]
        action_links = [x for i in range(len(out.pages)) for x in links(out, i) if x[0] == '/GoTo']
        assert not action_links
        assert semantic(reader) == before
        observations.append({'case': method + ' indirect-D defect', 'source_outline_target': 1, 'source_and_default_resolve': True, 'source_unchanged': True, 'output_names': semantic(out)['names'], 'named_action_links': action_links, 'outline_names': [x[4] for x in named_actions], 'outline_target_pages': [x[2] for x in named_actions]})
    print(json.dumps({'fixture': 'in-memory serialized PDF; same recorded final production code', 'observations': observations}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
