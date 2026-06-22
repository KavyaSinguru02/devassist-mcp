# DevAssist Any Language / Any Framework Upgrade

Replace these files in your repository:

- `app.py`
- `src/tools/repository_overview.py`
- `src/tools/code_builder.py`
- `src/tools/test_generator.py`
- `src/utils/repository_cache.py`

## What changed

1. Repository Overview now uses the selected language for headings and teaching text.
2. Telugu output no longer shows the default English template.
3. Repository cache now separates cached results by repository URL, audience, language, and diagram option.
4. Build Code now supports any language and any framework using text inputs instead of fixed dropdowns.
5. Generate Tests now supports any test framework. Known frameworks get conventions; unknown frameworks still generate a useful test prompt.

## Important

Because old cached English overviews may exist, either wait for cache expiry or clear rows in `repository_cache` if needed.
