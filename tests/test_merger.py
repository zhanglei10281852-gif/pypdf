"""Test merging PDF functionality."""
from io import BytesIO
from pathlib import Path

import pytest

import pypdf
from pypdf import PdfReader, PdfWriter
from pypdf.generic import (
    ArrayObject,
    Destination,
    DictionaryObject,
    Fit,
    NameObject,
    NullObject,
    NumberObject,
    RectangleObject,
    TextStringObject,
)

from . import RESOURCE_ROOT, get_data_from_url
from .test_encryption import HAS_AES


def merger_operate(merger):
    pdf_path = RESOURCE_ROOT / "crazyones.pdf"
    outline = RESOURCE_ROOT / "pdflatex-outline.pdf"
    pdf_forms = RESOURCE_ROOT / "pdflatex-forms.pdf"
    pdf_pw = RESOURCE_ROOT / "libreoffice-writer-password.pdf"

    merger.append(pdf_path)
    merger.append(outline)
    merger.append(pdf_path, pages=pypdf.pagerange.PageRange(slice(0, 0)))
    merger.append(pdf_forms)
    merger.merge(0, pdf_path, import_outline=False)
    with pytest.raises(NotImplementedError) as exc:
        with open(pdf_path, "rb") as fp:
            data = fp.read()
        merger.append(data)
    assert exc.value.args[0].startswith(
        "Merging requires an object that PdfReader can parse. "
        "Typically, that is a Path"
    )

    # Merging an encrypted file
    reader = pypdf.PdfReader(pdf_pw)
    reader.decrypt("openpassword")
    merger.append(reader)

    # PdfReader object:
    r = pypdf.PdfReader(pdf_path)
    merger.append(r, outline_item="foo", pages=list(range(len(r.pages))))

    # File handle
    with open(pdf_path, "rb") as fh:
        merger.append(fh)

    # to force to build outlines and ensure the add_outline_item is
    # at end of the list
    merger.write(BytesIO())
    outline_item = merger.add_outline_item("An outline item", 0)
    oi2 = merger.add_outline_item(
        "deeper", 0, parent=outline_item, italic=True, bold=True
    )
    merger.add_outline_item(
        "Let's see", 2, oi2, (255, 255, 0), True, True, Fit.fit_box_vertically(left=12)
    )
    merger.add_outline_item(
        "The XYZ fit",
        0,
        outline_item,
        (255, 0, 15),
        True,
        True,
        Fit.xyz(left=10, top=20, zoom=3),
    )
    merger.add_outline_item(
        "The FitH fit",
        0,
        outline_item,
        (255, 0, 15),
        True,
        True,
        Fit.fit_horizontally(top=10),
    )
    merger.add_outline_item(
        "The FitV fit",
        0,
        outline_item,
        (255, 0, 15),
        True,
        True,
        Fit.fit_vertically(left=10),
    )
    merger.add_outline_item(
        "The FitR fit",
        0,
        outline_item,
        (255, 0, 15),
        True,
        True,
        Fit.fit_rectangle(left=10, bottom=20, right=30, top=40),
    )
    merger.add_outline_item(
        "The FitB fit", 0, outline_item, (255, 0, 15), True, True, Fit.fit_box()
    )
    merger.add_outline_item(
        "The FitBH fit",
        0,
        outline_item,
        (255, 0, 15),
        True,
        True,
        Fit.fit_box_horizontally(top=10),
    )
    merger.add_outline_item(
        "The FitBV fit",
        0,
        outline_item,
        (255, 0, 15),
        True,
        True,
        Fit.fit_box_vertically(left=10),
    )

    found_oi = merger.find_outline_item("nothing here")
    assert found_oi is None

    found_oi = merger.find_outline_item("foo")
    assert found_oi == [9]

    merger.add_metadata({"/Author": "Martin Thoma"})
    merger.add_named_destination("/Title", 0)
    merger.set_page_layout("/SinglePage")
    merger.page_mode = "/UseThumbs"


def check_outline(tmp_path):
    # Check if outline is correct
    reader = pypdf.PdfReader(tmp_path)
    assert [el.title for el in reader.outline if isinstance(el, Destination)] == [
        "Foo",
        "Bar",
        "Baz",
        "Foo",
        "Bar",
        "Baz",
        "Foo",
        "Bar",
        "Baz",
        "foo",
        "An outline item",  # this has been moved to end normal???
    ]

    # TODO: There seem to be no destinations for those links?


tmp_filename = "dont_commit_merged.pdf"


def test_merger_operations_by_traditional_usage_with_writer(tmp_path):
    # Arrange
    merger = PdfWriter()
    merger_operate(merger)
    path = tmp_path / tmp_filename

    # Act
    merger.write(path)
    merger.close()
    # Assert
    check_outline(path)


def test_merger_operations_by_semi_traditional_usage_with_writer(tmp_path):
    path = tmp_path / tmp_filename

    with PdfWriter() as merger:
        merger_operate(merger)
        merger.write(path)  # Act

    # Assert
    assert Path(path).is_file()
    check_outline(path)


def test_merger_operation_by_new_usage_with_writer(tmp_path):
    path = tmp_path / tmp_filename
    with PdfWriter(fileobj=path) as merger:
        merger_operate(merger)

    # Assert
    assert Path(path).is_file()
    check_outline(path)


def test_merge_page_exception_with_writer():
    merger = pypdf.PdfWriter()
    pdf_path = RESOURCE_ROOT / "crazyones.pdf"
    with pytest.raises(TypeError) as exc:
        merger.merge(0, pdf_path, pages="a:b")
    assert (
        exc.value.args[0]
        == '"pages" must be a tuple of (start, stop[, step]) or a list'
    )
    merger.close()


def test_merge_page_tuple_with_writer():
    merger = pypdf.PdfWriter()
    pdf_path = RESOURCE_ROOT / "crazyones.pdf"
    merger.merge(0, pdf_path, pages=(0, 1))
    merger.close()


def test_merge_write_closed_fh_with_writer(pdf_file_path):
    merger = pypdf.PdfWriter()
    pdf_path = RESOURCE_ROOT / "crazyones.pdf"
    merger.append(pdf_path)

    merger.close()
    merger.write(pdf_file_path)
    merger.add_metadata({"author": "Martin Thoma"})
    merger.set_page_layout("/SinglePage")
    merger.page_mode = "/UseNone"
    merger.add_outline_item("An outline item", 0)


@pytest.mark.enable_socket
def test_trim_outline_list_with_writer(pdf_file_path):
    url = "https://github.com/user-attachments/files/18381771/tika-995175.pdf"
    name = "tika-995175.pdf"
    reader = PdfReader(BytesIO(get_data_from_url(url=url, name=name)))
    merger = PdfWriter()
    merger.append(reader)
    merger.add_outline_item_dict(merger.outline[0])
    merger.write(pdf_file_path)
    merger.close()


@pytest.mark.enable_socket
def test_zoom_with_writer(pdf_file_path):
    url = "https://github.com/user-attachments/files/18381769/tika-994759.pdf"
    name = "tika-994759.pdf"
    reader = PdfReader(BytesIO(get_data_from_url(url=url, name=name)))
    merger = PdfWriter()
    merger.append(reader)
    merger.write(pdf_file_path)
    merger.close()


@pytest.mark.enable_socket
@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_zoom_xyz_no_left_with_add_page(pdf_file_path):
    url = "https://github.com/user-attachments/files/18381704/tika-933322.pdf"
    name = "tika-933322.pdf"
    reader = PdfReader(BytesIO(get_data_from_url(url=url, name=name)))
    merger = PdfWriter()
    for p in reader.pages:
        merger.add_page(p)
    merger.write(pdf_file_path)
    merger.close()


@pytest.mark.enable_socket
def test_zoom_xyz_no_left_with_writer(pdf_file_path):
    url = "https://github.com/user-attachments/files/18381704/tika-933322.pdf"
    name = "tika-933322.pdf"
    reader = PdfReader(BytesIO(get_data_from_url(url=url, name=name)))
    merger = PdfWriter()
    merger.append(reader)
    merger.write(pdf_file_path)
    merger.close()


@pytest.mark.enable_socket
@pytest.mark.slow
def test_outline_item_with_writer(pdf_file_path):
    url = "https://github.com/user-attachments/files/18381773/tika-997511.pdf"
    name = "tika-997511.pdf"
    reader = PdfReader(BytesIO(get_data_from_url(url=url, name=name)))
    merger = PdfWriter()
    merger.append(reader)
    merger.write(pdf_file_path)
    merger.close()


@pytest.mark.enable_socket
@pytest.mark.slow
def test_trim_outline_with_writer(pdf_file_path):
    url = "https://github.com/user-attachments/files/18381759/tika-982336.pdf"
    name = "tika-982336.pdf"
    reader = PdfReader(BytesIO(get_data_from_url(url=url, name=name)))
    merger = PdfWriter()
    merger.append(reader)
    merger.write(pdf_file_path)
    merger.close()


@pytest.mark.enable_socket
@pytest.mark.slow
def test1_with_writer(pdf_file_path):
    url = "https://github.com/user-attachments/files/18381696/tika-923621.pdf"
    name = "tika-923621.pdf"
    reader = PdfReader(BytesIO(get_data_from_url(url=url, name=name)))
    merger = PdfWriter()
    merger.append(reader)
    merger.write(pdf_file_path)
    merger.close()


@pytest.mark.enable_socket
@pytest.mark.slow
def test_sweep_recursion1_with_writer(pdf_file_path):
    # TODO: This test looks like an infinite loop.
    url = "https://github.com/user-attachments/files/18381697/tika-924546.pdf"
    name = "tika-924546.pdf"
    reader = PdfReader(BytesIO(get_data_from_url(url=url, name=name)))
    merger = PdfWriter()
    merger.append(reader)
    merger.write(pdf_file_path)
    merger.close()

    reader2 = PdfReader(pdf_file_path)
    reader2.pages


@pytest.mark.enable_socket
@pytest.mark.slow
@pytest.mark.parametrize(
    ("url", "name"),
    [
        (
            # TODO: This test looks like an infinite loop.
            "https://github.com/user-attachments/files/18381700/tika-924794.pdf",
            "tika-924794.pdf",
        ),
        (
            "https://github.com/user-attachments/files/18381697/tika-924546.pdf",
            "tika-924546.pdf",
        ),
    ],
)
def test_sweep_recursion2_with_writer(url, name, pdf_file_path):
    reader = PdfReader(BytesIO(get_data_from_url(url=url, name=name)))
    merger = PdfWriter()
    merger.append(reader)
    merger.write(pdf_file_path)
    merger.close()

    reader2 = PdfReader(pdf_file_path)
    reader2.pages


@pytest.mark.enable_socket
def test_sweep_indirect_list_newobj_is_none_with_writer(caplog, pdf_file_path):
    url = "https://github.com/user-attachments/files/18381681/tika-906769.pdf"
    name = "tika-906769.pdf"
    reader = PdfReader(BytesIO(get_data_from_url(url=url, name=name)))
    merger = PdfWriter()
    merger.append(reader)
    merger.write(pdf_file_path)
    merger.close()
    # used to be: assert "Object 21 0 not defined." in caplog.text

    reader2 = PdfReader(pdf_file_path)
    reader2.pages


@pytest.mark.enable_socket
def test_iss1145_with_writer():
    # issue with FitH destination with null param
    url = "https://github.com/py-pdf/pypdf/files/9164743/file-0.pdf"
    name = "iss1145.pdf"
    merger = PdfWriter()
    merger.append(PdfReader(BytesIO(get_data_from_url(url=url, name=name))))
    merger.close()


@pytest.mark.enable_socket
def test_iss1344_with_writer(caplog):
    url = "https://github.com/py-pdf/pypdf/files/9549001/input.pdf"
    name = "iss1344.pdf"
    m = PdfWriter()
    m.append(PdfReader(BytesIO(get_data_from_url(url=url, name=name))))
    b = BytesIO()
    m.write(b)
    p = PdfReader(b).pages[0]
    assert "/DIJMAC+Arial Black" in p._debug_for_extract()
    assert "adresse où le malade peut être visité" in p.extract_text()


@pytest.mark.enable_socket
def test_articles_with_writer(caplog):
    url = "https://github.com/user-attachments/files/18381699/tika-924666.pdf"
    name = "924666.pdf"
    m = PdfWriter()
    m.append(PdfReader(BytesIO(get_data_from_url(url=url, name=name))), (2, 10))
    b = BytesIO()
    m.write(b)
    r = PdfReader(b)
    assert len(r.threads) == 4
    assert r.threads[0].get_object()["/F"]["/P"] == r.pages[0]


@pytest.mark.skipif(not HAS_AES, reason="No AES implementation")
@pytest.mark.enable_socket
def test_null_articles_with_writer():
    data = get_data_from_url(name="issue-3508.pdf")
    merger = PdfWriter()
    merger.append(BytesIO(data))
    assert len(merger.pages) == 98


def test_get_reference():
    writer = PdfWriter(RESOURCE_ROOT / "crazyones.pdf")
    assert writer.get_reference(writer.pages[0]) == writer.pages[0].indirect_reference


@pytest.mark.enable_socket
def test_direct_link_preserved(pdf_file_path):
    # this could be any PDF -- we don't care which
    reader = PdfReader(BytesIO(get_data_from_url(name="iss3268.pdf")))
    writer = PdfWriter(clone_from=reader)

    # this PDF has a direct link from p1 to p2
    merger = PdfReader(BytesIO(get_data_from_url(name="direct-link.pdf")))
    for p in merger.pages:
        writer.add_page(p)

    writer.write(pdf_file_path)

    check = PdfReader(pdf_file_path)
    page3 = check.pages[2]
    link = page3["/Annots"][0].get_object()
    assert link["/Subtype"] == "/Link"
    dest = link["/Dest"][0]  # indirect reference of page referred to

    page4 = check.flattened_pages[3]
    assert dest == page4.indirect_reference, "Link from page 3 to page 4 is broken"


@pytest.mark.enable_socket
def test_direct_link_preserved_reordering(pdf_file_path):
    # this could be any PDF -- we don't care which
    reader = PdfReader(BytesIO(get_data_from_url(name="iss3268.pdf")))
    writer = PdfWriter(clone_from=reader)

    # this PDF has a direct link from p1 to p2
    merger = PdfReader(BytesIO(get_data_from_url(name="direct-link.pdf")))
    for p in merger.pages:
        writer.add_page(p)

    # let's insert a page to mess up the page order
    writer.insert_page(reader.pages[0], 3)

    writer.write(pdf_file_path)

    check = PdfReader(pdf_file_path)
    page3 = check.pages[2]
    link = page3["/Annots"][0].get_object()
    assert link["/Subtype"] == "/Link"
    dest = link["/Dest"][0]  # indirect reference of page referred to

    page5 = check.flattened_pages[4]  # it moved one out
    assert dest == page5.indirect_reference, "Link from page 3 to page 5 is broken"


@pytest.mark.enable_socket
def test_direct_link_page_missing(pdf_file_path):
    # this could be any PDF -- we don't care which
    reader = PdfReader(BytesIO(get_data_from_url(name="iss3268.pdf")))
    writer = PdfWriter(clone_from=reader)

    # this PDF has a direct link from p1 to p2
    merger = PdfReader(BytesIO(get_data_from_url(name="direct-link.pdf")))
    writer.add_page(merger.pages[0])
    # but we're not adding page 2

    writer.write(pdf_file_path)  # verify nothing crashes


@pytest.mark.enable_socket
def test_named_reference_preserved(pdf_file_path):
    # this could be any PDF -- we don't care which
    reader = PdfReader(BytesIO(get_data_from_url(name="iss3268.pdf")))
    writer = PdfWriter(clone_from=reader)

    # this PDF has a named reference from from p3 to p5
    merger = PdfReader(BytesIO(get_data_from_url(name="named-reference.pdf")))
    for p in merger.pages:
        writer.add_page(p)

    writer.write(pdf_file_path)

    check = PdfReader(pdf_file_path)
    page5 = check.pages[4]
    page7 = check.flattened_pages[6]
    for link in page5["/Annots"]:
        action = link["/A"]
        assert action.get("/S") == "/GoTo"
        dest = str(action["/D"])
        assert dest in check.named_destinations
        pref = check.named_destinations[dest].page

        assert pref == page7.indirect_reference, "Link from page 5 to page 7 is broken"


@pytest.mark.enable_socket
def test_named_ref_to_page_that_is_gone(pdf_file_path):
    source = PdfReader(BytesIO(get_data_from_url(name="named-reference.pdf")))
    buf = BytesIO()
    tmp = PdfWriter()
    tmp.add_page(source.pages[2])  # we add only the page with the reference
    tmp.write(buf)

    source = PdfReader(buf)

    writer = PdfWriter()
    writer.add_page(source.pages[0])  # now references to non-existent page
    writer.write(pdf_file_path)  # don't crash


def test_merge__null_destination():
    """Tests for issue #3444."""
    writer = PdfWriter(clone_from=RESOURCE_ROOT / "crazyones.pdf")
    writer2 = PdfWriter(clone_from=RESOURCE_ROOT / "crazyones.pdf")

    annotation = DictionaryObject()
    annotation[NameObject("/Subtype")] = NameObject("/Link")
    a = DictionaryObject()
    annotation[NameObject("/A")] = a
    a[NameObject("/S")] = NameObject("/GoTo")

    target = NullObject()
    a[NameObject("/D")] = writer._add_object(target)

    annots = ArrayObject([annotation])
    page = writer2.pages[0]
    page[NameObject("/Annots")] = annots

    data = BytesIO()
    writer2.write(data)
    data.seek(0)

    writer.merge(position=1, fileobj=data)
    assert writer.pages[0].annotations is None


def test_merge_annotation_without_subtype():
    """Regression test for #3356."""
    src = PdfWriter()
    src.add_blank_page(width=612, height=792)
    annot = DictionaryObject()
    src.pages[0][NameObject("/Annots")] = ArrayObject([src._add_object(annot)])

    source = BytesIO()
    src.write(source)
    source.seek(0)

    writer = PdfWriter()
    writer.append(PdfReader(source), import_outline=False)

    merged = BytesIO()
    writer.write(merged)
    merged.seek(0)

    reread = PdfReader(merged)
    merged_annot = reread.pages[0]["/Annots"][0].get_object()
    assert "/Subtype" not in merged_annot


@pytest.mark.enable_socket
def test_append_page_with_non_terminal_fields():
    """
    This test is a regression test for issue #3736.
    Appending a single page must not pull in the other pages through fields
    sharing a non-terminal parent field.
    """
    reader = PdfReader(BytesIO(get_data_from_url(name="issue-3736.pdf")))
    writer = PdfWriter()
    writer.append(reader, pages=[0])

    output = BytesIO()
    writer.write(output)
    output.seek(0)

    # Only the appended page and its page tree may be written.
    page_types = [
        obj.get("/Type")
        for obj in writer._objects
        if isinstance(obj, DictionaryObject)
    ]
    assert page_types.count("/Page") == 1
    assert page_types.count("/Pages") == 1

    result = PdfReader(output)
    assert len(result.pages) == 1
    assert list(result.get_fields()) == [
        "common", "common.Text1", "common.Text2", "common.Button1"
    ]
    page_reference = result.pages[0].indirect_reference
    for annotation in result.pages[0]["/Annots"]:
        assert annotation.get_object().raw_get("/P") == page_reference

    # Appending the whole document keeps all fields in their original order.
    writer = PdfWriter()
    writer.append(reader)
    assert list(writer.get_fields()) == list(reader.get_fields())


def test_merge_widget_with_non_dictionary_parent():
    """
    A ``/Widget`` whose ``/Parent`` does not resolve to a dictionary must not
    abort the merge. The malformed reference is dropped and the widget itself
    is still carried over.
    """
    input_writer = PdfWriter()
    input_writer.add_blank_page(width=612, height=792)
    annotation = DictionaryObject()
    annotation[NameObject("/Subtype")] = NameObject("/Widget")
    # An indirect reference to something that is not a dictionary.
    annotation[NameObject("/Parent")] = input_writer._add_object(NullObject())
    input_writer.pages[0][NameObject("/Annots")] = ArrayObject([input_writer._add_object(annotation)])

    input_pdf = BytesIO()
    input_writer.write(input_pdf)
    input_pdf.seek(0)

    writer = PdfWriter()
    writer.append(PdfReader(input_pdf), import_outline=False)

    merged = BytesIO()
    writer.write(merged)
    merged.seek(0)

    reader = PdfReader(merged)
    assert len(reader.pages) == 1
    merged_annotation = reader.pages[0]["/Annots"][0].get_object()
    assert merged_annotation["/Subtype"] == "/Widget"
    assert "/Parent" not in merged_annotation


def test_merge_widget_with_cyclic_parent_chain():
    """
    A ``/Parent`` chain that loops back on itself must not hang the merge.
    Every field in the loop is cloned once and keeps its ``/Parent`` and ``/Kids``.
    """
    input_writer = PdfWriter()
    input_writer.add_blank_page(width=612, height=792)
    first_field = DictionaryObject({NameObject("/T"): TextStringObject("first")})
    second_field = DictionaryObject({NameObject("/T"): TextStringObject("second")})
    first_reference = input_writer._add_object(first_field)
    second_reference = input_writer._add_object(second_field)
    widget = DictionaryObject({
        NameObject("/Subtype"): NameObject("/Widget"),
        NameObject("/Parent"): first_reference,
    })
    widget_reference = input_writer._add_object(widget)
    first_field[NameObject("/Parent")] = second_reference
    first_field[NameObject("/Kids")] = ArrayObject([widget_reference])
    second_field[NameObject("/Parent")] = first_reference
    second_field[NameObject("/Kids")] = ArrayObject([first_reference])
    input_writer.pages[0][NameObject("/Annots")] = ArrayObject([widget_reference])

    input_pdf = BytesIO()
    input_writer.write(input_pdf)
    input_pdf.seek(0)

    writer = PdfWriter()
    writer.append(PdfReader(input_pdf), import_outline=False)

    merged_widget = writer.pages[0]["/Annots"][0].get_object()
    merged_first = merged_widget["/Parent"].get_object()
    merged_second = merged_first["/Parent"].get_object()
    assert merged_first["/T"] == "first"
    assert merged_second["/T"] == "second"
    assert merged_second.raw_get("/Parent") == merged_widget.raw_get("/Parent")
    assert merged_first["/Kids"] == [merged_widget.indirect_reference]
    assert merged_second["/Kids"] == [merged_widget.raw_get("/Parent")]
    fields = [obj for obj in writer._objects if isinstance(obj, DictionaryObject) and "/T" in obj]
    assert len(fields) == 2
def _link_annotation(source: PdfWriter, entries: dict[str, object]) -> DictionaryObject:
    annotation = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Annot"),
            NameObject("/Subtype"): NameObject("/Link"),
            NameObject("/Rect"): RectangleObject([0, 0, 10, 10]),
        }
    )
    for key, value in entries.items():
        annotation[NameObject(key)] = value
    return source._add_object(annotation)


def _build_named_destination_source() -> BytesIO:
    """
    Build a 3-page source exercising named destinations and named navigation.

    It contains:

    * four named destinations (including a non-ASCII name and a destination on
      an unselected page);
    * link annotations using a named ``/A`` GoTo action, a named ``/Dest``,
      an undefined name, a URI action and an explicit array destination;
    * an outline whose first item shares its named GoTo action with a link
      annotation and whose second item uses an explicit array destination.
    """
    source = PdfWriter()
    for _ in range(3):
        source.add_blank_page(width=200, height=200)
    source.add_named_destination("chap1", 0, fit=Fit.xyz(left=10, top=20, zoom=2))
    source.add_named_destination("chap2", 1, fit=Fit.fit_horizontally(top=199))
    source.add_named_destination("skip", 2, fit=Fit.fit())
    source.add_named_destination("anchör", 0, fit=Fit.fit())

    shared_action = source._add_object(
        DictionaryObject(
            {
                NameObject("/S"): NameObject("/GoTo"),
                NameObject("/D"): TextStringObject("chap1"),
            }
        )
    )

    source.pages[0][NameObject("/Annots")] = ArrayObject(
        [
            _link_annotation(source, {"/A": shared_action}),
            _link_annotation(source, {"/Dest": TextStringObject("chap2")}),
            _link_annotation(
                source,
                {
                    "/A": DictionaryObject(
                        {
                            NameObject("/S"): NameObject("/GoTo"),
                            NameObject("/D"): TextStringObject("missing"),
                        }
                    )
                },
            ),
            _link_annotation(
                source,
                {
                    "/A": DictionaryObject(
                        {
                            NameObject("/S"): NameObject("/URI"),
                            NameObject("/URI"): NameObject("/https://example.com"),
                        }
                    )
                },
            ),
            _link_annotation(
                source,
                {
                    # Remote GoTo actions are not named navigation and must be
                    # imported verbatim.
                    "/A": DictionaryObject(
                        {
                            NameObject("/S"): NameObject("/GoToR"),
                            NameObject("/F"): NameObject("/other-document.pdf"),
                            NameObject("/D"): TextStringObject("remote-name"),
                        }
                    )
                },
            ),
            _link_annotation(source, {"/Dest": TextStringObject("skip")}),
            _link_annotation(
                source,
                {"/Dest": ArrayObject([source.pages[2].indirect_reference, NameObject("/Fit")])},
            ),
        ]
    )

    chapter1 = source.add_outline_item("Chapter 1", 0, fit=Fit.fit())
    chapter1.get_object()[NameObject("/A")] = shared_action
    chapter2 = source.add_outline_item("Chapter 2", 1, fit=Fit.fit_horizontally(top=199))
    source.add_outline_item("Child of 2", 1, parent=chapter2)

    buffer = BytesIO()
    source.write(buffer)
    buffer.seek(0)
    return buffer


def _annotation_navigation(page: pypdf.PageObject) -> list[tuple[str, str | None]]:
    navigation: list[tuple[str, str | None]] = []
    for reference in page.get("/Annots", []) or []:
        annotation = reference.get_object()
        if "/A" in annotation:
            action = annotation["/A"].get_object()
            if "/D" in action and isinstance(action["/D"], str):
                navigation.append((str(action["/S"]), str(action["/D"])))
            elif "/D" in action:
                navigation.append((str(action["/S"]), "array"))
            else:
                navigation.append((str(action["/S"]), None))
        elif "/Dest" in annotation:
            destination = annotation["/Dest"]
            navigation.append(("/Dest", str(destination) if isinstance(destination, str) else "array"))
    return navigation


def _flatten_outline_titles(items: list[Destination]) -> list[str]:
    titles: list[str] = []
    for item in items:
        if isinstance(item, list):
            titles.extend(_flatten_outline_titles(item))
        else:
            titles.append(item.title)
    return titles


def test_named_destination_prefix_imports_destinations_and_rewrites_navigation():
    reader = PdfReader(_build_named_destination_source())
    writer = PdfWriter()
    writer.append(reader, named_destination_prefix="a-")

    # The names are the verbatim "prefix + source name", including non-ASCII.
    assert set(writer.named_destinations) == {
        "a-chap1",
        "a-chap2",
        "a-skip",
        "a-anchör",
    }

    # The fit mode and its parameters are preserved and pages are retargeted.
    chap1 = writer.named_destinations["a-chap1"]
    assert chap1.typ == "/XYZ"
    assert (chap1.left, chap1.top, chap1.zoom) == (10, 20, 2)
    assert chap1.page == writer.pages[0].indirect_reference
    chap2 = writer.named_destinations["a-chap2"]
    assert chap2.typ == "/FitH"
    assert chap2.top == 199
    assert chap2.page == writer.pages[1].indirect_reference
    assert writer.named_destinations["a-skip"].page == writer.pages[2].indirect_reference

    # Named links are renamed; the undefined name is filtered; URI, remote GoTo
    # and explicit array navigation are kept with their original meaning.
    assert _annotation_navigation(writer.pages[0]) == [
        ("/GoTo", "a-chap1"),
        ("/Dest", "a-chap2"),
        ("/URI", None),
        ("/GoToR", "remote-name"),
        ("/Dest", "a-skip"),
        ("/Dest", "array"),
    ]
    remote_action = next(
        annotation.get_object()["/A"].get_object()
        for annotation in writer.pages[0]["/Annots"]
        if isinstance(annotation.get_object().get("/A"), DictionaryObject)
        and annotation.get_object()["/A"].get_object().get("/S") == "/GoToR"
    )
    assert str(remote_action["/F"]) == "/other-document.pdf"
    assert str(remote_action["/D"]) == "remote-name"

    output = BytesIO()
    writer.write(output)
    output.seek(0)
    reread = PdfReader(output)

    assert set(reread.named_destinations) == {
        "a-chap1",
        "a-chap2",
        "a-skip",
        "a-anchör",
    }
    assert _annotation_navigation(reread.pages[0]) == [
        ("/GoTo", "a-chap1"),
        ("/Dest", "a-chap2"),
        ("/URI", None),
        ("/GoToR", "remote-name"),
        ("/Dest", "a-skip"),
        ("/Dest", "array"),
    ]
    explicit_link = next(
        annotation
        for annotation in reread.pages[0]["/Annots"]
        if isinstance(annotation.get_object().get("/Dest"), ArrayObject)
    )
    assert explicit_link.get_object()["/Dest"][0] == reread.pages[2].indirect_reference

    # Outline titles, hierarchy and target views are preserved; named actions
    # use the prefixed name.
    assert _flatten_outline_titles(reread.outline) == [
        "Chapter 1",
        "Chapter 2",
        "Child of 2",
    ]
    chapter1_action = reread.outline[0].node["/A"].get_object()
    assert chapter1_action["/S"] == "/GoTo"
    assert str(chapter1_action["/D"]) == "a-chap1"
    chapter2_action = reread.outline[1].node["/A"].get_object()
    assert chapter2_action["/D"][0] == reread.pages[1].indirect_reference
    assert chapter2_action["/D"][1] == "/FitH"
    assert chapter2_action["/D"][2] == 199


def test_named_destination_prefix_two_copies_of_same_reader_are_independent():
    reader = PdfReader(_build_named_destination_source())
    writer = PdfWriter()
    writer.append(reader, named_destination_prefix="a-")
    writer.append(reader, named_destination_prefix="b-")

    # Each copy keeps the navigation within its own page set.
    first_action = writer.pages[0]["/Annots"][0].get_object()["/A"].get_object()
    second_action = writer.pages[3]["/Annots"][0].get_object()["/A"].get_object()
    assert first_action is not second_action
    assert str(first_action["/D"]) == "a-chap1"
    assert str(second_action["/D"]) == "b-chap1"

    first_explicit = next(
        annotation
        for annotation in writer.pages[0]["/Annots"]
        if isinstance(annotation.get_object().get("/Dest"), ArrayObject)
    ).get_object()
    second_explicit = next(
        annotation
        for annotation in writer.pages[3]["/Annots"]
        if isinstance(annotation.get_object().get("/Dest"), ArrayObject)
    ).get_object()
    assert first_explicit["/Dest"][0] == writer.pages[2].indirect_reference
    assert second_explicit["/Dest"][0] == writer.pages[5].indirect_reference

    # The source reader is not modified by either import.
    assert set(reader.named_destinations) == {"chap1", "chap2", "skip", "anchör"}
    source_action = reader.pages[0]["/Annots"][0].get_object()["/A"].get_object()
    assert str(source_action["/D"]) == "chap1"

    output = BytesIO()
    writer.write(output)
    output.seek(0)
    reread = PdfReader(output)

    assert len(reread.pages) == 6
    for name, page_index in (
        ("a-chap1", 0),
        ("a-chap2", 1),
        ("a-skip", 2),
        ("b-chap1", 3),
        ("b-chap2", 4),
        ("b-skip", 5),
    ):
        assert reread.named_destinations[name].page == reread.pages[page_index].indirect_reference
    assert _annotation_navigation(reread.pages[0])[0] == ("/GoTo", "a-chap1")
    assert _annotation_navigation(reread.pages[3])[0] == ("/GoTo", "b-chap1")
    top_level = [item for item in reread.outline if not isinstance(item, list)]
    assert [item.title for item in top_level] == [
        "Chapter 1",
        "Chapter 2",
        "Chapter 1",
        "Chapter 2",
    ]
    assert str(top_level[0].node["/A"].get_object()["/D"]) == "a-chap1"
    assert str(top_level[2].node["/A"].get_object()["/D"]) == "b-chap1"


def test_named_destination_prefix_conflict_raises_and_leaves_writer_untouched():
    buffer = _build_named_destination_source()

    # The output already owns a name that the prefixed import would create.
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.add_named_destination("a-chap1", 0)
    names_root_before = list(writer.get_named_dest_root())

    with pytest.raises(ValueError, match="a-chap1"):
        writer.append(PdfReader(BytesIO(buffer.getvalue())), named_destination_prefix="a-")
    # No page, name or bookmark leaked and the name tree is unchanged.
    assert len(writer.pages) == 1
    assert set(writer.named_destinations) == {"a-chap1"}
    assert len(writer.outline) == 0
    assert list(writer.get_named_dest_root()) == names_root_before

    # A non-conflicting prefix can be used on the same writer.
    writer.append(PdfReader(BytesIO(buffer.getvalue())), named_destination_prefix="b-")
    pages_before = len(writer.pages)
    names_before = set(writer.named_destinations)
    with pytest.raises(ValueError, match="b-"):
        writer.append(PdfReader(BytesIO(buffer.getvalue())), named_destination_prefix="b-")
    # Again, nothing leaked and existing links are unchanged.
    assert len(writer.pages) == pages_before
    assert set(writer.named_destinations) == names_before
    assert str(writer.pages[1]["/Annots"][0].get_object()["/A"].get_object()["/D"]) == "b-chap1"

    # Retrying with yet another prefix works and the document can be written.
    writer.append(PdfReader(BytesIO(buffer.getvalue())), named_destination_prefix="c-")
    output = BytesIO()
    writer.write(output)
    output.seek(0)
    reread = PdfReader(output)
    assert len(reread.pages) == 7
    assert "c-chap1" in reread.named_destinations


def test_named_destination_prefix_filters_unselected_and_undefined_references():
    reader = PdfReader(_build_named_destination_source())
    writer = PdfWriter()
    writer.append(reader, pages=[0], named_destination_prefix="p-")

    # Only destinations of the selected page are imported.
    assert set(writer.named_destinations) == {"p-chap1", "p-anchör"}

    # Links to chap2/skip (unselected pages) and "missing" (undefined) are gone.
    assert _annotation_navigation(writer.pages[0]) == [
        ("/GoTo", "p-chap1"),
        ("/URI", None),
        ("/GoToR", "remote-name"),
    ]

    # The outline item targeting an unselected page is filtered as well.
    assert _flatten_outline_titles(writer.outline) == ["Chapter 1"]
    assert str(writer.outline[0].node["/A"].get_object()["/D"]) == "p-chap1"


def test_named_destination_prefix_does_not_resolve_against_other_sources():
    target = PdfWriter()
    target.add_blank_page(width=200, height=200)
    target.add_named_destination("shared", 0)
    target_buffer = BytesIO()
    target.write(target_buffer)
    target_buffer.seek(0)

    link_source = PdfWriter()
    link_source.add_blank_page(width=200, height=200)
    link_source.pages[0][NameObject("/Annots")] = ArrayObject(
        [_link_annotation(link_source, {"/Dest": TextStringObject("shared")})]
    )
    link_buffer = BytesIO()
    link_source.write(link_buffer)
    link_buffer.seek(0)

    # Legacy behavior: the link is kept and resolves against the output target.
    legacy = PdfWriter()
    legacy.append(PdfReader(BytesIO(target_buffer.getvalue())))
    legacy.append(PdfReader(BytesIO(link_buffer.getvalue())))
    assert _annotation_navigation(legacy.pages[1]) == [("/Dest", "shared")]

    # Prefixed behavior: the source does not define the name, so the link is
    # filtered instead of jumping to the other source's same-named target.
    prefixed = PdfWriter()
    prefixed.append(
        PdfReader(BytesIO(target_buffer.getvalue())),
        named_destination_prefix="t-",
    )
    prefixed.append(
        PdfReader(BytesIO(link_buffer.getvalue())),
        named_destination_prefix="l-",
    )
    assert "t-shared" in prefixed.named_destinations
    assert len(prefixed.pages[1].get("/Annots", [])) == 0


@pytest.mark.parametrize("prefix", [None, ""])
def test_named_destination_prefix_none_and_empty_keep_legacy_behavior(prefix):
    buffer = _build_named_destination_source()
    writer = PdfWriter()
    writer.append(PdfReader(BytesIO(buffer.getvalue())), named_destination_prefix=prefix)
    writer.append(PdfReader(BytesIO(buffer.getvalue())), named_destination_prefix=prefix)

    # Duplicate names are silently skipped, as historically.
    assert set(writer.named_destinations) == {"chap1", "chap2", "skip", "anchör"}
    assert len(writer.pages) == 6
    assert _annotation_navigation(writer.pages[0])[0] == ("/GoTo", "chap1")

    # Legacy positional call form stays valid.
    positional = PdfWriter()
    positional.add_blank_page(width=100, height=100)
    positional.merge(0, PdfReader(BytesIO(buffer.getvalue())), None, [0, 1], True, ())
    assert len(positional.pages) == 3
    assert "chap1" in positional.named_destinations


def test_named_destination_prefix_respects_import_outline_and_annotation_exclusions():
    reader = PdfReader(_build_named_destination_source())

    without_annotations = PdfWriter()
    without_annotations.append(reader, named_destination_prefix="x-", excluded_fields=("/Annots",))
    assert "x-chap1" in without_annotations.named_destinations
    assert without_annotations.pages[0].get("/Annots") is None

    without_outline = PdfWriter()
    without_outline.append(reader, named_destination_prefix="x-", import_outline=False)
    assert "x-chap1" in without_outline.named_destinations
    assert len(without_outline.outline) == 0
    assert _annotation_navigation(without_outline.pages[0])[0] == (
        "/GoTo",
        "x-chap1",
    )


def test_named_destination_prefix_supports_legacy_catalog_dests():
    source = PdfWriter()
    source.add_blank_page(width=200, height=200)
    source.add_blank_page(width=200, height=200)
    source.root_object[NameObject("/Dests")] = DictionaryObject(
        {
            # Name token key, indirect page reference.
            NameObject("/old"): ArrayObject([source.pages[1].indirect_reference, NameObject("/Fit")]),
            # Destination addressing the page by number.
            NameObject("/num"): ArrayObject([NumberObject(0), NameObject("/Fit")]),
        }
    )
    source.pages[0][NameObject("/Annots")] = ArrayObject(
        [
            source._add_object(
                DictionaryObject(
                    {
                        NameObject("/Type"): NameObject("/Annot"),
                        NameObject("/Subtype"): NameObject("/Link"),
                        NameObject("/Rect"): RectangleObject([0, 0, 10, 10]),
                        NameObject("/Dest"): NameObject("/old"),
                    }
                )
            )
        ]
    )
    buffer = BytesIO()
    source.write(buffer)
    buffer.seek(0)
    reader = PdfReader(buffer)
    assert set(reader.named_destinations) == {"/old", "/num"}

    writer = PdfWriter()
    writer.append(reader, named_destination_prefix="z-")

    assert set(writer.named_destinations) == {"z-/old", "z-/num"}
    assert writer.named_destinations["z-/old"].page == writer.pages[1].indirect_reference
    assert int(writer.named_destinations["z-/num"].page) == 0
    renamed_link = writer.pages[0]["/Annots"][0].get_object()
    assert isinstance(renamed_link["/Dest"], TextStringObject)
    assert str(renamed_link["/Dest"]) == "z-/old"

    output = BytesIO()
    writer.write(output)
    output.seek(0)
    reread = PdfReader(output)
    assert set(reread.named_destinations) == {"z-/old", "z-/num"}
    assert str(reread.pages[0]["/Annots"][0].get_object()["/Dest"]) == "z-/old"
    assert reread.named_destinations["z-/old"].page == reread.pages[1].indirect_reference


