# Gallery of Examples

This gallery of examples shows off how to create a gallery. The directive is:

```markdown
:::{example-gallery} <example-type-name>
:::
```

Subfolders are treated as subsections on this page.

:::{example-gallery} python
:::

You can also explicitly choose which subsections should be shown, and optionally
give them titles. Examples in the top-level folder for this example type can be
shown by the special `self` subsection. The syntax is the same as for `toctree`
directives. If a title is specified, the subsection is listed inside angle brackets,
otherwise the subsection can be listed on its own line. This example shows how
to add a title to a subsection.

```markdown
:::{example-gallery} <example-type-name>

A new title <subfolder>
:::
```

:::{example-gallery} python

A new title <self>
:::

:::{example-gallery} jupyter
:::

:::{example-gallery} cxx
:::
