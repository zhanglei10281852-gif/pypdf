# PDF 合并时的命名锚点前缀与副本导航隔离

> **Workspace:** F:\swe\099929\project-01

---

**User**

把几份带章节锚点的 PDF 装订成一本手册时，开发者希望为每份来源保留可预测的独立锚点名，也能把同一份模板放进手册两次而分别跳转到各自的副本。请为 PdfWriter.append 和 PdfWriter.merge 增加可选的 named_destination_prefix 参数，默认 None，None 和空字符串均沿用原行为；传入非空字符串时，将本次所选页面对应的命名目标按“前缀加原名”导入，原名以源 named_destinations 读出的名称为准，不擅自添加分隔符或改写字符，非 ASCII 名称及旧式目录 /Dests 的来源也适用。新增名称应指向本次导入后的页面，保留原目标的 Fit 模式和参数，插入位置和页面选择仍由现有参数决定，未选中目标页的名称不导入。本次导入页面中以 /Dest 或 /A 的 /GoTo 动作引用这些名称的链接，以及导入书签中的命名 /GoTo 动作，都要使用对应的新名称；源中没有定义的命名页面链接、或指向未选中页的命名页面链接应被过滤，不能因为输出文档恰好有同名目标而跳到其他来源。书签的显示标题、层级及目标视图保持原样，import_outline=False 和排除 /Annots 的选项继续生效。同一个 PdfReader 连续以不同前缀导入时，不要求调用方重建 Reader 或手动重置克隆状态，每份副本的命名导航都应留在自己的页面集合；即使页面注释与书签共享同一个动作对象，后一次导入也不能改变前一次副本或源 Reader 中的目标名、链接和书签。若本次将要导入的新名称与输出文档已有命名目标冲突，应抛出 ValueError 并指出冲突名称，不覆盖、不静默跳过，也不自动加后缀；这次失败不能留下新页面、名称或书签，也不能改变已有链接，调用方换用未冲突的前缀后可直接在同一 Writer 上重试并正常写出。上述名称与导航关系在 write 后重新读取仍应成立，显式页面数组目标、URI 和远程跳转等非命名导航维持既有含义；不启用前缀时，包括旧位置参数在内的原合并调用方式和同名处理规则均保持兼容。

**Assistant**

toolName: view_folder

status: success

f:\swe\099929\project-01

toolName: todo_write

status: success

Todos updated: 6 items

toolName: search_by_regex

status: success

toolName: search_by_regex

status: success

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

toolName: search_by_regex

status: success

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\pypdf\_doc_common.py

toolName: search_by_regex

status: success

toolName: search_by_regex

status: success

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\pypdf\_doc_common.py

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

toolName: search_by_regex

status: success

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\pypdf\generic\_data_structures.py

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\pypdf\generic\_data_structures.py

toolName: search_by_regex

status: success

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\pypdf\generic\_base.py

Now let me examine the `Destination` class and `Fit.fit_args`/`dest_array`:

toolName: search_by_regex

status: success

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\pypdf\generic\_data_structures.py

Let me look at the string object classes to understand name equality semantics:

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\pypdf\generic\_base.py

Let me look at `_resolve_links` and how links are fixed at write time, plus the Link helper:

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\pypdf\generic\_link.py

toolName: search_by_regex

status: success

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\tests\test_merger.py

toolName: search_by_regex

status: success

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\tests\test_writer.py

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\tests\test_writer.py

Let me check the reader's `_named_destinations` caching and the writer imports/top section:

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\pypdf\_reader.py

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

toolName: search_by_regex

status: success

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\pypdf\_doc_common.py

Let me check `_add_object` behavior with already-registered clones:

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

toolName: search_by_regex

status: success

toolName: search_by_regex

status: success

toolName: todo_write

status: success

Todos updated: 6 items

Now let me implement. First, update `append`:

toolName: edit_file_search_replace

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

changes: undefined

Now update the `merge` method body:

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

toolName: edit_file_search_replace

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

changes: undefined

Now add the planning/import helpers after `_merge__process_named_dests`:

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

Now add the `_PrefixedNamedDestination` helper class before `PdfWriter`:

toolName: edit_file_search_replace

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

changes: undefined

toolName: search_by_regex

status: success

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

toolName: edit_file_search_replace

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

changes: undefined

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\pypdf\generic\_base.py

Now update `_insert_filtered_annotations`:

toolName: search_by_regex

status: success

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

toolName: edit_file_search_replace

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

changes: undefined

toolName: edit_file_search_replace

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

changes: undefined

toolName: edit_file_search_replace

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

changes: undefined

toolName: edit_file_search_replace

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

changes: undefined

Now update `_clone_outline` and `_insert_filtered_outline`:

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

toolName: edit_file_search_replace

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

changes: undefined

Now let me verify the module imports cleanly and run the existing writer/merger tests:

toolName: Shell

status: success

toolName: Shell

status: success

Let me write an exploratory scratch script to validate the feature end-to-end before formalizing tests:

toolName: Write

status: success

filePath: f:\swe\099929\project-01\scratch_test.py

changes: undefined

toolName: Shell

status: success

toolName: Shell

status: success

toolName: Shell

status: success

toolName: edit_file_search_replace

status: success

filePath: f:\swe\099929\project-01\scratch_test.py

changes: undefined

toolName: Shell

status: success

toolName: edit_file_search_replace

status: success

filePath: f:\swe\099929\project-01\scratch_test.py

changes: undefined

toolName: edit_file_search_replace

status: success

filePath: f:\swe\099929\project-01\scratch_test.py

changes: undefined

toolName: Shell

status: success

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

toolName: edit_file_search_replace

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

changes: undefined

toolName: edit_file_search_replace

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

changes: undefined

toolName: edit_file_search_replace

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

changes: undefined

toolName: Shell

status: success

Core behavior works. Now test conflict/atomicity, page filtering, old-style `/Dests`, and source non-mutation:

toolName: Write

status: success

filePath: f:\swe\099929\project-01\scratch_test2.py

changes: undefined

toolName: Shell

status: success

toolName: edit_file_search_replace

status: success

filePath: f:\swe\099929\project-01\scratch_test2.py

changes: undefined

toolName: Shell

status: success

All scenarios pass. Now run the existing test suites for regressions:

toolName: Shell

status: success

toolName: Shell

status: success

toolName: Shell

status: success

toolName: Shell

status: success

toolName: search_by_regex

status: success

toolName: Shell

status: success

toolName: Shell

status: success

toolName: Shell

status: success

toolName: Shell

status: success

All failures are missing submodule fixtures — environmental. Now let me add formal tests. First check the test file's imports and fixtures:

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\tests\test_merger.py

toolName: search_by_regex

status: success

Now let me view the end of `test_merger.py` and append comprehensive tests:

toolName: Shell

status: success

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\tests\test_merger.py

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\tests\test_merger.py

Now append the formal test suite:

toolName: edit_file_search_replace

status: success

filePath: f:\swe\099929\project-01\tests\test_merger.py

changes: undefined

toolName: edit_file_search_replace

status: success

filePath: f:\swe\099929\project-01\tests\test_merger.py

changes: undefined

toolName: search_by_regex

status: success

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\pypdf\__init__.py

toolName: edit_file_search_replace

status: success

filePath: f:\swe\099929\project-01\tests\test_merger.py

changes: undefined

toolName: Shell

status: success

Three test-expectation bugs (not implementation). Let me fix them:

toolName: edit_file_search_replace

status: success

filePath: f:\swe\099929\project-01\tests\test_merger.py

changes: undefined

toolName: edit_file_search_replace

status: success

filePath: f:\swe\099929\project-01\tests\test_merger.py

changes: undefined

toolName: edit_file_search_replace

status: success

filePath: f:\swe\099929\project-01\tests\test_merger.py

changes: undefined

toolName: Shell

status: success

toolName: edit_file_search_replace

status: success

filePath: f:\swe\099929\project-01\tests\test_merger.py

changes: undefined

toolName: edit_file_search_replace

status: success

filePath: f:\swe\099929\project-01\tests\test_merger.py

changes: undefined

toolName: Shell

status: success

All 9 pass. Now run the full relevant suites again:

toolName: Shell

status: success

Only the 3 pre-existing missing-submodule failures remain. Now check lint/type checks used by this project:

toolName: Shell

status: success

toolName: Shell

status: success

toolName: search_by_regex

status: success

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\pyproject.toml

toolName: search_by_regex

status: success

Let me reduce `merge` complexity by extracting page resolution, and simplify prefix normalization:

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

toolName: edit_file_search_replace

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

changes: undefined

toolName: edit_file_search_replace

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

changes: undefined

toolName: Shell

status: success

toolName: Shell

status: success

toolName: Shell

status: success

toolName: Shell

status: success

toolName: Shell

status: success

toolName: Shell

status: success

Baseline is clean — all 10 are mine. Let me inspect and fix each:

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

toolName: Shell

status: success

toolName: Shell

status: success

The ruff reformat detached a `# type: ignore` from its line. Let me check `PageRangeSpec` and fix all typing issues:

toolName: search_by_regex

status: success

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

Now fix all type issues. First `add_named_destination_object`:

toolName: edit_file_search_replace

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

changes: undefined

toolName: edit_file_search_replace

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

changes: undefined

toolName: edit_file_search_replace

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

changes: undefined

toolName: edit_file_search_replace

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

changes: undefined

toolName: edit_file_search_replace

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

changes: undefined

toolName: edit_file_search_replace

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

changes: undefined

toolName: Shell

status: success

toolName: search_by_regex

status: success

toolName: Shell

status: success

toolName: edit_file_search_replace

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

changes: undefined

toolName: Shell

status: success

toolName: Shell

status: success

mypy clean; only the 3 environmental submodule failures remain. Let me run the broader suite to catch any other regressions:

toolName: Shell

status: success

All failures are missing-submodule environmental issues (871 passed). Let me verify the submodule situation and then review the full diff:

toolName: Shell

status: success

toolName: Shell

status: success

The installed ruff reformatted unrelated lines, creating noise. Let me check the project's pinned ruff version:

toolName: search_by_regex

status: success

toolName: search_by_regex

status: success

The project pins ruff 0.17.3 (newer than the installed 0.15.10) — my global format run used the wrong style. Let me install the pinned version:

toolName: Shell

status: success

toolName: Shell

status: success

toolName: Shell

status: success

HEAD predates ruff 0.17 style too, so I must eliminate unrelated formatting churn. Let me quantify the unrelated hunks:

toolName: Shell

status: success

81 hunks — mostly churn. I'll reconstruct from HEAD and re-apply only logical changes. First save my work and check line-length config:

toolName: Shell

status: success

toolName: search_by_regex

status: success

toolName: Shell

status: success

Now re-apply cleanly. First the helper class:

toolName: edit_file_search_replace

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

changes: undefined

Now the `append` method:

toolName: edit_file_search_replace

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

changes: undefined

Now the `merge` signature and docstring:

toolName: edit_file_search_replace

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

changes: undefined

Now add the new helper methods after `_merge__process_named_dests`:

toolName: search_by_regex

status: success

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

toolName: edit_file_search_replace

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

changes: undefined

Now re-apply the annotation filtering changes:

toolName: search_by_regex

status: success

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

toolName: edit_file_search_replace

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

changes: undefined

Now the outline methods:

toolName: search_by_regex

status: success

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

toolName: edit_file_search_replace

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

changes: undefined

toolName: Shell

status: success

toolName: Shell

status: success

All deletions are intentional. Now restore the test file and validate:

toolName: Shell

status: success

toolName: Shell

status: success

The backup carried unrelated formatting churn. Restore pristine and re-apply only my additions:

toolName: Shell

status: success

toolName: Shell

status: success

toolName: Shell

status: success

toolName: edit_file_search_replace

status: success

filePath: f:\swe\099929\project-01\tests\test_merger.py

changes: undefined

toolName: Shell

status: success

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\tests\test_merger.py

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\tests\test_merger.py

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\tests\test_merger.py

toolName: Shell

status: success

All tests present. Now validate everything:

toolName: Shell

status: success

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\.pre-commit-config.yaml

Only `ruff-check` (not format) is gated. Fix the import ordering:

toolName: edit_file_search_replace

status: success

filePath: f:\swe\099929\project-01\tests\test_merger.py

changes: undefined

toolName: Shell

status: success

toolName: Shell

status: success

toolName: Shell

status: success

toolName: Shell

status: success

Line endings need normalization to LF (repo standard). Let me check HEAD first, then normalize:

toolName: Shell

status: success

toolName: Shell

status: success

Now re-run the complete validation:

toolName: Shell

status: success

Same environmental-only failures. Re-run the scratch scenarios against the reconstructed code:

toolName: Shell

status: success

All scenarios pass. Let me do a final full-diff review:

toolName: Shell

status: success

toolName: view_files

status: success

filePath: C:\Users\czxy4\AppData\Local\Temp\trae-agent-toolhost\jobs\job-67c5a069bef8419ab23d9054a78f28f8\output.log

toolName: Shell

status: success

toolName: view_files

status: success

filePath: C:\Users\czxy4\AppData\Local\Temp\trae-agent-toolhost\jobs\job-5f23386bce1d4cbab1d393933789200b\output.log

toolName: Shell

status: success

toolName: view_files

status: success

filePath: C:\Users\czxy4\AppData\Local\Temp\trae-agent-toolhost\jobs\job-84f9b3bc6e86457790f97366de920107\output.log

The diff is clean and focused. Let me validate a few remaining edge cases (remote GoTo, named `/Dest` outline, partial second import):

toolName: Write

status: success

filePath: f:\swe\099929\project-01\scratch_test3.py

changes: undefined

toolName: Shell

status: success

toolName: edit_file_search_replace

status: success

filePath: f:\swe\099929\project-01\scratch_test3.py

changes: undefined

toolName: Shell

status: success

The second bookmark is correctly filtered (its named target page 1 wasn't selected). Fix the test expectation:

toolName: edit_file_search_replace

status: success

filePath: f:\swe\099929\project-01\scratch_test3.py

changes: undefined

toolName: Shell

status: success

All edge cases pass. Let me strengthen the formal suite with a remote-GoTo case (explicit requirement: remote jumps keep their meaning):

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\tests\test_merger.py

toolName: search_by_regex

status: success

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\tests\test_merger.py

toolName: edit_file_search_replace

status: success

filePath: f:\swe\099929\project-01\tests\test_merger.py

changes: undefined

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\tests\test_merger.py

toolName: edit_file_search_replace

status: success

filePath: f:\swe\099929\project-01\tests\test_merger.py

changes: undefined

toolName: edit_file_search_replace

status: success

filePath: f:\swe\099929\project-01\tests\test_merger.py

changes: undefined

toolName: Shell

status: success

toolName: edit_file_search_replace

status: success

filePath: f:\swe\099929\project-01\tests\test_merger.py

changes: undefined

toolName: Shell

status: success

toolName: Shell

status: success

Everything is green except environmental fixture issues. Let me check whether docs need updating and clean up scratch files:

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\docs\modules\PdfWriter.rst

Docs are autodoc-based — no manual update needed. Clean up scratch files and finalize:

toolName: delete_file

status: success

toolName: todo_write

status: success

Todos updated: 6 items

toolName: Shell

status: success

All 41 merger tests pass; only the two intended files changed. Final review of the complete added test block:

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\tests\test_merger.py

Let me do a final read of the complete `merge` method to confirm coherence:

toolName: view_files

status: success

filePath: f:\swe\099929\project-01\pypdf\_writer.py

The implementation is coherent. Final verification of overall state:

toolName: Shell

status: success

toolName: todo_write

status: success

Todos updated: 6 items

toolName: GetDiagnostics

status: success

完成。已为 [PdfWriter.append](file:///f:/swe/099929/project-01/pypdf/_writer.py#L2715-L2782) 和 [PdfWriter.merge](file:///f:/swe/099929/project-01/pypdf/_writer.py#L2784-L2938) 增加了可选参数 `named_destination_prefix: str | None = None`。

## 实现要点（[pypdf/_writer.py](file:///f:/swe/099929/project-01/pypdf/_writer.py)）

**参数语义**
- `None` 和 `""` 完全走旧路径：旧位置参数调用、重名静默跳过等历史规则一字不动。
- 非空前缀：命名目标按**逐字拼接** `prefix + 原名` 导入（不加分隔符、不改字符），目标指向本次导入的页面，保留原 Fit 模式与参数；插入位置和页面选择仍由现有参数决定，未选中页的名称不导入。

**新增私有组件**
- [_PrefixedNamedDestination](file:///f:/swe/099929/project-01/pypdf/_writer.py#L140-L165)：待导入目标的规划记录。
- [_merge__plan_prefixed_named_dests](file:///f:/swe/099929/project-01/pypdf/_writer.py#L3042-L3138)：在克隆任何页面前完成规划与冲突检测，覆盖 `/Names` 名称树和旧式目录 `/Dests`、非 ASCII 名称，原名一律取自源 `named_destinations`。
- [_merge__clone_prefixed_action](file:///f:/swe/099929/project-01/pypdf/_writer.py#L3156-L3211)：重写命名 `/GoTo`，显式数组、`/URI`、`/GoToR` 维持原含义。

**关键正确性保证**
- **冲突原子性**：冲突时抛 `ValueError` 并指出冲突名称；检测发生在任何 writer 变更之前，不残留页面/名称/书签，也不改已有链接，换前缀可在同一 writer 上直接重试。
- **链接/书签重写与过滤**：页面链接的 `/Dest` 名称、`/A /GoTo /D` 名称及书签命名 GoTo 动作统一按映射改名；源中未定义或指向未选中页的名称被过滤，不会借输出文档里的同名目标跳到其他来源。
- **副本独立性**：对被改写的注释/动作使用 `force_duplicate=True` 克隆，同一 `PdfReader` 连续以不同前缀导入无需 `reset_translation`；即使注释与书签共享同一动作对象，后一次导入也不会改动前一副本或源 Reader。
- 书签标题、层级、视图保持原样；`import_outline=False`、`excluded_fields=("/Annots",)` 继续生效；write 后重新读取验证导航关系成立。

## 测试（[tests/test_merger.py](file:///f:/swe/099929/project-01/tests/test_merger.py)）

新增 9 个用例，覆盖：前缀导入与 Fit 保留、write 后重读、同 Reader 双副本独立（含共享动作）、冲突原子性与重试、未选中/未定义名称过滤、不跨源解析同名目标、`None`/`""` 旧行为与旧位置参数、`import_outline`/`/Annots` 排除项、旧式 `/Dests`（含数字页码目标）、非 ASCII 名称、`/GoToR` 远程跳转原样保留。

验证结果：ruff check 与 mypy 均通过；test_merger 41/41 通过，writer/merger 等相关套件 766 通过。仅有的 3 个失败是本机未初始化 `sample-files` 子模块导致的 `FileNotFoundError`，与本次改动无关。
