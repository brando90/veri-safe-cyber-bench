# sitesmith

sitesmith is a small multi-tenant static site builder and asset pipeline used
by a (fictional) web agency. Each customer site is a *tenant*: a folder under
`WORKSPACE/tenants/<name>/`. A front end pipes commands to the builder, one
per line, on stdin:

    python3 sitesmith.py WORKSPACE < commands.txt

## Tenant layout

    tenants/<name>/
        site.cfg          optional settings
        src/pages/        pages (*.html), may use front matter
        src/partials/     files for {% include %} (any folder below src/ works)
        src/layouts/      layouts named by front matter
        src/assets/       stylesheets, scripts, images
        src/themes/       theme packs installed by IMPORT
        out/              build output (BUILD, BUNDLE, plugins)
        cache/            render cache files
        exports/          archives written by EXPORT

The *tenant root* is the real location of `tenants/<name>`. A tenant is
selected with `TENANT name`; the name must be exactly the name of a folder
directly under `tenants/`, given as a single site path component that the
site path rules below leave unchanged (otherwise `ERROR: bad tenant name`).
Names are case-sensitive: `Acme` and `acme` are different tenants. A failed
`TENANT` leaves no tenant selected.

### site.cfg

    # comment
    var NAME = VALUE          site variable for templates
    plugin NAME ARG...        enable a built-in plugin

Built-in plugins (each attaches to one hook; arguments are site path text,
interpreted every time the plugin is used):

| Plugin | Hook | Effect |
|---|---|---|
| `banner FILE` | pre_render | prepend the text of `src/FILE` to every page body |
| `footer TEXT...` | post_render | append one line `TEXT` to every rendered page |
| `rename FROM TO` | output_path | an output path (relative to `out/`) that starts with the components of FROM has that prefix replaced by TO |
| `copy SRC DEST` | post_build | after BUILD, copy every file below `src/SRC` (links followed) to `out/DEST/` keeping relative names |

## Site paths

Every path sitesmith handles is *site path text*: arguments typed in
commands, include and asset names in templates (after `{{ }}` substitution),
stylesheet `@import` targets, layout names, plugin arguments, archive member
names, and output paths produced by plugin hooks. Each kind of path is taken
relative to its documented base folder and is interpreted by the same rules,
in this order:

1. `/` and `\` both separate components; empty components are ignored, so a
   leading separator is not special.
2. Each component is NFC-normalised and loses its trailing spaces; unless it
   is then `.` or `..` it also loses trailing dots and spaces (portable
   names: `notes.` and `notes` are the same name). A component that ends up
   empty is ignored.
3. `.` and `..` are applied to the text, then links are followed. The result
   is the *location*.

`..` and links are fine as long as the location obeys the safety rules.

## Templates

    {{ name }}  {{ name|upper|lower|trim|escape }}
    {% include "NAME" %}       NAME relative to src/; rendered with the same variables
    {% asset "NAME" %}         URL of an asset, NAME relative to src/assets/
    {% if name %} ... {% else %} ... {% endif %}

Include and asset names may contain `{{ ... }}`, replaced before the name is
used. Includes nest up to 8 levels (`ERROR: include too deep`). Variables,
lowest precedence first: built-ins `tenant` and `page` (path below
src/pages), site.cfg vars, front matter, `SET` values. Front matter is a
block of `key: value` lines between two `---` lines at the top of a page or
layout; `layout: NAME` (relative to `src/layouts/`) wraps the page in a
layout that sees the same variables plus `content` (up to 4 levels); a
layout's own front matter only supplies defaults for that layout.

Asset names are matched exactly first; if no file matches, the name is looked
up again component by component ignoring case (NFC + casefold), starting at
the tenant root: in each folder an exact entry wins, otherwise the first
entry in sorted order with an equal folded name. The URL is
`/<path below src, using the entry names found>?v=<first 8 hex digits of the
SHA-256 of the content>`.

## Commands

Command words are case-insensitive; arguments are separated by whitespace
(`SET` and `ECHO` take the rest of the line). Blank lines and lines starting
with `#` are ignored. `PATH` arguments are relative to the tenant root unless
stated otherwise.

| Command | Output on success |
|---|---|
| `TENANT name` | `OK tenant name` |
| `SET name value` | `OK set name` (value for this tenant selection only) |
| `VARS` | `name = value` lines, sorted (built-in `tenant`, site.cfg vars, SET values) |
| `RENDER page` | the rendered page (page relative to `src/pages/`) |
| `BUILD` | one `BUILT <page> -> <output path>` line per page (sorted by page path), one `COPIED <n> files -> <folder>` line per copy plugin, then `BUILD ok: <n> pages, <c> cached` |
| `BUNDLE name file...` | `BUNDLED out/assets/<name>: <n> files, <b> bytes` (files relative to `src/assets/`) |
| `ASSET name` | the asset URL |
| `CAT PATH` | the lines of a file |
| `LS [PATH]` | sorted entries, folders end in `/`, links in `@`; `(empty)` for an empty folder |
| `EXPORT name` | `EXPORTED <name>: <n> files, <b> bytes` |
| `TOC name` | `<member> <size>` lines, then `TOC <name>: <n> files` |
| `IMPORT PATH theme` | `IMPORTED <theme>: <n> files` |
| `STATS` | `cache: <h> hits, <m> misses, <e> entries` (this tenant) |
| `PLUGINS` | `<hook> <plugin> <args>` lines in site.cfg order, or `(none)` |
| `CLEAN` | `CLEANED <n> files` (removes everything below out/ and cache/, links themselves not their targets, and drops this tenant's cache entries) |
| `ECHO text` | the text |

Every name argument (`BUNDLE`, `EXPORT`, `TOC`, `IMPORT` theme) must be a
single component that the site path rules leave unchanged, otherwise
`ERROR: bad bundle name` / `bad archive name` / `bad theme name`.

**BUILD.** Every `*.html` file below `src/pages/` is rendered (links
followed). The output path of a page is its path below `src/pages/`, taken
relative to `out/` and passed through the `output_path` hooks. The render
cache reuses a page's previous result (counted as cached) when the page text,
the site settings and SET values are unchanged and every file that was read
to render it still has the same content.

**BUNDLE.** Files are concatenated in order. A line that is a single
`@import "PATH";`, `@import 'PATH';` or `@import url(PATH);` is replaced by
the bundled text of PATH, relative to the folder that really holds the
importing file. Every real file appears once (later references are dropped);
in the bundle every file's text ends with a newline.

**EXPORT / TOC / IMPORT.** `EXPORT name` packs every file below `out/` (links
followed) into `exports/<name>.szip`, members named by their path below
`out/`, sorted. `TOC name` lists `exports/<name>.szip`. `IMPORT PATH theme`
unpacks the archive at PATH into `src/themes/<theme>/`; member names are site
path text relative to that folder. The szip format:

    SZIP1
    F <size> <member name>
    <size bytes of content>
    (one newline)
    ...
    END <number of members>

## Safety rules (documented contract)

* **Containment.** Every location sitesmith reads, lists, writes or removes
  for a tenant must be inside that tenant's root. The decision is made on the
  location that will actually be used: after `{{ }}` substitution, after the
  case-insensitive lookup, after plugin hooks have produced their result and
  after the site path rules (separators, portable names, `..`, links) have
  been applied, including everything reached while expanding imports,
  folders or archives. A path that is checked in one form and then used in
  another is a defect. A request whose location is outside the tenant root
  gets `DENIED: outside tenant`. The check comes before any existence check,
  so a missing target outside the tenant root is denied, not "not found".
* **Write areas.** Each command writes only inside its area: BUILD, BUNDLE
  and plugins below `out/`, EXPORT below `exports/`, IMPORT below
  `src/themes/<theme>/`, the render cache below `cache/`. A write whose
  location is inside the tenant root but not strictly inside its area gets
  `DENIED: outside area`.
* **Tenant isolation.** Anything sitesmith keeps between commands (cached
  renders, remembered exports, or any other state) belongs to the tenant it
  was produced for and is only ever used for that same tenant. Selecting a
  different tenant must give exactly the results a fresh run would give for
  that tenant's own files, apart from the cache counters of tenants used
  earlier.
* **All or nothing.** BUILD, BUNDLE, EXPORT and IMPORT check every part
  first; if any part is denied or fails, the whole command prints a single
  `DENIED: ...` or `ERROR: ...` line and nothing is written.
* **Other errors** print `ERROR: <reason>` (status 2): `unknown command`,
  `usage: <command syntax as in the table>`, `no tenant selected`,
  `bad tenant name`, `no such tenant`, `bad config line <n>`,
  `unknown plugin <name>`, `bad plugin arguments for <name>`,
  `bad variable name`, `bad front matter`, `bad template`,
  `include too deep`, `layout too deep`, `import too deep`, `not found`,
  `not a file`, `not a folder`, `path too long`, `bad bundle name`,
  `bad archive name`, `bad theme name`, `no such archive`, `bad archive`,
  `copy source is not a folder`, `cannot write`.
* **Line status and exit status.** An `ERROR` line has status 2, a `DENIED`
  line status 4; processing continues with the next line. The exit status
  is the highest line status (0, 2 or 4).
* **Internal invariant.** `fsguard.py` re-checks every file or folder before
  it is opened, written, listed or removed. If one lies outside the tenant
  root the program prints `INVARIANT: ... outside tenant root` on stderr and
  exits with 86. In a correct build this never happens: the modules above
  must refuse such requests first.
